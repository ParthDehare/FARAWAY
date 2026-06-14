"""GNN-based rerouting model with Dijkstra fallback."""

from __future__ import annotations

from dataclasses import dataclass

from .graph_builder import RailwayGraph

# ---------------------------------------------------------------------------
# Try importing torch_geometric; fall back gracefully
# ---------------------------------------------------------------------------
_HAS_TORCH_GEOMETRIC = False
try:
    import torch
    import torch.nn.functional as F
    from torch_geometric.nn import GCNConv
    _HAS_TORCH_GEOMETRIC = True
except ImportError:
    pass


@dataclass
class AlternateRoute:
    path: list[str]  # station codes
    distance_km: float
    estimated_delay_hours: float
    weather_risk_score: float
    score: float  # lower is better


# ---------------------------------------------------------------------------
# Simple GCN model (only used when torch_geometric is available)
# ---------------------------------------------------------------------------
if _HAS_TORCH_GEOMETRIC:
    class _PathScoringGCN(torch.nn.Module):
        """2-layer GCN that scores nodes for path selection."""

        def __init__(self, num_features: int = 4, hidden: int = 16):
            super().__init__()
            self.conv1 = GCNConv(num_features, hidden)
            self.conv2 = GCNConv(hidden, 1)

        def forward(self, x, edge_index):
            h = F.relu(self.conv1(x, edge_index))
            h = self.conv2(h, edge_index)
            return h.squeeze(-1)


class GNNRouter:
    """Route finder using GNN scoring or Dijkstra fallback."""

    def __init__(self, graph: RailwayGraph | None = None):
        self.graph = graph or RailwayGraph()
        self._model = None
        if _HAS_TORCH_GEOMETRIC:
            self._model = _PathScoringGCN()

    def find_alternate_routes(
        self,
        blocked_from: str,
        blocked_to: str,
        num_routes: int = 3,
    ) -> list[AlternateRoute]:
        """Find alternate routes avoiding a blocked segment.

        Parameters
        ----------
        blocked_from : str
            Origin station code of the blocked segment.
        blocked_to : str
            Destination station code of the blocked segment.
        num_routes : int
            Number of alternate routes to return.
        """
        # Block the segment
        self.graph.block_segment(blocked_from, blocked_to)

        try:
            if self._model is not None:
                routes = self._gnn_routes(blocked_from, blocked_to, num_routes)
            else:
                routes = self._dijkstra_routes(blocked_from, blocked_to, num_routes)
        finally:
            # Always restore
            self.graph.unblock_segment(blocked_from, blocked_to)

        return routes

    def _dijkstra_routes(self, start: str, end: str, k: int) -> list[AlternateRoute]:
        raw = self.graph.k_shortest_paths(start, end, k=k)
        results: list[AlternateRoute] = []
        original = self.graph.dijkstra(start, end)
        original_time = original[1] if original else 0

        for path, weight in raw:
            dist = self.graph.route_distance(path)
            time_h = self.graph.route_time(path)
            delay = max(0.0, time_h - (original_time * 5))  # rough estimate
            weather_risk = self._path_weather_risk(path)
            results.append(
                AlternateRoute(
                    path=path,
                    distance_km=dist,
                    estimated_delay_hours=round(delay, 2),
                    weather_risk_score=round(weather_risk, 3),
                    score=round(weight, 3),
                )
            )

        results.sort(key=lambda r: r.score)
        return results[:k]

    def _gnn_routes(self, start: str, end: str, k: int) -> list[AlternateRoute]:
        """Use GCN to re-score Dijkstra candidates."""
        # Get candidate paths via Dijkstra first
        candidates = self._dijkstra_routes(start, end, k=k * 2)

        if not candidates or not _HAS_TORCH_GEOMETRIC:
            return candidates[:k]

        # Build tensors
        code_to_idx = {code: i for i, code in enumerate(self.graph.stations)}
        num_nodes = len(self.graph.stations)

        # Node features: [lat, lon, degree, is_junction]
        x = torch.zeros(num_nodes, 4)
        for code, station in self.graph.stations.items():
            idx = code_to_idx[code]
            x[idx] = torch.tensor([
                station.lat / 35.0,
                station.lon / 100.0,
                len(self.graph.adjacency[code]) / 10.0,
                1.0 if len(self.graph.adjacency[code]) >= 3 else 0.0,
            ])

        edge_src, edge_dst = [], []
        for code, edges in self.graph.adjacency.items():
            for e in edges:
                if not e.blocked:
                    edge_src.append(code_to_idx[code])
                    edge_dst.append(code_to_idx[e.to_station])
        edge_index = torch.tensor([edge_src, edge_dst], dtype=torch.long)

        with torch.no_grad():
            node_scores = self._model(x, edge_index)

        # Re-score candidates using GNN node scores
        for route in candidates:
            gnn_bonus = 0.0
            for station_code in route.path:
                idx = code_to_idx.get(station_code, 0)
                gnn_bonus += node_scores[idx].item()
            route.score = round(route.score - gnn_bonus * 0.1, 3)

        candidates.sort(key=lambda r: r.score)
        return candidates[:k]

    def _path_weather_risk(self, path: list[str]) -> float:
        """Average weather risk along a path."""
        if len(path) < 2:
            return 0.0
        total = 0.0
        count = 0
        for i in range(len(path) - 1):
            edge = self.graph.get_edge(path[i], path[i + 1])
            if edge:
                total += edge.weather_risk
                count += 1
        return total / count if count else 0.0
