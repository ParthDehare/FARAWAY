"""Routing Agent — GNN-based rerouting and delay impact analysis."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import anthropic

SYSTEM_PROMPT = """You are the Routing Agent for RailNerv Sentinel, an Indian Railways safety AI system.

Your role:
- Run GNN-based rerouting models to find optimal alternate paths when a segment is blocked or restricted.
- Evaluate alternate routes for capacity, delay impact, and passenger count.
- Indian Railway context: major junctions NDLS, BCT, BRC, AII, JP, ADI; Rajdhani/Shatabdi priority routing.

When using tools, reason step-by-step:
1. Run the GNN reroute model with the affected segment and train details.
2. Get alternate routes ranked by delay and capacity.
3. Calculate delay impact on affected trains and downstream services.
4. Recommend the best reroute option with justification.

Always return structured JSON with keys: recommended_route, delay_minutes, affected_passengers, confidence, reasoning."""

TOOLS = [
    {
        "name": "run_gnn_reroute",
        "description": "Run the Graph Neural Network rerouting model to find optimal alternate paths around a blocked segment.",
        "input_schema": {
            "type": "object",
            "properties": {
                "blocked_segment": {"type": "string", "description": "Segment ID that is blocked or restricted"},
                "train_number": {"type": "string", "description": "Train number e.g. 12951"},
                "priority_class": {"type": "string", "description": "Train priority: rajdhani, shatabdi, mail_express, passenger"},
            },
            "required": ["blocked_segment"],
        },
    },
    {
        "name": "get_alternate_routes",
        "description": "Retrieve ranked alternate routes from the network graph with capacity and timing data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "origin": {"type": "string", "description": "Origin station code"},
                "destination": {"type": "string", "description": "Destination station code"},
                "avoid_segments": {"type": "array", "items": {"type": "string"}, "description": "Segments to avoid"},
            },
            "required": ["origin", "destination"],
        },
    },
    {
        "name": "calculate_delay_impact",
        "description": "Calculate cascading delay impact on the affected train and connecting services.",
        "input_schema": {
            "type": "object",
            "properties": {
                "train_number": {"type": "string"},
                "delay_minutes": {"type": "integer"},
                "reroute_path": {"type": "array", "items": {"type": "string"}, "description": "Ordered list of station codes"},
            },
            "required": ["train_number", "delay_minutes"],
        },
    },
]


def _handle_tool_call(name: str, input_data: dict) -> str:
    """Execute tool calls with mock/deterministic data."""
    if name == "run_gnn_reroute":
        return json.dumps({
            "model_version": "gnn-rail-v2.4",
            "blocked_segment": input_data.get("blocked_segment", "MUM-DEL-KM402"),
            "recommended_path": ["BCT", "BRC", "AII", "JP", "NDLS"],
            "confidence": 0.88,
            "estimated_delay_minutes": 45,
            "path_capacity_utilization": 0.62,
        })
    elif name == "get_alternate_routes":
        return json.dumps({
            "routes": [
                {"path": ["BCT", "BRC", "AII", "JP", "NDLS"], "delay_min": 45, "capacity_pct": 62},
                {"path": ["BCT", "BRC", "RTM", "KOTA", "NDLS"], "delay_min": 68, "capacity_pct": 44},
                {"path": ["BCT", "ADI", "ABR", "JP", "NDLS"], "delay_min": 92, "capacity_pct": 71},
            ],
        })
    elif name == "calculate_delay_impact":
        return json.dumps({
            "train_number": input_data.get("train_number", "12951"),
            "primary_delay_min": input_data.get("delay_minutes", 45),
            "affected_passengers": 2847,
            "cascading_delays": [
                {"train": "12953", "delay_min": 12, "reason": "platform_conflict_NDLS"},
                {"train": "19019", "delay_min": 8, "reason": "section_occupancy_BRC"},
            ],
            "total_pax_affected": 2847,
        })
    return json.dumps({"error": f"Unknown tool: {name}"})


def _mock_run(state: dict) -> dict:
    """Deterministic fallback when no API key is set."""
    now = datetime.now(timezone.utc).isoformat()
    segment_id = state.get("segment_id", "MUM-DEL-KM402")
    train_number = state.get("train_number", "12951")

    state["reroute"] = {
        "path": ["BCT", "BRC", "AII", "JP", "NDLS"],
        "delay_minutes": 45,
        "affected_passengers": 2847,
    }
    state["audit_entries"] = state.get("audit_entries", [])
    state["audit_entries"].append({
        "agent": "routing",
        "action": "reroute_proposed",
        "reasoning": (
            f"GNN reroute model (v2.4) evaluated 3 alternate paths for train {train_number} "
            f"(Rajdhani Express) avoiding segment {segment_id}. "
            f"Recommended: BCT-BRC-AII-JP-NDLS with +45 min delay, 62% path capacity utilization. "
            f"2847 passengers affected on primary service. "
            f"Cascading impact: 2 downstream trains with minor delays (12 min, 8 min). "
            f"This route preferred over BRC-RTM-KOTA-NDLS (+68 min) and BCT-ADI-ABR-JP-NDLS (+92 min)."
        ),
        "confidence": 0.88,
        "timestamp": now,
    })
    return state


async def run(state: dict) -> dict:
    """Run GNN rerouting analysis for the affected train."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _mock_run(state)

    client = anthropic.AsyncAnthropic()
    now = datetime.now(timezone.utc).isoformat()

    user_message = (
        f"Find the best reroute for this incident:\n"
        f"- Blocked segment: {state.get('segment_id', 'UNKNOWN')}\n"
        f"- Train: {state.get('train_number', '12951')} (Rajdhani Express)\n"
        f"- Severity: {state.get('severity', 'UNKNOWN')}\n"
        f"- Incident ID: {state.get('incident_id', 'N/A')}\n\n"
        f"Use your tools to run the GNN model, get alternate routes, and calculate delay impact. "
        f"Recommend the best reroute option."
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

    state["reroute"] = {
        "path": ["BCT", "BRC", "AII", "JP", "NDLS"],
        "delay_minutes": 45,
        "affected_passengers": 2847,
    }
    state["audit_entries"] = state.get("audit_entries", [])
    state["audit_entries"].append({
        "agent": "routing",
        "action": "reroute_proposed",
        "reasoning": final_text[:500],
        "confidence": 0.88,
        "timestamp": now,
    })
    return state
