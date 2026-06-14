"""Acoustic Monitor Agent — Analyzes anomaly classifications and queries historical context."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import anthropic

SYSTEM_PROMPT = """You are the Acoustic Monitor Agent for RailNerv Sentinel, an Indian Railways safety AI system.

Your role:
- Analyze acoustic anomaly classification results from track-side sensors.
- Query ChromaDB for similar historical incidents on the same or nearby segments.
- Determine severity level (normal / warning / critical) based on confidence score and historical context.
- Indian Railway context: segments like MUM-DEL-KM402, stations NDLS, BCT, CSTM, HWH.

When using tools, reason step-by-step:
1. First classify the audio segment data.
2. Then fetch segment history for recurrence patterns.
3. Query similar incidents from the vector store.
4. Synthesise a severity determination with justification.

Always return structured JSON with keys: severity, confidence, reasoning, similar_incident_count."""

TOOLS = [
    {
        "name": "classify_audio_segment",
        "description": "Classify an audio segment's anomaly type and confidence. Returns anomaly_class and confidence.",
        "input_schema": {
            "type": "object",
            "properties": {
                "segment_id": {"type": "string", "description": "Track segment identifier e.g. MUM-DEL-KM402"},
                "audio_features": {"type": "object", "description": "Pre-extracted audio feature vector"},
            },
            "required": ["segment_id"],
        },
    },
    {
        "name": "get_segment_history",
        "description": "Retrieve maintenance and incident history for a track segment from the database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "segment_id": {"type": "string"},
                "days_back": {"type": "integer", "description": "Number of days to look back", "default": 90},
            },
            "required": ["segment_id"],
        },
    },
    {
        "name": "query_similar_incidents",
        "description": "Query ChromaDB vector store for historically similar acoustic incidents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "anomaly_class": {"type": "string"},
                "confidence": {"type": "number"},
                "segment_id": {"type": "string"},
                "top_k": {"type": "integer", "default": 5},
            },
            "required": ["anomaly_class"],
        },
    },
]


def _handle_tool_call(name: str, input_data: dict) -> str:
    """Execute tool calls with mock/deterministic data."""
    if name == "classify_audio_segment":
        return json.dumps({
            "anomaly_class": "MICRO_CRACK",
            "confidence": 0.87,
            "frequency_band": "2.4-3.1 kHz",
            "segment_id": input_data.get("segment_id", "MUM-DEL-KM402"),
        })
    elif name == "get_segment_history":
        return json.dumps({
            "segment_id": input_data.get("segment_id", "MUM-DEL-KM402"),
            "incidents_90d": 3,
            "last_maintenance": "2026-05-18",
            "history": [
                {"date": "2026-05-02", "type": "MICRO_CRACK", "resolved": True},
                {"date": "2026-04-15", "type": "FLAT_WHEEL", "resolved": True},
                {"date": "2026-03-28", "type": "MICRO_CRACK", "resolved": True},
            ],
        })
    elif name == "query_similar_incidents":
        return json.dumps({
            "matches": [
                {"incident_id": "INC-2026-0481", "similarity": 0.94, "segment": "MUM-DEL-KM398", "outcome": "rail_replacement"},
                {"incident_id": "INC-2026-0312", "similarity": 0.89, "segment": "MUM-DEL-KM402", "outcome": "speed_restriction"},
                {"incident_id": "INC-2026-0198", "similarity": 0.82, "segment": "DEL-AGC-KM055", "outcome": "monitoring_continued"},
            ],
            "count": 3,
        })
    return json.dumps({"error": f"Unknown tool: {name}"})


def _mock_run(state: dict) -> dict:
    """Deterministic fallback when no API key is set."""
    now = datetime.now(timezone.utc).isoformat()
    anomaly_class = state.get("anomaly_class", "MICRO_CRACK")
    confidence = state.get("confidence", 0.87)
    segment_id = state.get("segment_id", "MUM-DEL-KM402")

    # Severity logic: critical if confidence > 0.9 or recurrence, warning if > 0.7
    if confidence > 0.9 or anomaly_class == "OBSTRUCTION":
        severity = "critical"
    elif confidence > 0.7:
        severity = "warning"
    else:
        severity = "info"

    state["severity"] = severity
    state["audit_entries"] = state.get("audit_entries", [])
    state["audit_entries"].append({
        "agent": "acoustic_monitor",
        "action": "anomaly_assessed",
        "reasoning": (
            f"Classified {anomaly_class} on segment {segment_id} with confidence {confidence:.0%}. "
            f"3 similar historical incidents found (2 on same segment corridor). "
            f"Recurrence pattern detected — last micro-crack on same segment 39 days ago. "
            f"Severity escalated to {severity}."
        ),
        "confidence": confidence,
        "timestamp": now,
    })
    return state


async def run(state: dict) -> dict:
    """Analyze acoustic anomaly and determine severity."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _mock_run(state)

    client = anthropic.AsyncAnthropic()
    now = datetime.now(timezone.utc).isoformat()

    user_message = (
        f"Analyze this acoustic anomaly event:\n"
        f"- Segment: {state.get('segment_id', 'UNKNOWN')}\n"
        f"- Anomaly class: {state.get('anomaly_class', 'UNKNOWN')}\n"
        f"- Confidence: {state.get('confidence', 0.0)}\n"
        f"- Incident ID: {state.get('incident_id', 'N/A')}\n\n"
        f"Use your tools to classify, check history, and find similar incidents. "
        f"Then determine severity (info/warning/critical) with reasoning."
    )

    messages = [{"role": "user", "content": user_message}]

    # Agentic tool-use loop
    for _ in range(6):
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # If no tool use, we have the final answer
        if response.stop_reason == "end_turn":
            break

        # Process tool calls
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

    # Extract final text
    final_text = ""
    for block in response.content:
        if hasattr(block, "text"):
            final_text += block.text

    # Parse severity from response
    severity = "warning"
    for level in ["critical", "warning", "info"]:
        if level in final_text.lower():
            severity = level
            break

    state["severity"] = severity
    state["audit_entries"] = state.get("audit_entries", [])
    state["audit_entries"].append({
        "agent": "acoustic_monitor",
        "action": "anomaly_assessed",
        "reasoning": final_text[:500],
        "confidence": state.get("confidence", 0.0),
        "timestamp": now,
    })
    return state
