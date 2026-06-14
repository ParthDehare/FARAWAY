"""OpenWeatherMap API client for Indian Railway weather monitoring."""

import os
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx

IST = timezone(timedelta(hours=5, minutes=30))

OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5"

# ---------------------------------------------------------------------------
# Mock weather profiles keyed by approximate (lat, lon) regions
# ---------------------------------------------------------------------------
MOCK_PROFILES: dict[str, dict] = {
    "mumbai": {
        "lat_range": (18.5, 19.5),
        "lon_range": (72.5, 73.5),
        "conditions": ["heavy rain", "thunderstorm", "overcast"],
        "temp_range": (24, 34),
        "humidity_range": (75, 98),
        "wind_range": (10, 45),
        "description": "Monsoon rain along Konkan coast",
    },
    "delhi": {
        "lat_range": (28.0, 29.0),
        "lon_range": (76.5, 77.5),
        "conditions": ["fog", "haze", "smog", "clear"],
        "temp_range": (5, 46),
        "humidity_range": (30, 90),
        "wind_range": (5, 20),
        "description": "Winter fog / summer heat in NCR",
    },
    "rajasthan": {
        "lat_range": (24.0, 28.0),
        "lon_range": (69.0, 76.0),
        "conditions": ["extreme heat", "dust storm", "clear"],
        "temp_range": (20, 50),
        "humidity_range": (10, 40),
        "wind_range": (8, 60),
        "description": "Desert heat and dust storms",
    },
    "chennai": {
        "lat_range": (12.5, 13.5),
        "lon_range": (79.5, 80.5),
        "conditions": ["cyclone warning", "heavy rain", "humid"],
        "temp_range": (26, 40),
        "humidity_range": (60, 95),
        "wind_range": (10, 70),
        "description": "Coastal cyclone-prone zone",
    },
    "kolkata": {
        "lat_range": (22.0, 23.0),
        "lon_range": (88.0, 89.0),
        "conditions": ["heavy rain", "humid", "thunderstorm"],
        "temp_range": (18, 38),
        "humidity_range": (65, 95),
        "wind_range": (8, 35),
        "description": "Eastern monsoon belt",
    },
    "guwahati": {
        "lat_range": (26.0, 26.5),
        "lon_range": (91.5, 92.0),
        "conditions": ["heavy rain", "flood warning", "overcast"],
        "temp_range": (12, 35),
        "humidity_range": (70, 98),
        "wind_range": (5, 30),
        "description": "NE India heavy rainfall zone",
    },
    "default": {
        "lat_range": (8.0, 35.0),
        "lon_range": (68.0, 97.0),
        "conditions": ["partly cloudy", "clear", "light rain"],
        "temp_range": (20, 38),
        "humidity_range": (40, 75),
        "wind_range": (5, 20),
        "description": "General Indian conditions",
    },
}


@dataclass
class WeatherData:
    lat: float
    lon: float
    temperature_c: float
    humidity: int
    wind_speed_kmh: float
    condition: str
    description: str
    visibility_km: float
    timestamp: str
    source: str  # "api" or "mock"


@dataclass
class ForecastPoint:
    timestamp: str
    temperature_c: float
    condition: str
    wind_speed_kmh: float
    precipitation_mm: float


def _match_profile(lat: float, lon: float) -> dict:
    for name, p in MOCK_PROFILES.items():
        if name == "default":
            continue
        if p["lat_range"][0] <= lat <= p["lat_range"][1] and p["lon_range"][0] <= lon <= p["lon_range"][1]:
            return p
    return MOCK_PROFILES["default"]


def _mock_weather(lat: float, lon: float) -> WeatherData:
    profile = _match_profile(lat, lon)
    temp = round(random.uniform(*profile["temp_range"]), 1)
    return WeatherData(
        lat=lat,
        lon=lon,
        temperature_c=temp,
        humidity=random.randint(*profile["humidity_range"]),
        wind_speed_kmh=round(random.uniform(*profile["wind_range"]), 1),
        condition=random.choice(profile["conditions"]),
        description=profile["description"],
        visibility_km=round(random.uniform(0.5, 10.0), 1),
        timestamp=datetime.now(IST).isoformat(),
        source="mock",
    )


def _mock_forecast(lat: float, lon: float, hours: int) -> list[ForecastPoint]:
    profile = _match_profile(lat, lon)
    points: list[ForecastPoint] = []
    now = datetime.now(IST)
    for h in range(1, hours + 1):
        points.append(
            ForecastPoint(
                timestamp=(now + timedelta(hours=h)).isoformat(),
                temperature_c=round(random.uniform(*profile["temp_range"]), 1),
                condition=random.choice(profile["conditions"]),
                wind_speed_kmh=round(random.uniform(*profile["wind_range"]), 1),
                precipitation_mm=round(random.uniform(0, 30), 1) if "rain" in " ".join(profile["conditions"]) else 0.0,
            )
        )
    return points


class OpenWeatherClient:
    """Async client for OpenWeatherMap with mock fallback."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or OPENWEATHERMAP_API_KEY
        self._use_mock = not self.api_key

    async def get_weather(self, lat: float, lon: float) -> WeatherData:
        """Get current weather for a coordinate."""
        if self._use_mock:
            return _mock_weather(lat, lon)

        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.get(
                    f"{BASE_URL}/weather",
                    params={"lat": lat, "lon": lon, "appid": self.api_key, "units": "metric"},
                )
                resp.raise_for_status()
                d = resp.json()
                return WeatherData(
                    lat=lat,
                    lon=lon,
                    temperature_c=d["main"]["temp"],
                    humidity=d["main"]["humidity"],
                    wind_speed_kmh=round(d["wind"]["speed"] * 3.6, 1),
                    condition=d["weather"][0]["main"],
                    description=d["weather"][0]["description"],
                    visibility_km=round(d.get("visibility", 10000) / 1000, 1),
                    timestamp=datetime.now(IST).isoformat(),
                    source="api",
                )
            except (httpx.HTTPError, KeyError):
                return _mock_weather(lat, lon)

    async def get_forecast(self, lat: float, lon: float, hours: int = 6) -> list[ForecastPoint]:
        """Get hourly forecast for a coordinate."""
        if self._use_mock:
            return _mock_forecast(lat, lon, hours)

        async with httpx.AsyncClient(timeout=10) as client:
            try:
                resp = await client.get(
                    f"{BASE_URL}/forecast",
                    params={"lat": lat, "lon": lon, "appid": self.api_key, "units": "metric", "cnt": hours},
                )
                resp.raise_for_status()
                d = resp.json()
                points: list[ForecastPoint] = []
                for item in d.get("list", [])[:hours]:
                    points.append(
                        ForecastPoint(
                            timestamp=item["dt_txt"],
                            temperature_c=item["main"]["temp"],
                            condition=item["weather"][0]["main"],
                            wind_speed_kmh=round(item["wind"]["speed"] * 3.6, 1),
                            precipitation_mm=item.get("rain", {}).get("3h", 0.0),
                        )
                    )
                return points
            except (httpx.HTTPError, KeyError):
                return _mock_forecast(lat, lon, hours)

    async def get_route_weather(self, route_coords: list[tuple]) -> list[WeatherData]:
        """Get weather at each coordinate along a route."""
        results: list[WeatherData] = []
        for lat, lon in route_coords:
            results.append(await self.get_weather(lat, lon))
        return results
