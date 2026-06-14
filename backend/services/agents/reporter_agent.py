"""Reporter Agent — Generates natural language incident reports from agent state."""

from __future__ import annotations

import os
from datetime import datetime, timezone

import anthropic

SYSTEM_PROMPT = """You are the Incident Reporter Agent for RailNerv Sentinel, an Indian Railways safety AI system.

Your role:
- Compile all agent findings into a clear, structured incident report.
- Write in formal Indian Railway reporting style suitable for DRM/CRS review.
- Include: Executive Summary, Agent Decisions, Recommended Actions, Risk Assessment.
- Reference Indian Railway terminology: caution orders, SPURT car, PWI gang, OHE, TRD, S&T.

Generate a well-formatted report with sections. Be concise but thorough. Include all agent audit entries."""

TOOLS: list = []


def _handle_tool_call(name: str, input_data: dict) -> str:
    """No tools for reporter agent."""
    return '{"error": "Reporter agent has no tools"}'


def _mock_run(state: dict) -> dict:
    """Deterministic fallback when no API key is set."""
    now = datetime.now(timezone.utc).isoformat()
    incident_id = state.get("incident_id", "INC-2026-0512")
    segment_id = state.get("segment_id", "MUM-DEL-KM402")
    severity = state.get("severity", "warning")
    anomaly_class = state.get("anomaly_class", "MICRO_CRACK")
    train_number = state.get("train_number", "12951")

    audit_entries = state.get("audit_entries", [])
    agent_summary = ""
    for entry in audit_entries:
        agent_summary += f"  - [{entry.get('agent', 'unknown')}] {entry.get('action', 'N/A')}: {entry.get('reasoning', '')[:200]}\n"

    if not agent_summary:
        agent_summary = "  - No agent decisions recorded.\n"

    reroute = state.get("reroute", {})
    reroute_info = ""
    if reroute:
        reroute_info = (
            f"  - Reroute via {' -> '.join(reroute.get('path', []))} "
            f"(+{reroute.get('delay_minutes', 0)} min, {reroute.get('affected_passengers', 0)} pax affected)\n"
        )

    report = (
        f"{'=' * 60}\n"
        f"RAILNERV SENTINEL — INCIDENT REPORT\n"
        f"{'=' * 60}\n"
        f"Incident ID   : {incident_id}\n"
        f"Generated     : {now}\n"
        f"Severity      : {severity.upper()}\n"
        f"Segment       : {segment_id}\n"
        f"Anomaly       : {anomaly_class}\n"
        f"{'=' * 60}\n\n"
        f"EXECUTIVE SUMMARY\n"
        f"{'-' * 40}\n"
        f"Acoustic sensors detected {anomaly_class} anomaly on segment {segment_id} "
        f"with high confidence. Multi-agent analysis completed. "
        f"Severity assessed as {severity}. "
        f"Train {train_number} (Mumbai Rajdhani Express) is the primary affected service.\n\n"
        f"AGENT DECISIONS\n"
        f"{'-' * 40}\n"
        f"{agent_summary}\n"
        f"RECOMMENDED ACTIONS\n"
        f"{'-' * 40}\n"
        f"  1. Issue caution order for segment {segment_id} — speed restriction as per severity.\n"
        f"  2. Deploy SPURT car for ultrasonic rail testing within 24 hours.\n"
        f"  3. PWI gang to conduct visual inspection at earliest available block.\n"
        f"{reroute_info}"
        f"  4. Monitor segment via drone/acoustic sensors for 72 hours post-inspection.\n"
        f"  5. Update asset register with inspection findings.\n\n"
        f"RISK ASSESSMENT\n"
        f"{'-' * 40}\n"
        f"  Overall risk  : {severity.upper()}\n"
        f"  Weather factor: {state.get('weather_risk', 'nominal')}\n"
        f"  Recurrence    : Historical pattern detected on corridor.\n"
        f"  Next review   : 24 hours or upon drone/inspection findings.\n"
        f"{'=' * 60}\n"
        f"END OF REPORT — RailNerv Sentinel v2.0\n"
        f"{'=' * 60}\n"
    )

    state["report"] = report
    state["audit_entries"] = state.get("audit_entries", [])
    state["audit_entries"].append({
        "agent": "reporter",
        "action": "report_generated",
        "reasoning": f"Incident report generated for {incident_id}. Severity: {severity}. All agent findings compiled.",
        "confidence": 1.0,
        "timestamp": now,
    })
    return state


async def run(state: dict) -> dict:
    """Generate a natural language incident report."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _mock_run(state)

    client = anthropic.AsyncAnthropic()
    now = datetime.now(timezone.utc).isoformat()

    audit_text = ""
    for entry in state.get("audit_entries", []):
        audit_text += f"- Agent: {entry.get('agent')}, Action: {entry.get('action')}, Reasoning: {entry.get('reasoning')}\n"

    user_message = (
        f"Generate an incident report for:\n"
        f"- Incident ID: {state.get('incident_id', 'N/A')}\n"
        f"- Segment: {state.get('segment_id', 'UNKNOWN')}\n"
        f"- Severity: {state.get('severity', 'UNKNOWN')}\n"
        f"- Anomaly: {state.get('anomaly_class', 'UNKNOWN')}\n"
        f"- Train: {state.get('train_number', '12951')}\n\n"
        f"Agent audit trail:\n{audit_text}\n"
        f"Compile a formal incident report with Executive Summary, Agent Decisions, "
        f"Recommended Actions, and Risk Assessment sections."
    )

    messages = [{"role": "user", "content": user_message}]

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=messages,
    )

    final_text = ""
    for block in response.content:
        if hasattr(block, "text"):
            final_text += block.text

    state["report"] = final_text
    state["audit_entries"] = state.get("audit_entries", [])
    state["audit_entries"].append({
        "agent": "reporter",
        "action": "report_generated",
        "reasoning": f"Incident report generated for {state.get('incident_id', 'N/A')}.",
        "confidence": 1.0,
        "timestamp": now,
    })
    return state
