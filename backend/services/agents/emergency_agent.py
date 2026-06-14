"""Emergency Protocol Agent — Handles critical incidents with drone dispatch and authority alerts."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import anthropic

SYSTEM_PROMPT = """You are the Emergency Protocol Agent for RailNerv Sentinel, an Indian Railways safety AI system.

Your role:
- Activate emergency protocols ONLY when severity is critical.
- Dispatch surveillance drones to the affected segment for visual confirmation.
- Generate emergency protocols per Indian Railway disaster management guidelines.
- Alert relevant authorities: DRM (Divisional Railway Manager), CRS (Commissioner of Railway Safety).
- Indian Railway context: DRM offices at Vadodara, Mumbai Central, Delhi; drone fleet DRN-WR-xxx (Western Railway).

When using tools, reason step-by-step:
1. Dispatch the nearest available drone to the incident location.
2. Generate an emergency protocol with containment and response steps.
3. Alert the appropriate railway authorities based on jurisdiction.

Always return structured JSON with keys: drone_dispatched, protocol_id, authorities_alerted, reasoning."""

TOOLS = [
    {
        "name": "dispatch_drone",
        "description": "Dispatch a surveillance drone to the affected track segment for visual inspection.",
        "input_schema": {
            "type": "object",
            "properties": {
                "segment_id": {"type": "string", "description": "Track segment to inspect"},
                "priority": {"type": "string", "enum": ["normal", "urgent", "emergency"], "description": "Dispatch priority level"},
                "drone_type": {"type": "string", "description": "Drone type: surveillance, thermal, multispectral"},
            },
            "required": ["segment_id", "priority"],
        },
    },
    {
        "name": "generate_emergency_protocol",
        "description": "Generate a standard emergency response protocol based on incident type and severity.",
        "input_schema": {
            "type": "object",
            "properties": {
                "incident_type": {"type": "string", "description": "Type of incident e.g. MICRO_CRACK, OBSTRUCTION, FLOOD"},
                "severity": {"type": "string", "enum": ["warning", "critical"]},
                "segment_id": {"type": "string"},
                "affected_trains": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["incident_type", "severity"],
        },
    },
    {
        "name": "alert_authorities",
        "description": "Send alerts to relevant railway authorities (DRM, CRS, Control Room).",
        "input_schema": {
            "type": "object",
            "properties": {
                "authority_level": {"type": "string", "enum": ["section_controller", "drm", "crs", "railway_board"]},
                "division": {"type": "string", "description": "Railway division e.g. Vadodara, Mumbai Central"},
                "message": {"type": "string", "description": "Alert message content"},
            },
            "required": ["authority_level", "division"],
        },
    },
]


def _handle_tool_call(name: str, input_data: dict) -> str:
    """Execute tool calls with mock/deterministic data."""
    if name == "dispatch_drone":
        return json.dumps({
            "drone_id": "DRN-WR-047",
            "status": "dispatched",
            "segment_id": input_data.get("segment_id", "MUM-DEL-KM402"),
            "eta_minutes": 12,
            "battery_pct": 94,
            "launch_base": "BRC-drone-hub",
        })
    elif name == "generate_emergency_protocol":
        return json.dumps({
            "protocol_id": "EP-2026-0892",
            "steps": [
                "Impose immediate speed restriction 30 km/h on affected section",
                "Halt all trains within 5 km radius pending drone visual confirmation",
                "Activate on-call PWI gang for emergency inspection",
                "Prepare SPURT car for ultrasonic testing if crack confirmed",
                "Notify OHE staff if overhead equipment in vicinity",
            ],
            "containment_radius_km": 5,
            "estimated_response_time_min": 45,
        })
    elif name == "alert_authorities":
        return json.dumps({
            "alert_sent": True,
            "authority": input_data.get("authority_level", "drm"),
            "division": input_data.get("division", "Vadodara"),
            "acknowledged": False,
            "alert_id": "ALT-2026-1847",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    return json.dumps({"error": f"Unknown tool: {name}"})


def _mock_run(state: dict) -> dict:
    """Deterministic fallback when no API key is set."""
    now = datetime.now(timezone.utc).isoformat()
    severity = state.get("severity", "warning")
    segment_id = state.get("segment_id", "MUM-DEL-KM402")

    # Only activate on critical severity
    if severity != "critical":
        state["emergency_activated"] = False
        state["audit_entries"] = state.get("audit_entries", [])
        state["audit_entries"].append({
            "agent": "emergency_protocol",
            "action": "no_action",
            "reasoning": f"Severity is {severity}, not critical. Emergency protocols not activated.",
            "confidence": 0.95,
            "timestamp": now,
        })
        return state

    state["emergency_activated"] = True
    state["drone_dispatched"] = "DRN-WR-047"
    state["protocol_id"] = "EP-2026-0892"
    state["authorities_alerted"] = ["DRM Vadodara"]
    state["audit_entries"] = state.get("audit_entries", [])
    state["audit_entries"].append({
        "agent": "emergency_protocol",
        "action": "emergency_activated",
        "reasoning": (
            f"Critical severity on segment {segment_id}. Emergency protocol EP-2026-0892 activated. "
            f"Drone DRN-WR-047 dispatched from BRC drone hub (ETA 12 min, battery 94%). "
            f"Immediate speed restriction 30 km/h imposed. All trains halted within 5 km radius. "
            f"DRM Vadodara alerted (alert ALT-2026-1847). PWI gang activated for emergency inspection. "
            f"SPURT car on standby for ultrasonic testing."
        ),
        "confidence": 0.93,
        "timestamp": now,
    })
    return state


async def run(state: dict) -> dict:
    """Execute emergency protocols if severity is critical."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _mock_run(state)

    severity = state.get("severity", "warning")
    if severity != "critical":
        now = datetime.now(timezone.utc).isoformat()
        state["emergency_activated"] = False
        state["audit_entries"] = state.get("audit_entries", [])
        state["audit_entries"].append({
            "agent": "emergency_protocol",
            "action": "no_action",
            "reasoning": f"Severity is {severity}, not critical. Emergency protocols not activated.",
            "confidence": 0.95,
            "timestamp": now,
        })
        return state

    client = anthropic.AsyncAnthropic()
    now = datetime.now(timezone.utc).isoformat()

    user_message = (
        f"CRITICAL incident — activate emergency protocols:\n"
        f"- Segment: {state.get('segment_id', 'UNKNOWN')}\n"
        f"- Anomaly: {state.get('anomaly_class', 'UNKNOWN')}\n"
        f"- Confidence: {state.get('confidence', 0.0)}\n"
        f"- Train at risk: {state.get('train_number', '12951')}\n"
        f"- Incident ID: {state.get('incident_id', 'N/A')}\n\n"
        f"Dispatch a drone, generate the emergency protocol, and alert the relevant DRM office."
    )

    messages = [{"role": "user", "content": user_message}]

    for _ in range(6):
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            break

        tool_results = []
        assistant_content = response.content
        for block in assistant_content:
            if block.type == "tool_use":
                result = _handle_tool_call(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        if not tool_results:
            break

        messages.append({"role": "assistant", "content": assistant_content})
        messages.append({"role": "user", "content": tool_results})

    final_text = ""
    for block in response.content:
        if hasattr(block, "text"):
            final_text += block.text

    state["emergency_activated"] = True
    state["drone_dispatched"] = "DRN-WR-047"
    state["protocol_id"] = "EP-2026-0892"
    state["authorities_alerted"] = ["DRM Vadodara"]
    state["audit_entries"] = state.get("audit_entries", [])
    state["audit_entries"].append({
        "agent": "emergency_protocol",
        "action": "emergency_activated",
        "reasoning": final_text[:500],
        "confidence": 0.93,
        "timestamp": now,
    })
    return state
