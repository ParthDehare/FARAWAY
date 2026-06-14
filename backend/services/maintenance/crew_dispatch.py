"""Maintenance crew dispatch service for Indian Railways."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import uuid4

IST = timezone(timedelta(hours=5, minutes=30))

# ---------------------------------------------------------------------------
# Segment location lookup (lat, lon)
# ---------------------------------------------------------------------------
SEGMENT_LOCATIONS: dict[str, tuple[float, float]] = {
    "SEG-MUM-GOA-001": (17.0, 73.3),
    "SEG-MUM-GOA-002": (16.0, 73.5),
    "SEG-DEL-JAI-001": (27.5, 76.5),
    "SEG-DEL-LKO-001": (27.8, 79.0),
    "SEG-HWH-GHY-001": (26.0, 91.7),
    "SEG-HWH-GHY-002": (25.5, 90.5),
    "SEG-MAS-TVC-001": (10.0, 76.5),
    "SEG-MUM-PNE-001": (18.8, 73.5),
    "SEG-DEL-MUM-001": (24.0, 73.0),
    "SEG-HWH-PAT-001": (25.0, 85.5),
    "SEG-BLR-HYD-001": (15.5, 78.0),
    "SEG-PAT-GHY-001": (26.2, 89.5),
}


@dataclass
class Crew:
    crew_id: str
    name: str
    base_station: str
    lat: float
    lon: float
    skills: list[str]
    available: bool
    current_assignment: str | None = None


@dataclass
class DispatchOrder:
    order_id: str
    crew_id: str
    crew_name: str
    segment_id: str
    priority: str
    distance_km: float
    eta_hours: float
    status: str  # dispatched / en_route / on_site / completed
    dispatched_at: str


# ---------------------------------------------------------------------------
# Mock crew database
# ---------------------------------------------------------------------------
CREWS: list[dict] = [
    {"crew_id": "CRW-001", "name": "Mumbai Rail Works Alpha", "base": "Mumbai", "lat": 19.0, "lon": 72.85, "skills": ["welding", "rail_replacement", "ballast"]},
    {"crew_id": "CRW-002", "name": "Mumbai Rail Works Beta", "base": "Mumbai", "lat": 19.1, "lon": 72.90, "skills": ["welding", "electrical"]},
    {"crew_id": "CRW-003", "name": "Pune Track Team", "base": "Pune", "lat": 18.53, "lon": 73.87, "skills": ["rail_replacement", "ballast", "welding"]},
    {"crew_id": "CRW-004", "name": "Delhi North Maintenance", "base": "Delhi", "lat": 28.7, "lon": 77.2, "skills": ["welding", "electrical", "rail_replacement"]},
    {"crew_id": "CRW-005", "name": "Jaipur Track Gang", "base": "Jaipur", "lat": 26.92, "lon": 75.79, "skills": ["ballast", "welding"]},
    {"crew_id": "CRW-006", "name": "Lucknow P-Way Unit", "base": "Lucknow", "lat": 26.85, "lon": 80.95, "skills": ["rail_replacement", "ballast", "electrical"]},
    {"crew_id": "CRW-007", "name": "Howrah Emergency Team", "base": "Kolkata", "lat": 22.58, "lon": 88.34, "skills": ["welding", "rail_replacement", "electrical"]},
    {"crew_id": "CRW-008", "name": "Guwahati Hill Section Unit", "base": "Guwahati", "lat": 26.17, "lon": 91.75, "skills": ["rail_replacement", "ballast"]},
    {"crew_id": "CRW-009", "name": "Chennai Southern Works", "base": "Chennai", "lat": 13.08, "lon": 80.27, "skills": ["welding", "electrical", "ballast"]},
    {"crew_id": "CRW-010", "name": "Bangalore Track Renewal", "base": "Bangalore", "lat": 12.98, "lon": 77.57, "skills": ["rail_replacement", "ballast", "welding", "electrical"]},
]


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class CrewDispatcher:
    """Manages maintenance crew assignments and dispatch."""

    def __init__(self):
        self.crews: list[Crew] = [
            Crew(
                crew_id=c["crew_id"],
                name=c["name"],
                base_station=c["base"],
                lat=c["lat"],
                lon=c["lon"],
                skills=c["skills"],
                available=random.random() > 0.2,  # 80% chance available
            )
            for c in CREWS
        ]
        self.dispatch_log: list[DispatchOrder] = []

    def find_nearest_crew(
        self,
        segment_id: str,
        required_skills: list[str] | None = None,
    ) -> list[dict]:
        """Find crews ranked by proximity that have the required skills.

        Returns list of dicts with crew info and distance.
        """
        seg_loc = SEGMENT_LOCATIONS.get(segment_id)
        if seg_loc is None:
            return []

        slat, slon = seg_loc
        candidates: list[dict] = []

        for crew in self.crews:
            if not crew.available:
                continue
            if required_skills:
                if not all(skill in crew.skills for skill in required_skills):
                    continue
            dist = _haversine_km(slat, slon, crew.lat, crew.lon)
            candidates.append({
                "crew_id": crew.crew_id,
                "name": crew.name,
                "base_station": crew.base_station,
                "skills": crew.skills,
                "distance_km": round(dist, 1),
                "eta_hours": round(dist / 60, 1),  # ~60 km/h average road travel
            })

        candidates.sort(key=lambda c: c["distance_km"])
        return candidates

    def dispatch_crew(self, crew_id: str, segment_id: str, priority: str = "P1") -> DispatchOrder | None:
        """Create a dispatch order for a crew to a segment.

        Priority: P0 (emergency), P1 (urgent), P2 (scheduled).
        """
        crew = next((c for c in self.crews if c.crew_id == crew_id), None)
        if crew is None or not crew.available:
            return None

        seg_loc = SEGMENT_LOCATIONS.get(segment_id)
        if seg_loc is None:
            return None

        dist = _haversine_km(seg_loc[0], seg_loc[1], crew.lat, crew.lon)
        eta = dist / 60

        # P0 gets priority transport (helicopter/special train)
        if priority == "P0":
            eta = eta * 0.4

        order = DispatchOrder(
            order_id=f"DSP-{uuid4().hex[:8].upper()}",
            crew_id=crew_id,
            crew_name=crew.name,
            segment_id=segment_id,
            priority=priority,
            distance_km=round(dist, 1),
            eta_hours=round(eta, 1),
            status="dispatched",
            dispatched_at=datetime.now(IST).isoformat(),
        )

        crew.available = False
        crew.current_assignment = segment_id
        self.dispatch_log.append(order)

        return order

    def get_crew_status(self) -> list[dict]:
        """Return status of all crews."""
        return [
            {
                "crew_id": c.crew_id,
                "name": c.name,
                "base": c.base_station,
                "available": c.available,
                "assignment": c.current_assignment,
                "skills": c.skills,
            }
            for c in self.crews
        ]
