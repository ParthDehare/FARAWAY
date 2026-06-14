import os
import socketio
import logging
from datetime import datetime

logger = logging.getLogger("railnerv.ws")

redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
mgr = socketio.AsyncRedisManager(redis_url)

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    client_manager=mgr,
    logger=False,
    engineio_logger=False,
)

connected_clients: dict[str, dict] = {}


@sio.event
async def connect(sid, environ, auth=None):
    logger.info(f"Client connected: {sid}")
    connected_clients[sid] = {
        "connected_at": datetime.utcnow().isoformat(),
        "subscriptions": [],
    }
    await sio.emit("server:welcome", {
        "sid": sid,
        "agents": ["acoustic", "weather", "routing", "emergency", "reporter", "supervisor"],
        "timestamp": datetime.utcnow().isoformat(),
    }, room=sid)


@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")
    connected_clients.pop(sid, None)


@sio.event
async def subscribe(sid, data):
    """Subscribe client to specific event channels."""
    channels = data.get("channels", []) if isinstance(data, dict) else []
    if sid in connected_clients:
        connected_clients[sid]["subscriptions"] = channels
    for ch in channels:
        sio.enter_room(sid, ch)
    await sio.emit("subscribed", {"channels": channels}, room=sid)


@sio.event
async def demo_inject(sid, data):
    """Inject a demo event and broadcast it to all clients."""
    event_type = data.get("type", "alert:new")
    payload = data.get("payload", {})
    payload["_injected"] = True
    payload["_injected_by"] = sid
    payload["timestamp"] = datetime.utcnow().isoformat()
    await sio.emit(event_type, payload)
    logger.info(f"Demo event injected by {sid}: {event_type}")


@sio.event
async def agent_invoke(sid, data):
    """Request an agent pipeline run."""
    incident_id = data.get("incident_id", "INC-0000")
    segment_id = data.get("segment_id")
    anomaly_class = data.get("anomaly_class", "NORMAL")
    confidence = data.get("confidence", 0.5)

    if not segment_id:
        await sio.emit("error", {"detail": "segment_id required"}, room=sid)
        return

    from services.agents.graph import run_agent_pipeline
    try:
        # Run the real LangGraph pipeline
        result = await run_agent_pipeline(
            incident_id=incident_id,
            segment_id=segment_id,
            anomaly_class=anomaly_class,
            confidence=confidence,
        )
        
        await sio.emit("agent:decision", {
            "incident_id": incident_id,
            "segment_id": segment_id,
            "decision_state": result,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Agent pipeline failed: {e}")
        await sio.emit("error", {"detail": str(e)}, room=sid)


async def broadcast_event(event_type: str, payload: dict):
    """Broadcast an event to all connected Socket.IO clients via Redis."""
    payload["timestamp"] = payload.get("timestamp", datetime.utcnow().isoformat())
    await sio.emit(event_type, payload)
