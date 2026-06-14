"""Weather Risk Agent — Assesses weather conditions and their impact on rail safety."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import anthropic

SYSTEM_PROMPT = """You are the Weather Risk Agent for RailNerv Sentinel, an Indian Railways safety AI system.

Your role:
- Assess weather conditions along train routes and their impact on rail infrastructure safety.
- Evaluate flood risk for low-lying track segments, especially during monsoon season.
- Monitor rail temperature for buckling risk (critical above 65°C rail temp in Indian summer).
- Indian Railway context: routes like NDLS-BCT Western corridor, segments through Gujarat/Rajasthan.

When using tools, reason step-by-step:
1. Fetch the route weather forecast for the affected corridor.
2. Assess flood risk for vulnerable segments (bridges, cuttings, low embankments).
3. Synthesise an overall weather risk level with recommended speed restrictions or caution orders.

Always return structured JSON with keys: risk_level, rail_temperature_c, flood_risk, reasoning, recommended_action."""

TOOLS = [
    {
        "name": "get_route_weather_forecast",
        "description": "Fetch weather forecast along a rail route corridor including temperature, precipitation, wind speed, and visibility.",
        "input_schema": {
            "type": "object",
            "properties": {
                "route_id": {"type": "string", "description": "Route identifier e.g. NDLS-BCT-RAJDHANI"},
                "segment_id": {"type": "string", "description": "Specific segment if narrowing down e.g. MUM-DEL-KM402"},
                "hours_ahead": {"type": "integer", "description": "Forecast window in hours", "default": 24},
            },
            "required": ["route_id"],
        },
    },
    {
        "name": "assess_flood_risk",
        "description": "Assess flood risk for a segment based on rainfall data, river levels, and drainage capacity.",
        "input_schema": {
            "type": "object",
            "properties": {
                "segment_id": {"type": "string", "description": "Track segment identifier"},
                "rainfall_mm": {"type": "number", "description": "Cumulative rainfall in mm over last 24h"},
                "river_proximity": {"type": "boolean", "description": "Whether segment is near a river crossing"},
            },
            "required": ["segment_id"],
        },
    },
]


def _handle_tool_call(name: str, input_data: dict) -> str:
    """Execute tool calls with mock/deterministic data."""
    if name == "get_route_weather_forecast":
        return json.dumps({
            "route_id": input_data.get("route_id", "NDLS-BCT-RAJDHANI"),
            "forecast": {
                "temperature_c": 44,
                "rail_temperature_c": 52,
                "humidity_pct": 38,
                "wind_speed_kmh": 22,
                "visibility_m": 2800,
                "precipitation_mm_24h": 0,
                "condition": "extreme_heat",
            },
            "alerts": ["Rail temperature approaching buckling threshold on BRC-ADI section"],
        })
    elif name == "assess_flood_risk":
        return json.dumps({
            "segment_id": input_data.get("segment_id", "MUM-DEL-KM402"),
            "flood_risk": "low",
            "water_level_pct": 22,
            "drainage_status": "clear",
            "last_inspection": "2026-06-08",
            "reasoning": "No significant rainfall in corridor. River levels nominal.",
        })
    return json.dumps({"error": f"Unknown tool: {name}"})


def _mock_run(state: dict) -> dict:
    """Deterministic fallback when no API key is set."""
    now = datetime.now(timezone.utc).isoformat()
    segment_id = state.get("segment_id", "MUM-DEL-KM402")

    state["weather_risk"] = "moderate"
    state["rail_temperature_c"] = 52
    state["audit_entries"] = state.get("audit_entries", [])
    state["audit_entries"].append({
        "agent": "weather_risk",
        "action": "weather_assessed",
        "reasoning": (
            f"Route weather assessment for segment {segment_id}: "
            f"Ambient 44°C, rail temperature 52°C (moderate — buckling threshold 65°C). "
            f"No precipitation; flood risk low. Visibility adequate at 2.8 km. "
            f"Recommend speed restriction to 90 km/h on BRC-ADI section as precaution "
            f"until rail temperature falls below 50°C. Caution order not yet warranted."
        ),
        "confidence": 0.82,
        "timestamp": now,
    })
    return state


async def run(state: dict) -> dict:
    """Assess weather risk for the affected route corridor."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _mock_run(state)

    client = anthropic.AsyncAnthropic()
    now = datetime.now(timezone.utc).isoformat()

    user_message = (
        f"Assess weather risk for this rail incident:\n"
        f"- Segment: {state.get('segment_id', 'UNKNOWN')}\n"
        f"- Route: {state.get('route_id', 'NDLS-BCT-RAJDHANI')}\n"
        f"- Current severity: {state.get('severity', 'UNKNOWN')}\n"
        f"- Incident ID: {state.get('incident_id', 'N/A')}\n\n"
        f"Use your tools to get the weather forecast and assess flood risk. "
        f"Then determine the overall weather risk level and recommended actions."
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

    risk_level = "moderate"
    for level in ["critical", "high", "moderate", "low"]:
        if level in final_text.lower():
            risk_level = level
            break

    state["weather_risk"] = risk_level
    state["audit_entries"] = state.get("audit_entries", [])
    state["audit_entries"].append({
        "agent": "weather_risk",
        "action": "weather_assessed",
        "reasoning": final_text[:500],
        "confidence": 0.82,
        "timestamp": now,
    })
    return state
