from fastapi import APIRouter, Body
from datetime import datetime
import uuid
from services.routing.router import compute_reroute

router = APIRouter(prefix="/routing", tags=["Routing"])

@router.post("/reroute")
async def reroute_train(
    train_id: str = Body(...),
    reason: str = Body(default="segment_degraded"),
    affected_segment: str = Body(default="MUM-DEL-KM402"),
):
    """Request a reroute for a train away from a compromised segment."""
    
    # Actually run the NetworkX Dijkstra Pathfinding
    result = await compute_reroute(affected_segment)
    
    return {
        "id": str(uuid.uuid4()),
        "train_id": train_id,
        "reason": reason,
        "affected_segment": affected_segment,
        "original_path": ["BCT", "BRC", "RTM", "NAD", "KOTA", "MTJ", "NDLS"],
        "rerouted_path": result.get("alternate_route", []),
        "additional_time_minutes": result.get("estimated_delay_minutes", 0),
        "additional_distance_km": result.get("path_distance_km", 0),
        "agent": "routing",
        "confidence": 0.95,
        "status": "pending_approval",
        "timestamp": datetime.utcnow().isoformat(),
    }
