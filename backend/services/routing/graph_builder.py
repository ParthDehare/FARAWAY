"""Indian Railway network graph builder."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field


@dataclass
class Station:
    code: str
    name: str
    lat: float
    lon: float
    zone: str  # Railway zone


@dataclass
class Edge:
    from_station: str
    to_station: str
    distance_km: float
    travel_time_hours: float
    track_health: float = 1.0  # 0-1, 1 = perfect
    weather_risk: float = 0.0  # 0-1, 0 = no risk
    blocked: bool = False

    @property
    def weight(self) -> float:
        """Composite weight: lower is better."""
        if self.blocked:
            return float("inf")
        base = self.distance_km / 100  # normalised distance
        health_penalty = (1.0 - self.track_health) * 3.0
        weather_penalty = self.weather_risk * 4.0
        return base + health_penalty + weather_penalty


# ---------------------------------------------------------------------------
# Network data — major Indian Railway stations and routes
# ---------------------------------------------------------------------------
STATIONS: list[dict] = [
    {"code": "NDLS", "name": "New Delhi", "lat": 28.6442, "lon": 77.2194, "zone": "NR"},
    {"code": "BCT", "name": "Mumbai Central", "lat": 18.9712, "lon": 72.8196, "zone": "WR"},
    {"code": "MAS", "name": "Chennai Central", "lat": 13.0827, "lon": 80.2707, "zone": "SR"},
    {"code": "HWH", "name": "Howrah (Kolkata)", "lat": 22.5839, "lon": 88.3428, "zone": "ER"},
    {"code": "SBC", "name": "Bangalore City", "lat": 12.9784, "lon": 77.5716, "zone": "SWR"},
    {"code": "HYB", "name": "Hyderabad", "lat": 17.3850, "lon": 78.4867, "zone": "SCR"},
    {"code": "JP", "name": "Jaipur", "lat": 26.9196, "lon": 75.7878, "zone": "NWR"},
    {"code": "ADI", "name": "Ahmedabad", "lat": 23.0225, "lon": 72.5714, "zone": "WR"},
    {"code": "LKO", "name": "Lucknow", "lat": 26.8467, "lon": 80.9462, "zone": "NR"},
    {"code": "PNBE", "name": "Patna", "lat": 25.6093, "lon": 85.1376, "zone": "ECR"},
    {"code": "GHY", "name": "Guwahati", "lat": 26.1722, "lon": 91.7530, "zone": "NFR"},
    {"code": "TVC", "name": "Trivandrum", "lat": 8.4875, "lon": 76.9525, "zone": "SR"},
    {"code": "PNE", "name": "Pune", "lat": 18.5285, "lon": 73.8743, "zone": "CR"},
    {"code": "MAO", "name": "Goa (Madgaon)", "lat": 15.2993, "lon": 74.1240, "zone": "KR"},
]

ROUTES: list[dict] = [
    {"from": "NDLS", "to": "JP", "km": 308, "hours": 4.5},
    {"from": "NDLS", "to": "LKO", "km": 511, "hours": 6.5},
    {"from": "NDLS", "to": "BCT", "km": 1384, "hours": 16.0},
    {"from": "NDLS", "to": "HWH", "km": 1530, "hours": 17.0},
    {"from": "NDLS", "to": "ADI", "km": 935, "hours": 12.0},
    {"from": "JP", "to": "ADI", "km": 625, "hours": 8.0},
    {"from": "BCT", "to": "PNE", "km": 192, "hours": 3.0},
    {"from": "BCT", "to": "ADI", "km": 493, "hours": 6.5},
    {"from": "BCT", "to": "MAO", "km": 588, "hours": 8.5},
    {"from": "PNE", "to": "SBC", "km": 840, "hours": 12.0},
    {"from": "PNE", "to": "HYB", "km": 560, "hours": 8.0},
    {"from": "MAS", "to": "SBC", "km": 362, "hours": 5.0},
    {"from": "MAS", "to": "HYB", "km": 625, "hours": 8.0},
    {"from": "MAS", "to": "TVC", "km": 773, "hours": 10.5},
    {"from": "SBC", "to": "HYB", "km": 570, "hours": 8.0},
    {"from": "SBC", "to": "TVC", "km": 510, "hours": 10.0},
    {"from": "SBC", "to": "MAO", "km": 560, "hours": 10.0},
    {"from": "HWH", "to": "PNBE", "km": 538, "hours": 7.0},
    {"from": "HWH", "to": "MAS", "km": 1663, "hours": 20.0},
    {"from": "PNBE", "to": "LKO", "km": 530, "hours": 7.5},
    {"from": "PNBE", "to": "GHY", "km": 988, "hours": 15.0},
    {"from": "HWH", "to": "GHY", "km": 1087, "hours": 17.0},
    {"from": "HYB", "to": "MAO", "km": 650, "hours": 10.0},
    {"from": "LKO", "to": "PNBE", "km": 530, "hours": 7.5},
]


class RailwayGraph:
    """Graph representation of the Indian Railway network."""

    def __init__(self):
        self.stations: dict[str, Station] = {}
        self.adjacency: dict[str, list[Edge]] = {}
        self._build()

    def _build(self):
        for s in STATIONS:
            station = Station(**s)
            self.stations[station.code] = station
            self.adjacency[station.code] = []

        for r in ROUTES:
            # Bidirectional edges
            fwd = Edge(from_station=r["from"], to_station=r["to"], distance_km=r["km"], travel_time_hours=r["hours"])
            rev = Edge(from_station=r["to"], to_station=r["from"], distance_km=r["km"], travel_time_hours=r["hours"])
            self.adjacency[r["from"]].append(fwd)
            self.adjacency[r["to"]].append(rev)

    def get_edge(self, from_code: str, to_code: str) -> Edge | None:
        for edge in self.adjacency.get(from_code, []):
            if edge.to_station == to_code:
                return edge
        return None

    def block_segment(self, from_code: str, to_code: str):
        """Mark a segment as blocked in both directions."""
        for edge in self.adjacency.get(from_code, []):
            if edge.to_station == to_code:
                edge.blocked = True
        for edge in self.adjacency.get(to_code, []):
            if edge.to_station == from_code:
                edge.blocked = True

    def unblock_segment(self, from_code: str, to_code: str):
        for edge in self.adjacency.get(from_code, []):
            if edge.to_station == to_code:
                edge.blocked = False
        for edge in self.adjacency.get(to_code, []):
            if edge.to_station == from_code:
                edge.blocked = False

    def update_track_health(self, from_code: str, to_code: str, health: float):
        for edge in self.adjacency.get(from_code, []):
            if edge.to_station == to_code:
                edge.track_health = health
        for edge in self.adjacency.get(to_code, []):
            if edge.to_station == from_code:
                edge.track_health = health

    def update_weather_risk(self, from_code: str, to_code: str, risk: float):
        for edge in self.adjacency.get(from_code, []):
            if edge.to_station == to_code:
                edge.weather_risk = risk
        for edge in self.adjacency.get(to_code, []):
            if edge.to_station == from_code:
                edge.weather_risk = risk

    def dijkstra(self, start: str, end: str) -> tuple[list[str], float] | None:
        """Shortest path by composite weight. Returns (path, total_weight) or None."""
        dist: dict[str, float] = {code: float("inf") for code in self.stations}
        prev: dict[str, str | None] = {code: None for code in self.stations}
        dist[start] = 0.0
        pq = [(0.0, start)]

        while pq:
            d, u = heapq.heappop(pq)
            if u == end:
                break
            if d > dist[u]:
                continue
            for edge in self.adjacency[u]:
                w = edge.weight
                if w == float("inf"):
                    continue
                nd = d + w
                if nd < dist[edge.to_station]:
                    dist[edge.to_station] = nd
                    prev[edge.to_station] = u
                    heapq.heappush(pq, (nd, edge.to_station))

        if dist[end] == float("inf"):
            return None

        path: list[str] = []
        node: str | None = end
        while node is not None:
            path.append(node)
            node = prev[node]
        path.reverse()
        return path, dist[end]

    def k_shortest_paths(self, start: str, end: str, k: int = 3) -> list[tuple[list[str], float]]:
        """Yen's K-shortest paths algorithm."""
        first = self.dijkstra(start, end)
        if first is None:
            return []

        A: list[tuple[list[str], float]] = [first]
        B: list[tuple[list[str], float]] = []

        for i in range(1, k):
            if not A:
                break
            prev_path = A[i - 1][0]
            for j in range(len(prev_path) - 1):
                spur_node = prev_path[j]
                root_path = prev_path[: j + 1]

                # Temporarily remove edges used by existing paths
                removed_edges: list[tuple[str, str, Edge]] = []
                for path, _ in A:
                    if path[: j + 1] == root_path and j + 1 < len(path):
                        e = self.get_edge(path[j], path[j + 1])
                        if e and not e.blocked:
                            e.blocked = True
                            removed_edges.append((path[j], path[j + 1], e))

                spur = self.dijkstra(spur_node, end)
                # Restore
                for _, _, e in removed_edges:
                    e.blocked = False

                if spur:
                    total_path = root_path[:-1] + spur[0]
                    # Compute real weight
                    total_w = 0.0
                    for idx in range(len(total_path) - 1):
                        e = self.get_edge(total_path[idx], total_path[idx + 1])
                        total_w += e.weight if e else float("inf")
                    candidate = (total_path, total_w)
                    if candidate not in B and candidate not in A:
                        B.append(candidate)

            if not B:
                break
            B.sort(key=lambda x: x[1])
            A.append(B.pop(0))

        return A

    def route_distance(self, path: list[str]) -> float:
        total = 0.0
        for i in range(len(path) - 1):
            e = self.get_edge(path[i], path[i + 1])
            total += e.distance_km if e else 0
        return total

    def route_time(self, path: list[str]) -> float:
        total = 0.0
        for i in range(len(path) - 1):
            e = self.get_edge(path[i], path[i + 1])
            total += e.travel_time_hours if e else 0
        return total
