"""ISRO satellite data client (mock) for flood and landslide risk assessment."""

import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))


@dataclass
class FloodRisk:
    lat: float
    lon: float
    radius_km: float
    risk_level: str  # low / medium / high / extreme
    risk_score: float  # 0.0 - 1.0
    water_level_trend: str  # rising / stable / falling
    nearby_rivers: list[str]
    satellite_pass: str  # last satellite observation timestamp
    notes: str


@dataclass
class LandslideRisk:
    lat: float
    lon: float
    risk_level: str
    risk_score: float
    soil_saturation_pct: float
    slope_grade: str  # gentle / moderate / steep / very_steep
    recent_rainfall_mm: float
    notes: str


# ---------------------------------------------------------------------------
# Regional risk profiles
# ---------------------------------------------------------------------------
FLOOD_ZONES: list[dict] = [
    {
        "name": "Konkan Coast",
        "lat_range": (15.0, 20.0),
        "lon_range": (72.0, 74.0),
        "base_risk": 0.7,
        "rivers": ["Ulhas", "Vashishti", "Savitri"],
        "notes": "Monsoon-prone coastal belt; frequent waterlogging on Mumbai-Goa route",
    },
    {
        "name": "Brahmaputra Basin",
        "lat_range": (25.5, 27.5),
        "lon_range": (89.0, 96.0),
        "base_risk": 0.85,
        "rivers": ["Brahmaputra", "Manas", "Subansiri"],
        "notes": "Annual flooding Jun-Sep; NF Railway severely affected",
    },
    {
        "name": "Gangetic Plains",
        "lat_range": (24.0, 27.0),
        "lon_range": (80.0, 88.0),
        "base_risk": 0.55,
        "rivers": ["Ganga", "Kosi", "Gandak", "Son"],
        "notes": "Bihar-UP flood belt; Kosi river embankment breaches",
    },
    {
        "name": "Kerala Backwaters",
        "lat_range": (8.5, 12.5),
        "lon_range": (75.5, 77.5),
        "base_risk": 0.6,
        "rivers": ["Periyar", "Pamba", "Bharathapuzha"],
        "notes": "Western Ghats runoff; 2018/2024 scale floods possible",
    },
]

LANDSLIDE_ZONES: list[dict] = [
    {
        "name": "Western Ghats",
        "lat_range": (10.0, 20.0),
        "lon_range": (73.0, 76.0),
        "base_risk": 0.65,
        "slope": "steep",
        "notes": "Konkan Railway ghat sections; laterite soil prone to slippage",
    },
    {
        "name": "NE Hill Sections",
        "lat_range": (25.0, 28.0),
        "lon_range": (91.0, 97.0),
        "base_risk": 0.75,
        "slope": "very_steep",
        "notes": "Lumding-Badarpur hill section; frequent debris falls",
    },
    {
        "name": "Himalayan Foothills",
        "lat_range": (29.0, 34.0),
        "lon_range": (74.0, 80.0),
        "base_risk": 0.6,
        "slope": "steep",
        "notes": "Kalka-Shimla, Jammu-Udhampur routes; seismic zone IV/V",
    },
    {
        "name": "Nilgiri Hills",
        "lat_range": (11.0, 12.0),
        "lon_range": (76.0, 77.5),
        "base_risk": 0.5,
        "slope": "moderate",
        "notes": "Nilgiri Mountain Railway section; heritage track",
    },
]


def _jitter(base: float, spread: float = 0.15) -> float:
    return max(0.0, min(1.0, base + random.uniform(-spread, spread)))


class SatelliteClient:
    """Mock ISRO satellite data client for risk assessments."""

    async def get_flood_risk(self, lat: float, lon: float, radius_km: float = 50) -> FloodRisk:
        """Assess flood risk at a location using simulated satellite imagery."""
        matched_zone = None
        for zone in FLOOD_ZONES:
            if zone["lat_range"][0] <= lat <= zone["lat_range"][1] and zone["lon_range"][0] <= lon <= zone["lon_range"][1]:
                matched_zone = zone
                break

        if matched_zone:
            score = _jitter(matched_zone["base_risk"])
            rivers = matched_zone["rivers"]
            notes = matched_zone["notes"]
        else:
            score = _jitter(0.15)
            rivers = []
            notes = "No major flood zone detected for this location"

        risk_level = (
            "extreme" if score >= 0.8
            else "high" if score >= 0.6
            else "medium" if score >= 0.35
            else "low"
        )

        return FloodRisk(
            lat=lat,
            lon=lon,
            radius_km=radius_km,
            risk_level=risk_level,
            risk_score=round(score, 3),
            water_level_trend=random.choice(["rising", "stable", "falling"]),
            nearby_rivers=rivers,
            satellite_pass=datetime.now(IST).isoformat(),
            notes=notes,
        )

    async def get_landslide_risk(self, lat: float, lon: float) -> LandslideRisk:
        """Assess landslide risk for mountain/hill sections."""
        matched_zone = None
        for zone in LANDSLIDE_ZONES:
            if zone["lat_range"][0] <= lat <= zone["lat_range"][1] and zone["lon_range"][0] <= lon <= zone["lon_range"][1]:
                matched_zone = zone
                break

        if matched_zone:
            score = _jitter(matched_zone["base_risk"])
            slope = matched_zone["slope"]
            notes = matched_zone["notes"]
            rainfall = round(random.uniform(50, 300), 1)
        else:
            score = _jitter(0.1)
            slope = "gentle"
            notes = "Flat terrain; landslide risk negligible"
            rainfall = round(random.uniform(0, 30), 1)

        risk_level = (
            "extreme" if score >= 0.8
            else "high" if score >= 0.6
            else "medium" if score >= 0.35
            else "low"
        )

        return LandslideRisk(
            lat=lat,
            lon=lon,
            risk_level=risk_level,
            risk_score=round(score, 3),
            soil_saturation_pct=round(random.uniform(40, 95) if score > 0.4 else random.uniform(10, 40), 1),
            slope_grade=slope,
            recent_rainfall_mm=rainfall,
            notes=notes,
        )
