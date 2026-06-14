"""Crew Dispatch Agent — Dispatches maintenance crews and creates work orders."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import anthropic

SYSTEM_PROMPT = """You are the Crew Dispatch Agent for RailNerv Sentinel, an Indian Railways safety AI system.

Your role:
- Create work orders for track maintenance and inspection tasks.
- Find the nearest available maintenance crew (PWI gang, S&T, OHE, TRD staff).
- Assign crews to work orders with estimated arrival and completion times.
- Indian Railway context: PWI (Permanent Way Inspector) gangs, track maintenance blocks,
  BRC/ADI/NDLS crew depots, keyman beats, trolley refuges.

When using tools, reason step-by-step:
1. Create a work order for the required maintenance/inspection task.
2. Find the nearest available crew with the right specialization.
3. Assign the crew to the work order with scheduling details.

Always return structured JSON with keys: work_order_id, crew_assigned, eta_minutes, reasoning."""

TOOLS = [
    {
        "name": "create_work_order",
        "description": "Create a maintenance work order for track inspection or repair.",
        "input_schema": {
            "type": "object",
            "properties": {
                "segment_id": {"type": "string", "description": "Track segment requiring work"},
                "work_type": {"type": "string", "description": "Type: visual_inspection, ultrasonic_test, rail_replacement, joint_repair"},
                "priority": {"type": "string", "enum": ["routine", "urgent", "emergency"]},
                "description": {"type": "string", "description": "Detailed work description"},
            },
            "required": ["segment_id", "work_type", "priority"],
        },
    },
    {
        "name": "find_nearest_crew",
        "description": "Find the nearest available maintenance crew for the given work type and location.",
        "input_schema": {
            "type": "object",
            "properties": {
                "segment_id": {"type": "string", "description": "Target segment"},
                "crew_type": {"type": "string", "description": "Crew type: pwi_gang, snt_staff, ohe_staff, trd_staff"},
                "min_crew_size": {"type": "integer", "description": "Minimum crew members required", "default": 4},
            },
            "required": ["segment_id", "crew_type"],
        },
    },
    {
        "name": "assign_crew_to_order",
        "description": "Assign a maintenance crew to a work order with scheduling details.",
        "input_schema": {
            "type": "object",
            "properties": {
                "work_order_id": {"type": "string"},
                "crew_id": {"type": "string"},
                "estimated_start": {"type": "string", "description": "ISO datetime for estimated start"},
            },
            "required": ["work_order_id", "crew_id"],
        },
    },
]


def _handle_tool_call(name: str, input_data: dict) -> str:
    """Execute tool calls with mock/deterministic data."""
    if name == "create_work_order":
        return json.dumps({
            "work_order_id": "WO-2026-04817",
            "segment_id": input_data.get("segment_id", "MUM-DEL-KM402"),
            "work_type": input_data.get("work_type", "visual_inspection"),
            "priority": input_data.get("priority", "urgent"),
            "status": "created",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    elif name == "find_nearest_crew":
        return json.dumps({
            "crew_id": "PWI-GANG-07-BRC",
            "crew_type": "pwi_gang",
            "base_station": "BRC",
            "crew_size": 6,
            "gang_leader": "SSE/P.Way/BRC",
            "current_status": "available",
            "distance_km": 18,
            "eta_minutes": 35,
        })
    elif name == "assign_crew_to_order":
        return json.dumps({
            "assignment_id": "ASG-2026-1192",
            "work_order_id": input_data.get("work_order_id", "WO-2026-04817"),
            "crew_id": input_data.get("crew_id", "PWI-GANG-07-BRC"),
            "status": "assigned",
            "estimated_start": input_data.get("estimated_start", datetime.now(timezone.utc).isoformat()),
            "estimated_completion_hours": 3,
            "block_section_required": True,
        })
    return json.dumps({"error": f"Unknown tool: {name}"})


def _mock_run(state: dict) -> dict:
    """Deterministic fallback when no API key is set."""
    now = datetime.now(timezone.utc).isoformat()
    segment_id = state.get("segment_id", "MUM-DEL-KM402")
    severity = state.get("severity", "warning")

    priority = "emergency" if severity == "critical" else "urgent"

    state["work_order_id"] = "WO-2026-04817"
    state["crew_dispatched"] = {
        "crew_id": "PWI-GANG-07-BRC",
        "base_station": "BRC",
        "crew_size": 6,
        "eta_minutes": 35,
    }
    state["audit_entries"] = state.get("audit_entries", [])
    state["audit_entries"].append({
        "agent": "crew_dispatch",
        "action": "crew_dispatched",
        "reasoning": (
            f"Work order WO-2026-04817 created ({priority} priority) for segment {segment_id}. "
            f"Nearest available crew: PWI Gang 07, base BRC (6 members, SSE/P.Way/BRC). "
            f"Distance 18 km, ETA 35 min. Assignment ASG-2026-1192 confirmed. "
            f"Block section will be required for inspection — coordinating with Section Controller. "
            f"Estimated completion: 3 hours from arrival."
        ),
        "confidence": 0.91,
        "timestamp": now,
    })
    return state


async def run(state: dict) -> dict:
    """Dispatch maintenance crew to the affected segment."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _mock_run(state)

    client = anthropic.AsyncAnthropic()
    now = datetime.now(timezone.utc).isoformat()
    severity = state.get("severity", "warning")
    priority = "emergency" if severity == "critical" else "urgent"

    user_message = (
        f"Dispatch a maintenance crew for this incident:\n"
        f"- Segment: {state.get('segment_id', 'UNKNOWN')}\n"
        f"- Anomaly: {state.get('anomaly_class', 'UNKNOWN')}\n"
        f"- Severity: {severity}\n"
        f"- Priority: {priority}\n"
        f"- Incident ID: {state.get('incident_id', 'N/A')}\n\n"
        f"Create a work order, find the nearest PWI gang, and assign them."
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

    state["work_order_id"] = "WO-2026-04817"
    state["crew_dispatched"] = {
        "crew_id": "PWI-GANG-07-BRC",
        "base_station": "BRC",
        "crew_size": 6,
        "eta_minutes": 35,
    }
    state["audit_entries"] = state.get("audit_entries", [])
    state["audit_entries"].append({
        "agent": "crew_dispatch",
        "action": "crew_dispatched",
        "reasoning": final_text[:500],
        "confidence": 0.91,
        "timestamp": now,
    })
    return state
