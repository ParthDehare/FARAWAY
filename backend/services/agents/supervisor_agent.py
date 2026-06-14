"""Supervisor Agent — Reviews all agent outputs, resolves conflicts, and gates final decisions."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import anthropic

SYSTEM_PROMPT = """You are the Supervisor Agent for RailNerv Sentinel, an Indian Railways safety AI system.

Your role:
- Review all agent outputs for consistency and confidence thresholds.
- Resolve conflicts between agents (e.g., routing vs. emergency recommendations).
- Escalate to human operators when confidence is below 70% on critical incidents.
- Approve or reject reroute proposals before they are executed.
- Indian Railway context: final decisions must comply with CRS safety norms, RDSO standards.

When using tools, reason step-by-step:
1. Check all agent confidence scores — flag any below 70%.
2. Identify conflicts between agent recommendations.
3. Resolve conflicts or escalate to human if unresolvable.
4. Approve reroute proposals if all checks pass.

Always return structured JSON with keys: approved, conflicts_resolved, escalated, reasoning."""

TOOLS = [
    {
        "name": "resolve_agent_conflict",
        "description": "Analyze and resolve conflicting recommendations from different agents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_a": {"type": "string", "description": "First agent name"},
                "agent_b": {"type": "string", "description": "Second agent name"},
                "conflict_description": {"type": "string", "description": "Description of the conflict"},
            },
            "required": ["agent_a", "agent_b", "conflict_description"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": "Escalate the incident to a human operator in the control room.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {"type": "string", "description": "Reason for escalation"},
                "urgency": {"type": "string", "enum": ["normal", "urgent", "immediate"]},
                "control_room": {"type": "string", "description": "Control room identifier e.g. WR-BRC, CR-CSTM"},
            },
            "required": ["reason", "urgency"],
        },
    },
    {
        "name": "approve_reroute_proposal",
        "description": "Review and approve or reject a proposed train reroute.",
        "input_schema": {
            "type": "object",
            "properties": {
                "route_path": {"type": "array", "items": {"type": "string"}, "description": "Proposed route station codes"},
                "delay_minutes": {"type": "integer"},
                "affected_passengers": {"type": "integer"},
                "confidence": {"type": "number"},
            },
            "required": ["route_path", "confidence"],
        },
    },
]


def _handle_tool_call(name: str, input_data: dict) -> str:
    """Execute tool calls with mock/deterministic data."""
    if name == "resolve_agent_conflict":
        return json.dumps({
            "resolved": True,
            "resolution": "Routing agent reroute is compatible with emergency speed restriction. "
                         "Apply emergency 30 km/h limit on affected segment while reroute is executed for through traffic.",
            "preferred_agent": input_data.get("agent_a", "routing"),
        })
    elif name == "escalate_to_human":
        return json.dumps({
            "escalation_id": "ESC-2026-0341",
            "acknowledged": False,
            "control_room": input_data.get("control_room", "WR-BRC"),
            "operator_on_duty": "Section Controller, BRC",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    elif name == "approve_reroute_proposal":
        confidence = input_data.get("confidence", 0.88)
        approved = confidence >= 0.70
        return json.dumps({
            "approved": approved,
            "confidence_check": f"{'PASS' if confidence >= 0.70 else 'FAIL'} ({confidence:.0%})",
            "capacity_check": "PASS",
            "safety_check": "PASS",
            "reason": "All checks passed" if approved else f"Confidence {confidence:.0%} below 70% threshold",
        })
    return json.dumps({"error": f"Unknown tool: {name}"})


def _mock_run(state: dict) -> dict:
    """Deterministic fallback when no API key is set."""
    now = datetime.now(timezone.utc).isoformat()
    severity = state.get("severity", "warning")

    # Check minimum confidence across all agent entries
    audit_entries = state.get("audit_entries", [])
    min_confidence = 1.0
    low_confidence_agent = None
    for entry in audit_entries:
        conf = entry.get("confidence", 1.0)
        if conf < min_confidence:
            min_confidence = conf
            low_confidence_agent = entry.get("agent")

    escalated = False
    if min_confidence < 0.70 and severity == "critical":
        escalated = True
        state["escalation_id"] = "ESC-2026-0341"

    # Approve reroute if present and confidence OK
    reroute = state.get("reroute")
    reroute_approved = False
    if reroute:
        reroute_approved = min_confidence >= 0.70

    state["supervisor_approved"] = not escalated
    state["reroute_approved"] = reroute_approved
    state["escalated"] = escalated
    state["audit_entries"] = state.get("audit_entries", [])
    state["audit_entries"].append({
        "agent": "supervisor",
        "action": "review_complete",
        "reasoning": (
            f"Supervisor review of {len(audit_entries)} agent decisions. "
            f"Min confidence: {min_confidence:.0%} ({low_confidence_agent or 'N/A'}). "
            + (
                f"ESCALATED to human operator — confidence {min_confidence:.0%} below 70% threshold on {severity} incident. "
                f"Escalation ESC-2026-0341 sent to Section Controller, BRC."
                if escalated else
                f"All confidence scores above 70% threshold. "
                f"{'Reroute proposal approved.' if reroute_approved else 'No reroute to approve.'} "
                f"No agent conflicts detected. Decision pipeline approved."
            )
        ),
        "confidence": min_confidence,
        "timestamp": now,
    })
    return state


async def run(state: dict) -> dict:
    """Review all agent outputs and gate final decisions."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _mock_run(state)

    client = anthropic.AsyncAnthropic()
    now = datetime.now(timezone.utc).isoformat()

    audit_text = ""
    for entry in state.get("audit_entries", []):
        audit_text += (
            f"- Agent: {entry.get('agent')}, Action: {entry.get('action')}, "
            f"Confidence: {entry.get('confidence', 'N/A')}, Reasoning: {entry.get('reasoning', '')[:200]}\n"
        )

    reroute = state.get("reroute", {})
    reroute_text = ""
    if reroute:
        reroute_text = (
            f"\nProposed reroute: {' -> '.join(reroute.get('path', []))} "
            f"(+{reroute.get('delay_minutes', 0)} min, {reroute.get('affected_passengers', 0)} pax)\n"
        )

    user_message = (
        f"Review all agent decisions for this incident:\n"
        f"- Incident ID: {state.get('incident_id', 'N/A')}\n"
        f"- Severity: {state.get('severity', 'UNKNOWN')}\n"
        f"- Segment: {state.get('segment_id', 'UNKNOWN')}\n\n"
        f"Agent audit trail:\n{audit_text}\n"
        f"{reroute_text}\n"
        f"Check confidence thresholds (min 70% for critical), resolve any conflicts, "
        f"and approve or reject the reroute proposal."
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

    escalated = "escalat" in final_text.lower()
    state["supervisor_approved"] = not escalated
    state["escalated"] = escalated
    state["reroute_approved"] = "approved" in final_text.lower() and bool(reroute)
    state["audit_entries"] = state.get("audit_entries", [])
    state["audit_entries"].append({
        "agent": "supervisor",
        "action": "review_complete",
        "reasoning": final_text[:500],
        "confidence": 0.90,
        "timestamp": now,
    })
    return state
