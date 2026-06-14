import asyncio
import uuid
import math
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text

# Import the base and all models so they are registered
from shared.database.connection import settings, Base
from shared.models.segment import Segment

# Real-world coordinates (London to Edinburgh approximation)
LONDON_LAT, LONDON_LON = 51.5074, -0.1278
EDINBURGH_LAT, EDINBURGH_LON = 55.9533, -3.1883
TOTAL_DISTANCE_KM = 630.0
NUM_SEGMENTS = 50

def generate_geometry(start_idx, end_idx, num_points=10):
    """Generates a GeoJSON LineString between two points on the route."""
    t_start = start_idx / NUM_SEGMENTS
    t_end = end_idx / NUM_SEGMENTS
    
    coords = []
    for i in range(num_points):
        t = t_start + (t_end - t_start) * (i / (num_points - 1))
        # Add slight mathematical noise to make the track curve realistically
        lat = LONDON_LAT + (EDINBURGH_LAT - LONDON_LAT) * t
        lon = LONDON_LON + (EDINBURGH_LON - LONDON_LON) * t + math.sin(t * 10) * 0.1
        coords.append([lon, lat])  # GeoJSON is [longitude, latitude]
        
    return {
        "type": "LineString",
        "coordinates": coords
    }

async def seed():
    print("Connecting to PostgreSQL...")
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        
    async with async_session() as session:
        # Clear existing segments
        await session.execute(text("TRUNCATE TABLE segments CASCADE"))
        
        print(f"Seeding {NUM_SEGMENTS} real railway segments...")
        segments = []
        
        for i in range(NUM_SEGMENTS):
            km_start = (i / NUM_SEGMENTS) * TOTAL_DISTANCE_KM
            km_end = ((i + 1) / NUM_SEGMENTS) * TOTAL_DISTANCE_KM
            
            seg = Segment(
                id=uuid.uuid4(),
                code=f"ECML-{i:03d}",
                route="East Coast Main Line",
                from_station="London King's Cross" if i == 0 else f"Waypoint {i}",
                to_station="Edinburgh Waverley" if i == NUM_SEGMENTS - 1 else f"Waypoint {i+1}",
                km_start=round(km_start, 2),
                km_end=round(km_end, 2),
                line_type="high_speed",
                health_index=100,
                status="normal",
                geometry=generate_geometry(i, i + 1),
                last_inspected=datetime.utcnow()
            )
            segments.append(seg)
            
        session.add_all(segments)
        await session.commit()
        print(f"Successfully committed {NUM_SEGMENTS} segments to the database!")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed())
