from fastapi import APIRouter
import random

router = APIRouter(prefix="/weather", tags=["Weather"])

@router.get("/route/{route_id}")
async def get_weather_for_route(route_id: str):
    """Dynamic weather generator using randomized simulation to avoid paid API limits."""
    segments = []
    conditions = ["clear", "partly_cloudy", "haze", "heavy_rain", "thunderstorm"]
    
    # Generate 4 dynamic segments for the requested route
    for i in range(4):
        cond = random.choice(conditions)
        temp = round(random.uniform(25.0, 42.0), 1)
        alert = "heat_warning" if temp > 40 else ("flood_warning" if cond == "heavy_rain" else None)
        segments.append({
            "km_range": f"{i*200}-{(i+1)*200}",
            "region": f"Zone {i+1}",
            "condition": cond,
            "temp_c": temp,
            "humidity_pct": random.randint(30, 95),
            "wind_speed_kmh": random.randint(5, 45),
            "visibility_km": round(random.uniform(1.0, 15.0), 1),
            "rainfall_mm_hr": round(random.uniform(0.0, 50.0), 1) if "rain" in cond or "storm" in cond else 0.0,
            "alert": alert,
        })
        
    return {
        "route_id": route_id,
        "route_name": f"Dynamic Route {route_id}",
        "segments": segments
    }
