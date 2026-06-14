"""LangGraph state machine for the RailNerv 6-agent brain.

Graph topology:
  START -> acoustic_monitor -> [weather_agent, routing_coordinator] (parallel)
        -> supervisor_agent -> [emergency_agent, incident_reporter] (parallel)
        -> END
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from langgraph.graph import END, StateGraph

from .state import RailNervState
from .tools import (
    ALL_TOOLS,
    execute_tool,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Claude API helpers
# ---------------------------------------------------------------------------

_ANTHROPIC_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")


def _get_client():
    """Return an AsyncAnthropic client, raising an error if the key is missing."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        from fastapi import HTTPException
        logger.error("ANTHROPIC_API_KEY not set. Silent mock fallbacks are forbidden.")
        raise HTTPException(
            status_code=500, 
            detail="ANTHROPIC_API_KEY is not configured. Strict production mode forbids mock LLM responses."
        )
    try:
        import anthropic
        return anthropic.AsyncAnthropic(api_key=api_key)
    except Exception as exc:
        logger.error("Failed to create Anthropic client: %s", exc)
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Anthropic client error: {exc}")


def _audit_entry(agent: str, action: str, reasoning: str, confidence: float) -> dict:
    return {
        "agent": agent,
        "action": action,
        "reasoning": reasoning,
        "confidence": confidence,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def _call_claude(
    system_prompt: str,
    user_message: str,
    tools: list,
    max_tokens: int = 2048,
) -> Dict[str, Any]:
    """Call Claude with tools enabled; return the full response message.
    Strictly forbidden from using synthetic fallback responses.
    """
    client = _get_client()

    response = await client.messages.create(
        model=_ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
        tools=tools,
    )

    # Process any tool_use blocks in the response
    result_content: List[dict] = []
    for block in response.content:
        if block.type == "text":
            result_content.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            tool_result = await execute_tool(block.name, block.input)
            result_content.append({
                "type": "tool_result",
                "tool_name": block.name,
                "tool_input": block.input,
                "result": tool_result,
            })

    return {
        "role": "assistant",
        "content": result_content,
        "stop_reason": response.stop_reason,
    }


def _extract_tool_results(response: dict) -> List[dict]:
    """Pull all tool_result dicts from a Claude response."""
    return [b for b in response.get("content", []) if b.get("type") == "tool_result"]


def _extract_text(response: dict) -> str:
    """Concatenate all text blocks from a Claude response."""
    return "\n".join(
        b["text"] for b in response.get("content", []) if b.get("type") == "text"
    )


# ---------------------------------------------------------------------------
# Agent system prompts
# ---------------------------------------------------------------------------

ACOUSTIC_PROMPT = """\
You are the Acoustic Monitor agent of the RailNerv Sentinel system for Indian Railways.
Your job is to analyse the acoustic sensor data for a track segment, classify any anomaly,
and retrieve similar historical incidents from memory.

Given an incident's segment_id, you MUST:
1. Call classify_audio_segment to get the current anomaly class and confidence.
2. Call get_segment_history to see recent patterns.
3. Call query_similar_incidents with a description of what you found.

Return a JSON summary with keys: anomaly_class, confidence, historical_matches, recommendation.
"""

WEATHER_PROMPT = """\
You are the Weather Intelligence agent of RailNerv Sentinel.
Assess weather risk for the affected rail segment and determine if environmental
conditions could worsen the detected anomaly.

Given the segment_id and current anomaly info, you MUST:
1. Call get_route_weather_forecast for upcoming conditions.
2. If rain > 20mm is forecast, call assess_flood_risk.
3. Call get_historical_weather_incidents for past weather-related problems here.

Return a JSON summary with keys: risk_level (low/moderate/high/severe),
conditions, forecast_summary, recommendation.
"""

ROUTING_PROMPT = """\
You are the Routing Coordinator agent of RailNerv Sentinel.
When an anomaly is detected, compute optimal rerouting to minimise delay and risk.

Given the segment_id, anomaly severity, and affected trains, you MUST:
1. Call run_gnn_reroute to get the best alternate path.
2. Call calculate_delay_impact with the proposed reroute.
3. If delay > 30 minutes, also call get_alternate_routes for more options.

Return a JSON summary with keys: original_path, new_path, delay_minutes,
affected_train_count, recommendation.
"""

SUPERVISOR_PROMPT = """\
You are the Supervisor agent of RailNerv Sentinel — the final decision-maker.
You receive assessments from the Weather and Routing agents and must:

1. Check for conflicts between agent assessments. If found, call resolve_agent_conflict.
2. If severity is critical AND confidence < 0.8, call escalate_to_human.
3. If a reroute is proposed, call approve_reroute_proposal with your decision.
4. Call log_final_decision with your reasoning.

Your output determines the severity level and actions the Emergency and Reporter agents take.
Return JSON with keys: approved_actions, severity, reasoning, escalated.
"""

EMERGENCY_PROMPT = """\
You are the Emergency Response agent of RailNerv Sentinel.
Based on the supervisor's decision, execute emergency protocols.

You MUST:
1. If severity is warning or critical, call dispatch_drone.
2. Call generate_emergency_protocol with the incident details.
3. If severity is critical, call alert_authorities.
4. If passengers are affected, call trigger_passenger_notifications.

Return JSON with keys: protocol, drone_dispatched, authorities_notified, passengers_notified.
"""

REPORTER_PROMPT = """\
You are the Incident Reporter agent of RailNerv Sentinel.
Generate a structured incident report from all data gathered by other agents.

Compile the full state into a human-readable summary with:
- Incident ID, timestamp, segment
- Anomaly classification and confidence
- Weather conditions and risk
- Rerouting decision and delay impact
- Emergency actions taken
- Audit trail of all agent decisions

Return the report as a JSON object with key: report (string).
"""


# ---------------------------------------------------------------------------
# Node functions
# ---------------------------------------------------------------------------

async def acoustic_monitor(state: RailNervState) -> dict:
    """Classify the anomaly and pull historical context."""
    user_msg = (
        f"Incident {state['incident_id']} on segment {state['segment_id']}. "
        f"Current classification hint: {state['anomaly_class']} "
        f"(confidence {state['confidence']}). "
        "Please run your tools and return your assessment."
    )
    response = await _call_claude(ACOUSTIC_PROMPT, user_msg, ALL_TOOLS["acoustic_monitor"])

    tool_results = _extract_tool_results(response)
    # Update state from tool results
    updates: dict = {"audit_entries": list(state.get("audit_entries", []))}
    for tr in tool_results:
        if tr["tool_name"] == "classify_audio_segment":
            r = tr["result"]
            updates["anomaly_class"] = r.get("anomaly_class", state["anomaly_class"])
            updates["confidence"] = r.get("confidence", state["confidence"])

    updates["audit_entries"].append(
        _audit_entry(
            "acoustic_monitor",
            "classify",
            _extract_text(response) or "Acoustic classification complete",
            updates.get("confidence", state["confidence"]),
        )
    )
    return updates


async def weather_agent(state: RailNervState) -> dict:
    """Assess weather risk for the segment."""
    user_msg = (
        f"Segment {state['segment_id']} has anomaly {state['anomaly_class']} "
        f"(confidence {state['confidence']}). "
        "Assess weather risk and return your findings."
    )
    response = await _call_claude(WEATHER_PROMPT, user_msg, ALL_TOOLS["weather_agent"])

    tool_results = _extract_tool_results(response)
    weather_risk = {"level": "low", "conditions": {}, "forecast": {}}
    for tr in tool_results:
        if tr["tool_name"] == "get_route_weather_forecast":
            weather_risk["forecast"] = tr["result"]
            weather_risk["level"] = tr["result"].get("risk_level", "low")
        elif tr["tool_name"] == "assess_flood_risk":
            weather_risk["conditions"]["flood_risk"] = tr["result"]
            if tr["result"].get("flood_risk_score", 0) > 0.6:
                weather_risk["level"] = "high"

    updates = {
        "weather_risk": weather_risk,
        "audit_entries": list(state.get("audit_entries", [])),
    }
    updates["audit_entries"].append(
        _audit_entry("weather_agent", "assess_weather", _extract_text(response) or "Weather assessed", 0.9)
    )
    return updates


async def routing_coordinator(state: RailNervState) -> dict:
    """Compute rerouting options."""
    trains_desc = json.dumps(state.get("affected_trains", []))
    user_msg = (
        f"Segment {state['segment_id']} anomaly {state['anomaly_class']}. "
        f"Severity: {state['severity']}. Affected trains: {trains_desc}. "
        "Compute rerouting and return your proposal."
    )
    response = await _call_claude(ROUTING_PROMPT, user_msg, ALL_TOOLS["routing_coordinator"])

    tool_results = _extract_tool_results(response)
    reroute = None
    for tr in tool_results:
        if tr["tool_name"] == "run_gnn_reroute":
            r = tr["result"]
            reroute = {
                "original_path": r.get("original_path", []),
                "new_path": r.get("new_path", []),
                "delay_minutes": r.get("delay_minutes", 0),
            }

    updates = {
        "reroute_proposal": reroute,
        "audit_entries": list(state.get("audit_entries", [])),
    }
    updates["audit_entries"].append(
        _audit_entry("routing_coordinator", "compute_reroute", _extract_text(response) or "Reroute computed", 0.9)
    )
    return updates


async def supervisor_agent(state: RailNervState) -> dict:
    """Make the final decision based on all agent inputs."""
    user_msg = (
        f"Incident {state['incident_id']} — segment {state['segment_id']}.\n"
        f"Anomaly: {state['anomaly_class']} (conf {state['confidence']})\n"
        f"Weather risk: {json.dumps(state.get('weather_risk'))}\n"
        f"Reroute proposal: {json.dumps(state.get('reroute_proposal'))}\n"
        f"Affected trains: {json.dumps(state.get('affected_trains', []))}\n"
        "Review all inputs, resolve conflicts, and issue your decision."
    )
    response = await _call_claude(SUPERVISOR_PROMPT, user_msg, ALL_TOOLS["supervisor_agent"])

    tool_results = _extract_tool_results(response)
    updates: dict = {"audit_entries": list(state.get("audit_entries", []))}

    escalated = False
    for tr in tool_results:
        if tr["tool_name"] == "escalate_to_human":
            escalated = True
            updates["human_override"] = tr["result"]
        elif tr["tool_name"] == "approve_reroute_proposal":
            if not tr["result"].get("approved", False):
                updates["reroute_proposal"] = None

    # Determine final severity
    severity = state["severity"]
    if state["confidence"] >= 0.85 and state["anomaly_class"] in ("MICRO_CRACK", "OBSTRUCTION"):
        severity = "critical"
    elif state["anomaly_class"] == "FLAT_WHEEL":
        severity = "warning"

    updates["severity"] = severity
    updates["audit_entries"].append(
        _audit_entry(
            "supervisor_agent",
            "final_decision",
            _extract_text(response) or f"Severity set to {severity}, escalated={escalated}",
            state["confidence"],
        )
    )
    return updates


async def emergency_agent(state: RailNervState) -> dict:
    """Execute emergency protocols based on supervisor decision."""
    user_msg = (
        f"Incident {state['incident_id']}, severity {state['severity']}.\n"
        f"Anomaly: {state['anomaly_class']}, segment: {state['segment_id']}.\n"
        f"Weather: {json.dumps(state.get('weather_risk'))}\n"
        f"Affected trains: {json.dumps(state.get('affected_trains', []))}\n"
        "Execute appropriate emergency protocols now."
    )
    response = await _call_claude(EMERGENCY_PROMPT, user_msg, ALL_TOOLS["emergency_agent"])

    tool_results = _extract_tool_results(response)
    protocol = None
    crew = None
    notification = None

    for tr in tool_results:
        if tr["tool_name"] == "generate_emergency_protocol":
            protocol = tr["result"]
        elif tr["tool_name"] == "dispatch_drone":
            crew = {"drone": tr["result"]}
        elif tr["tool_name"] == "trigger_passenger_notifications":
            notification = {
                "message": tr["result"].get("message", ""),
                "affected_count": tr["result"].get("estimated_reach", 0),
                "channels": tr["result"].get("channels", []),
            }

    updates = {
        "emergency_protocol": protocol,
        "passenger_notification": notification,
        "audit_entries": list(state.get("audit_entries", [])),
    }
    if crew:
        updates["crew_dispatch"] = crew

    updates["audit_entries"].append(
        _audit_entry("emergency_agent", "execute_protocol", _extract_text(response) or "Protocols executed", 1.0)
    )
    return updates


async def incident_reporter(state: RailNervState) -> dict:
    """Generate the final incident report."""
    full_state = json.dumps(
        {k: v for k, v in state.items() if k != "audit_entries"},
        default=str,
    )
    audit = json.dumps(state.get("audit_entries", []), default=str)
    user_msg = (
        f"Compile the incident report.\nState: {full_state}\nAudit trail: {audit}"
    )
    response = await _call_claude(REPORTER_PROMPT, user_msg, [])  # no tools needed

    report_text = _extract_text(response) or "Report generation complete."
    updates = {
        "resolution": {
            "report": report_text,
            "resolved_at": datetime.now(timezone.utc).isoformat(),
            "severity": state["severity"],
        },
        "audit_entries": list(state.get("audit_entries", [])),
    }
    updates["audit_entries"].append(
        _audit_entry("incident_reporter", "generate_report", "Final report compiled", 1.0)
    )
    return updates


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def _build_graph() -> StateGraph:
    graph = StateGraph(RailNervState)

    # Add nodes
    graph.add_node("acoustic_monitor", acoustic_monitor)
    graph.add_node("weather_agent", weather_agent)
    graph.add_node("routing_coordinator", routing_coordinator)
    graph.add_node("supervisor_agent", supervisor_agent)
    graph.add_node("emergency_agent", emergency_agent)
    graph.add_node("incident_reporter", incident_reporter)

    # Edges: START -> acoustic_monitor
    graph.set_entry_point("acoustic_monitor")

    # acoustic_monitor -> parallel(weather_agent, routing_coordinator)
    graph.add_edge("acoustic_monitor", "weather_agent")
    graph.add_edge("acoustic_monitor", "routing_coordinator")

    # parallel outputs -> supervisor_agent
    graph.add_edge("weather_agent", "supervisor_agent")
    graph.add_edge("routing_coordinator", "supervisor_agent")

    # supervisor -> parallel(emergency_agent, incident_reporter)
    graph.add_edge("supervisor_agent", "emergency_agent")
    graph.add_edge("supervisor_agent", "incident_reporter")

    # parallel outputs -> END
    graph.add_edge("emergency_agent", END)
    graph.add_edge("incident_reporter", END)

    return graph


agent_graph = _build_graph().compile()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def run_agent_pipeline(
    incident_id: str,
    segment_id: str,
    anomaly_class: str = "NORMAL",
    confidence: float = 0.5,
    affected_trains: List[dict] | None = None,
    severity: str = "info",
) -> RailNervState:
    """Run the full 6-agent pipeline and return the final state."""

    initial_state: RailNervState = {
        "incident_id": incident_id,
        "segment_id": segment_id,
        "anomaly_class": anomaly_class,
        "confidence": confidence,
        "weather_risk": None,
        "affected_trains": affected_trains or [],
        "reroute_proposal": None,
        "emergency_protocol": None,
        "crew_dispatch": None,
        "passenger_notification": None,
        "audit_entries": [],
        "human_override": None,
        "resolution": None,
        "severity": severity,
    }

    logger.info("Starting agent pipeline for incident %s", incident_id)
    final_state = await agent_graph.ainvoke(initial_state)
    logger.info("Pipeline complete for incident %s — severity: %s", incident_id, final_state.get("severity"))

    return final_state
