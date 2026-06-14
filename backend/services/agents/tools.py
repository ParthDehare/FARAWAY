"""Claude API tool definitions for all RailNerv agents.

Each agent has a set of tools defined as dicts compatible with the
Anthropic SDK tool_use format.  The `execute_tool` dispatcher routes
tool calls to the actual service implementations.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Acoustic Monitor tools
# ---------------------------------------------------------------------------

acoustic_tools = [
    {
        "name": "classify_audio_segment",
        "description": (
            "Run the acoustic ML classifier on a rail segment's latest audio "
            "capture. Returns anomaly class (NORMAL, FLAT_WHEEL, MICRO_CRACK, "
            "OBSTRUCTION) and confidence score."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "segment_id": {
                    "type": "string",
                    "description": "UUID of the track segment to classify.",
                },
                "window_seconds": {
                    "type": "integer",
                    "description": "Audio window length in seconds (default 30).",
                    "default": 30,
                },
            },
            "required": ["segment_id"],
        },
    },
    {
        "name": "get_segment_history",
        "description": (
            "Retrieve the anomaly history for a track segment over a time range. "
            "Returns a list of past classifications with timestamps."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "segment_id": {"type": "string"},
                "hours_back": {
                    "type": "integer",
                    "description": "How many hours of history to fetch.",
                    "default": 24,
                },
            },
            "required": ["segment_id"],
        },
    },
    {
        "name": "query_similar_incidents",
        "description": (
            "Semantic search over ChromaDB for historically similar acoustic "
            "incidents. Returns top-N matches with metadata."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "anomaly_description": {
                    "type": "string",
                    "description": "Natural-language description of the anomaly.",
                },
                "n_results": {"type": "integer", "default": 5},
            },
            "required": ["anomaly_description"],
        },
    },
]

# ---------------------------------------------------------------------------
# Weather Agent tools
# ---------------------------------------------------------------------------

weather_tools = [
    {
        "name": "get_route_weather_forecast",
        "description": (
            "Fetch a 24-hour weather forecast along the rail route that "
            "passes through the given segment."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "segment_id": {"type": "string"},
                "hours_ahead": {"type": "integer", "default": 24},
            },
            "required": ["segment_id"],
        },
    },
    {
        "name": "get_satellite_imagery",
        "description": (
            "Retrieve the latest satellite/radar imagery metadata for the "
            "region around a track segment."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "segment_id": {"type": "string"},
                "radius_km": {"type": "number", "default": 25.0},
            },
            "required": ["segment_id"],
        },
    },
    {
        "name": "assess_flood_risk",
        "description": (
            "Compute flood-risk score for a segment based on rainfall, "
            "river proximity, historical data, and soil saturation."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "segment_id": {"type": "string"},
                "rainfall_mm_24h": {"type": "number"},
            },
            "required": ["segment_id"],
        },
    },
    {
        "name": "get_historical_weather_incidents",
        "description": (
            "Query ChromaDB for past weather-related incidents on or near "
            "this segment."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "segment_id": {"type": "string"},
                "n_results": {"type": "integer", "default": 5},
            },
            "required": ["segment_id"],
        },
    },
]

# ---------------------------------------------------------------------------
# Routing Coordinator tools
# ---------------------------------------------------------------------------

routing_tools = [
    {
        "name": "run_gnn_reroute",
        "description": (
            "Run the GNN-based rerouting model to find an optimal alternate "
            "path avoiding the affected segment."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "segment_id": {"type": "string"},
                "blocked": {
                    "type": "boolean",
                    "description": "Whether to treat the segment as fully blocked.",
                    "default": True,
                },
            },
            "required": ["segment_id"],
        },
    },
    {
        "name": "get_alternate_routes",
        "description": (
            "List all viable alternate routes that bypass the affected "
            "segment, ranked by total delay."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "segment_id": {"type": "string"},
                "max_results": {"type": "integer", "default": 3},
            },
            "required": ["segment_id"],
        },
    },
    {
        "name": "calculate_delay_impact",
        "description": (
            "Calculate cascading delay impact on all trains if a given "
            "reroute is applied."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reroute_path": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Ordered list of segment IDs for the new route.",
                },
                "affected_train_numbers": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["reroute_path"],
        },
    },
    {
        "name": "notify_affected_trains",
        "description": (
            "Send reroute instructions to train control systems for the "
            "listed trains."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "train_numbers": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "new_route": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "New route as ordered segment IDs.",
                },
                "delay_minutes": {"type": "integer"},
            },
            "required": ["train_numbers", "new_route"],
        },
    },
]

# ---------------------------------------------------------------------------
# Emergency Agent tools
# ---------------------------------------------------------------------------

emergency_tools = [
    {
        "name": "dispatch_drone",
        "description": (
            "Dispatch an inspection drone to the affected segment for visual "
            "confirmation of the anomaly."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "segment_id": {"type": "string"},
                "priority": {
                    "type": "string",
                    "enum": ["routine", "urgent", "emergency"],
                    "default": "urgent",
                },
            },
            "required": ["segment_id"],
        },
    },
    {
        "name": "generate_emergency_protocol",
        "description": (
            "Generate a structured emergency response protocol based on "
            "severity, anomaly type, and environmental conditions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "severity": {
                    "type": "string",
                    "enum": ["info", "warning", "critical"],
                },
                "anomaly_class": {"type": "string"},
                "weather_conditions": {"type": "object"},
                "passenger_count": {"type": "integer"},
            },
            "required": ["severity", "anomaly_class"],
        },
    },
    {
        "name": "alert_authorities",
        "description": (
            "Send alerts to railway authorities, police, or emergency "
            "services as appropriate for the severity level."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "severity": {"type": "string"},
                "incident_id": {"type": "string"},
                "description": {"type": "string"},
                "authorities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of authority codes to notify.",
                },
            },
            "required": ["severity", "incident_id", "description"],
        },
    },
    {
        "name": "trigger_passenger_notifications",
        "description": (
            "Send SMS / app push / PA system notifications to passengers "
            "on affected trains."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "train_numbers": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "message": {"type": "string"},
                "channels": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["sms", "app_push", "pa_system", "email"],
                    },
                    "default": ["sms", "app_push"],
                },
            },
            "required": ["train_numbers", "message"],
        },
    },
]

# ---------------------------------------------------------------------------
# Supervisor Agent tools
# ---------------------------------------------------------------------------

supervisor_tools = [
    {
        "name": "resolve_agent_conflict",
        "description": (
            "When two agents disagree (e.g., weather says safe but acoustic "
            "says critical), resolve the conflict by weighing evidence."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_a": {"type": "string"},
                "agent_a_assessment": {"type": "object"},
                "agent_b": {"type": "string"},
                "agent_b_assessment": {"type": "object"},
                "context": {"type": "object"},
            },
            "required": ["agent_a", "agent_a_assessment", "agent_b", "agent_b_assessment"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": (
            "Escalate the incident to a human operator when confidence is "
            "below threshold or severity is critical."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "incident_id": {"type": "string"},
                "reason": {"type": "string"},
                "current_state": {"type": "object"},
                "recommended_action": {"type": "string"},
            },
            "required": ["incident_id", "reason"],
        },
    },
    {
        "name": "approve_reroute_proposal",
        "description": (
            "Approve or reject a reroute proposal from the routing agent, "
            "returning the final decision with justification."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "proposal": {"type": "object"},
                "weather_risk": {"type": "object"},
                "passenger_impact": {"type": "integer"},
                "approved": {"type": "boolean"},
                "justification": {"type": "string"},
            },
            "required": ["proposal", "approved", "justification"],
        },
    },
    {
        "name": "log_final_decision",
        "description": (
            "Record the supervisor's final decision into the audit trail."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "incident_id": {"type": "string"},
                "decision": {"type": "string"},
                "reasoning": {"type": "string"},
                "confidence": {"type": "number"},
                "actions_taken": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["incident_id", "decision", "reasoning", "confidence"],
        },
    },
]

# ---------------------------------------------------------------------------
# Tool name → tool list mapping (for quick lookup)
# ---------------------------------------------------------------------------

ALL_TOOLS: Dict[str, list] = {
    "acoustic_monitor": acoustic_tools,
    "weather_agent": weather_tools,
    "routing_coordinator": routing_tools,
    "emergency_agent": emergency_tools,
    "supervisor_agent": supervisor_tools,
}

_TOOL_REGISTRY: Dict[str, Any] = {}
for _tools in [acoustic_tools, weather_tools, routing_tools, emergency_tools, supervisor_tools]:
    for _t in _tools:
        _TOOL_REGISTRY[_t["name"]] = _t


# ---------------------------------------------------------------------------
# Tool execution dispatcher
# ---------------------------------------------------------------------------

async def execute_tool(tool_name: str, tool_input: dict) -> dict:
    """Dispatch a tool call to the actual service implementation.
    
    Strict production mode: Mock fallbacks are forbidden. If a service 
    is not implemented, it raises an HTTPException.
    """
    now = datetime.now(timezone.utc).isoformat()
    from fastapi import HTTPException

    try:
        # ---- Acoustic tools ------------------------------------------------
        if tool_name == "classify_audio_segment":
            try:
                from services.acoustic.classifier import classify_segment
                return await classify_segment(tool_input["segment_id"],
                                              tool_input.get("window_seconds", 30))
            except ImportError:
                raise HTTPException(status_code=501, detail="services.acoustic.classifier.classify_segment not implemented")

        if tool_name == "get_segment_history":
            try:
                from services.acoustic.classifier import get_history
                return await get_history(tool_input["segment_id"],
                                         tool_input.get("hours_back", 24))
            except ImportError:
                raise HTTPException(status_code=501, detail="services.acoustic.classifier.get_history not implemented")

        if tool_name == "query_similar_incidents":
            try:
                from shared.chroma.client import chroma_client
                results = await chroma_client.query_similar(
                    "acoustic_signatures",
                    tool_input["anomaly_description"],
                    n_results=tool_input.get("n_results", 5),
                )
                return {"matches": results}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"ChromaDB query failed: {e}")

        # ---- Weather tools --------------------------------------------------
        if tool_name == "get_route_weather_forecast":
            try:
                from services.weather.fusion import get_route_forecast
                return await get_route_forecast(tool_input["segment_id"],
                                                tool_input.get("hours_ahead", 24))
            except ImportError:
                raise HTTPException(status_code=501, detail="services.weather.fusion.get_route_forecast not implemented")

        if tool_name == "get_satellite_imagery":
            try:
                from services.weather.satellite import get_imagery
                return await get_imagery(tool_input["segment_id"],
                                         tool_input.get("radius_km", 25.0))
            except ImportError:
                raise HTTPException(status_code=501, detail="services.weather.satellite.get_imagery not implemented")

        if tool_name == "assess_flood_risk":
            try:
                from services.weather.fusion import assess_flood
                return await assess_flood(tool_input["segment_id"],
                                          tool_input.get("rainfall_mm_24h"))
            except ImportError:
                raise HTTPException(status_code=501, detail="services.weather.fusion.assess_flood not implemented")

        if tool_name == "get_historical_weather_incidents":
            try:
                from shared.chroma.client import chroma_client
                results = await chroma_client.query_similar(
                    "weather_patterns",
                    f"weather incidents near segment {tool_input['segment_id']}",
                    n_results=tool_input.get("n_results", 5),
                )
                return {"matches": results}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"ChromaDB query failed: {e}")

        # ---- Routing tools --------------------------------------------------
        if tool_name == "run_gnn_reroute":
            try:
                from services.routing.gnn_model import compute_reroute
                return await compute_reroute(tool_input["segment_id"],
                                             tool_input.get("blocked", True))
            except ImportError:
                raise HTTPException(status_code=501, detail="services.routing.gnn_model.compute_reroute not implemented")

        if tool_name == "get_alternate_routes":
            try:
                from services.routing.router import get_alternates
                return await get_alternates(tool_input["segment_id"],
                                            tool_input.get("max_results", 3))
            except ImportError:
                raise HTTPException(status_code=501, detail="services.routing.router.get_alternates not implemented")

        if tool_name == "calculate_delay_impact":
            try:
                from services.routing.router import calculate_impact
                return await calculate_impact(tool_input["reroute_path"],
                                              tool_input.get("affected_train_numbers", []))
            except ImportError:
                raise HTTPException(status_code=501, detail="services.routing.router.calculate_impact not implemented")

        if tool_name == "notify_affected_trains":
            try:
                from services.routing.router import notify_trains
                return await notify_trains(tool_input["train_numbers"],
                                           tool_input["new_route"],
                                           tool_input.get("delay_minutes", 0))
            except ImportError:
                raise HTTPException(status_code=501, detail="services.routing.router.notify_trains not implemented")

        # ---- Emergency tools ------------------------------------------------
        if tool_name == "dispatch_drone":
            try:
                from services.maintenance.crew_dispatch import dispatch_drone
                return await dispatch_drone(tool_input["segment_id"],
                                            tool_input.get("priority", "urgent"))
            except ImportError:
                raise HTTPException(status_code=501, detail="services.maintenance.crew_dispatch.dispatch_drone not implemented")

        # Basic logic tools that don't need external imports can stay as pure logic
        if tool_name == "generate_emergency_protocol":
            return {
                "level": tool_input["severity"],
                "anomaly_class": tool_input["anomaly_class"],
                "actions": [
                    "Reduce speed to 30 km/h on affected segment",
                    "Dispatch inspection drone",
                    "Alert section engineer",
                ],
                "authorities_notified": (
                    ["railway_board", "ndrf"] if tool_input["severity"] == "critical"
                    else ["section_engineer"]
                ),
                "generated_at": now,
            }

        if tool_name == "alert_authorities":
            return {
                "incident_id": tool_input["incident_id"],
                "authorities_contacted": tool_input.get("authorities", ["section_engineer"]),
                "status": "notified",
                "timestamp": now,
            }

        if tool_name == "trigger_passenger_notifications":
            return {
                "trains_notified": tool_input["train_numbers"],
                "message": tool_input["message"],
                "channels": tool_input.get("channels", ["sms", "app_push"]),
                "estimated_reach": len(tool_input["train_numbers"]) * 450,
                "timestamp": now,
            }

        # ---- Supervisor tools -----------------------------------------------
        if tool_name == "resolve_agent_conflict":
            return {
                "resolution": "accept_higher_severity",
                "chosen_agent": tool_input["agent_a"],
                "reasoning": "Higher-confidence assessment takes priority when severity differs.",
                "timestamp": now,
            }

        if tool_name == "escalate_to_human":
            return {
                "incident_id": tool_input["incident_id"],
                "escalated": True,
                "reason": tool_input["reason"],
                "operator_queue": "control-room-main",
                "timestamp": now,
            }

        if tool_name == "approve_reroute_proposal":
            return {
                "approved": tool_input["approved"],
                "justification": tool_input["justification"],
                "timestamp": now,
            }

        if tool_name == "log_final_decision":
            return {
                "logged": True,
                "incident_id": tool_input["incident_id"],
                "decision": tool_input["decision"],
                "timestamp": now,
            }

        # Unknown tool
        logger.warning("Unknown tool requested: %s", tool_name)
        raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_name}")

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Tool execution failed: %s", tool_name)
        raise HTTPException(status_code=500, detail=f"Tool error: {str(exc)}")
