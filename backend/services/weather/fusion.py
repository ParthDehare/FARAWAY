"""Weather fusion service combining OpenWeather and ISRO satellite data."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from .openweather import OpenWeatherClient
from .satellite import SatelliteClient

IST = timezone(timedelta(hours=5, minutes=30))

# ---------------------------------------------------------------------------
# Segment coordinate lookup (mock — maps segment IDs to midpoint coords)
# ---------------------------------------------------------------------------
SEGMENT_COORDS: dict[str, tuple[float, float]] = {
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
class RouteRiskAssessment:
    segment_id: str
    risk_level: str  # low / medium / high / extreme
    overall_score: float  # 0.0 - 1.0
    conditions: dict
    forecast_text: str
    affected_segments: list[str]
    assessed_at: str


class WeatherFusion:
    """Combines OpenWeather API data and satellite imagery for route risk."""

    def __init__(self):
        self.weather_client = OpenWeatherClient()
        self.satellite_client = SatelliteClient()

    async def assess_route_risk(self, segment_id: str) -> RouteRiskAssessment:
        """Produce a combined risk assessment for a rail segment."""
        coords = SEGMENT_COORDS.get(segment_id)
        if coords is None:
            return RouteRiskAssessment(
                segment_id=segment_id,
                risk_level="low",
                overall_score=0.1,
                conditions={"note": "Segment not in lookup; defaulting to low risk"},
                forecast_text="No data available for this segment.",
                affected_segments=[segment_id],
                assessed_at=datetime.now(IST).isoformat(),
            )

        lat, lon = coords

        # Gather data concurrently (both are async)
        weather = await self.weather_client.get_weather(lat, lon)
        forecast = await self.weather_client.get_forecast(lat, lon, hours=6)
        flood = await self.satellite_client.get_flood_risk(lat, lon)
        landslide = await self.satellite_client.get_landslide_risk(lat, lon)

        # Weighted score: weather condition 30%, flood 40%, landslide 30%
        weather_score = self._weather_severity(weather.condition)
        combined = 0.30 * weather_score + 0.40 * flood.risk_score + 0.30 * landslide.risk_score
        combined = round(min(1.0, combined), 3)

        risk_level = (
            "extreme" if combined >= 0.8
            else "high" if combined >= 0.6
            else "medium" if combined >= 0.35
            else "low"
        )

        # Build human-readable forecast summary
        upcoming = [f.condition for f in forecast[:3]]
        forecast_text = (
            f"Current: {weather.condition} ({weather.temperature_c}C, "
            f"humidity {weather.humidity}%, wind {weather.wind_speed_kmh} km/h). "
            f"Next 3h: {', '.join(upcoming)}. "
            f"Flood risk: {flood.risk_level} ({flood.notes}). "
            f"Landslide risk: {landslide.risk_level}."
        )

        # Find neighbouring affected segments
        affected = [segment_id]
        for sid, (slat, slon) in SEGMENT_COORDS.items():
            if sid == segment_id:
                continue
            if abs(slat - lat) < 2.0 and abs(slon - lon) < 2.0:
                affected.append(sid)

        return RouteRiskAssessment(
            segment_id=segment_id,
            risk_level=risk_level,
            overall_score=combined,
            conditions={
                "temperature_c": weather.temperature_c,
                "humidity": weather.humidity,
                "wind_speed_kmh": weather.wind_speed_kmh,
                "weather_condition": weather.condition,
                "flood_risk": flood.risk_level,
                "flood_score": flood.risk_score,
                "landslide_risk": landslide.risk_level,
                "landslide_score": landslide.risk_score,
            },
            forecast_text=forecast_text,
            affected_segments=affected,
            assessed_at=datetime.now(IST).isoformat(),
        )

    @staticmethod
    def _weather_severity(condition: str) -> float:
        """Map a weather condition string to a 0-1 severity score."""
        condition_lower = condition.lower()
        if any(w in condition_lower for w in ["cyclone", "extreme", "dust storm"]):
            return 0.95
        if any(w in condition_lower for w in ["heavy rain", "thunderstorm", "flood"]):
            return 0.8
        if any(w in condition_lower for w in ["fog", "smog", "haze"]):
            return 0.5
        if any(w in condition_lower for w in ["rain", "overcast", "humid"]):
            return 0.35
        if any(w in condition_lower for w in ["partly cloudy", "light rain"]):
            return 0.2
        return 0.1
