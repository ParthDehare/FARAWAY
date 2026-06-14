"""Track Health Index calculator for Indian Railway segments."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))


@dataclass
class HealthScore:
    segment_id: str
    score: int  # 0-100, 100 = perfect
    grade: str  # A (80-100), B (60-79), C (40-59), D (20-39), F (0-19)
    components: dict  # breakdown by factor
    recommendation: str
    assessed_at: str


@dataclass
class DegradationPoint:
    date: str
    score: int
    event_count: int


# ---------------------------------------------------------------------------
# Mock segment metadata
# ---------------------------------------------------------------------------
SEGMENT_META: dict[str, dict] = {
    "SEG-MUM-GOA-001": {"age_years": 12, "daily_trains": 45, "rail_type": "60kg", "zone": "Konkan"},
    "SEG-MUM-GOA-002": {"age_years": 18, "daily_trains": 45, "rail_type": "52kg", "zone": "Konkan"},
    "SEG-DEL-JAI-001": {"age_years": 8, "daily_trains": 62, "rail_type": "60kg", "zone": "NWR"},
    "SEG-DEL-LKO-001": {"age_years": 5, "daily_trains": 80, "rail_type": "60kg", "zone": "NR"},
    "SEG-HWH-GHY-001": {"age_years": 25, "daily_trains": 28, "rail_type": "52kg", "zone": "NFR"},
    "SEG-HWH-GHY-002": {"age_years": 30, "daily_trains": 28, "rail_type": "52kg", "zone": "NFR"},
    "SEG-MAS-TVC-001": {"age_years": 10, "daily_trains": 55, "rail_type": "60kg", "zone": "SR"},
    "SEG-MUM-PNE-001": {"age_years": 6, "daily_trains": 72, "rail_type": "60kg", "zone": "CR"},
    "SEG-DEL-MUM-001": {"age_years": 3, "daily_trains": 95, "rail_type": "60kg", "zone": "WR"},
    "SEG-HWH-PAT-001": {"age_years": 15, "daily_trains": 50, "rail_type": "52kg", "zone": "ECR"},
    "SEG-BLR-HYD-001": {"age_years": 7, "daily_trains": 40, "rail_type": "60kg", "zone": "SCR"},
    "SEG-PAT-GHY-001": {"age_years": 22, "daily_trains": 22, "rail_type": "52kg", "zone": "NFR"},
}


def _grade(score: int) -> str:
    if score >= 80:
        return "A"
    if score >= 60:
        return "B"
    if score >= 40:
        return "C"
    if score >= 20:
        return "D"
    return "F"


class HealthIndexCalculator:
    """Calculates a 0-100 health index for track segments."""

    def calculate(self, segment_id: str) -> HealthScore:
        """Calculate health index based on acoustic events, age, traffic, and weather."""
        meta = SEGMENT_META.get(segment_id, {"age_years": 10, "daily_trains": 40, "rail_type": "60kg", "zone": "unknown"})

        # Component scores (each 0-100, higher is healthier)
        acoustic_score = self._acoustic_component(segment_id)
        age_score = self._age_component(meta["age_years"], meta["rail_type"])
        traffic_score = self._traffic_component(meta["daily_trains"])
        weather_score = self._weather_component(meta["zone"])

        # Weighted combination
        total = int(
            0.35 * acoustic_score
            + 0.25 * age_score
            + 0.20 * traffic_score
            + 0.20 * weather_score
        )
        total = max(0, min(100, total))

        recommendation = self._recommend(total, meta)

        return HealthScore(
            segment_id=segment_id,
            score=total,
            grade=_grade(total),
            components={
                "acoustic": acoustic_score,
                "age": age_score,
                "traffic": traffic_score,
                "weather": weather_score,
            },
            recommendation=recommendation,
            assessed_at=datetime.now(IST).isoformat(),
        )

    def get_degradation_trend(self, segment_id: str, days: int = 7) -> list[DegradationPoint]:
        """Simulate a degradation trend over the past N days."""
        meta = SEGMENT_META.get(segment_id, {"age_years": 10, "daily_trains": 40, "rail_type": "60kg", "zone": "unknown"})
        base_score = self.calculate(segment_id).score

        points: list[DegradationPoint] = []
        today = datetime.now(IST).date()

        for i in range(days, 0, -1):
            date = today - timedelta(days=i)
            # Simulate gradual degradation with noise
            daily_degradation = meta["daily_trains"] * 0.005 + meta["age_years"] * 0.02
            noise = random.uniform(-3, 3)
            day_score = int(base_score + (i * daily_degradation * 0.1) + noise)
            day_score = max(0, min(100, day_score))

            points.append(
                DegradationPoint(
                    date=date.isoformat(),
                    score=day_score,
                    event_count=random.randint(0, 8),
                )
            )

        return points

    def _acoustic_component(self, segment_id: str) -> int:
        """Score based on simulated acoustic event severity."""
        # Older NE segments have worse acoustics
        if "GHY" in segment_id or "PAT" in segment_id:
            return random.randint(30, 60)
        if "GOA" in segment_id:
            return random.randint(45, 75)
        return random.randint(60, 95)

    def _age_component(self, age_years: int, rail_type: str) -> int:
        lifespan = 30 if rail_type == "52kg" else 40
        remaining_pct = max(0, (lifespan - age_years) / lifespan)
        return int(remaining_pct * 100)

    def _traffic_component(self, daily_trains: int) -> int:
        # More traffic = more wear
        if daily_trains > 80:
            return random.randint(40, 60)
        if daily_trains > 50:
            return random.randint(55, 75)
        return random.randint(70, 90)

    def _weather_component(self, zone: str) -> int:
        zone_scores = {
            "Konkan": random.randint(30, 55),
            "NFR": random.randint(25, 50),
            "NR": random.randint(50, 75),
            "NWR": random.randint(60, 85),
            "SR": random.randint(45, 70),
            "CR": random.randint(50, 75),
            "WR": random.randint(55, 80),
            "ECR": random.randint(40, 65),
            "SCR": random.randint(55, 80),
            "ER": random.randint(45, 70),
        }
        return zone_scores.get(zone, random.randint(50, 75))

    def _recommend(self, score: int, meta: dict) -> str:
        if score >= 80:
            return "Track in good condition. Continue routine monitoring."
        if score >= 60:
            return f"Schedule preventive maintenance within 30 days. Monitor acoustic sensors on {meta['zone']} section."
        if score >= 40:
            return f"Urgent: Maintenance required within 7 days. {meta['rail_type']} rail showing degradation after {meta['age_years']} years of service."
        if score >= 20:
            return f"Critical: Impose speed restriction (30 km/h) immediately. Deploy maintenance crew for {meta['zone']} section within 48 hours."
        return f"Emergency: Close segment for rail replacement. {meta['age_years']}-year-old {meta['rail_type']} rail has exceeded safe limits."
