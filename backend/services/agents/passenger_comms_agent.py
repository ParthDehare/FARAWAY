"""Passenger Communications Agent — Generates passenger-facing notifications and announcements."""

from __future__ import annotations

import os
from datetime import datetime, timezone

import anthropic

SYSTEM_PROMPT = """You are the Passenger Communications Agent for RailNerv Sentinel, an Indian Railways safety AI system.

Your role:
- Generate clear, calm, and reassuring passenger notifications for affected trains.
- Write announcements suitable for SMS, app push notifications, and station PA systems.
- Never reveal internal severity classifications or technical details to passengers.
- Use Indian Railways passenger communication style: train numbers, station names, expected delays.
- Provide alternative arrangements when available (reroute info, refund eligibility).

Generate messages that are informative but do not cause panic. Always include train number, expected delay, and helpline."""

TOOLS: list = []


def _handle_tool_call(name: str, input_data: dict) -> str:
    """No tools for passenger comms agent."""
    return '{"error": "Passenger comms agent has no tools"}'


def _mock_run(state: dict) -> dict:
    """Deterministic fallback when no API key is set."""
    now = datetime.now(timezone.utc).isoformat()
    train_number = state.get("train_number", "12951")
    reroute = state.get("reroute", {})
    delay_minutes = reroute.get("delay_minutes", 30) if reroute else 30

    # SMS notification
    sms_message = (
        f"Indian Railways Alert: Train {train_number} (Mumbai Central - New Delhi Rajdhani Exp) "
        f"is expected to arrive approx {delay_minutes} min late due to a precautionary speed restriction "
        f"on the route. Your safety is our priority. "
        f"For assistance call 139 or visit enquiry.indianrail.gov.in. We regret the inconvenience."
    )

    # Station PA announcement
    pa_announcement = (
        f"Attention please. Train number {train_number}, Mumbai Central to New Delhi Rajdhani Express, "
        f"is running approximately {delay_minutes} minutes behind schedule due to operational reasons. "
        f"Passengers are requested to check the updated arrival time on the display boards. "
        f"For any assistance, please contact the station master or call helpline 139. "
        f"Indian Railways regrets the inconvenience."
    )

    # App push notification
    push_notification = {
        "title": f"Train {train_number} Rajdhani Exp — Delay Alert",
        "body": (
            f"Your train is expected {delay_minutes} min late due to a precautionary measure on route. "
            f"Revised ETA will be updated shortly. Call 139 for help."
        ),
    }

    state["passenger_notifications"] = {
        "sms": sms_message,
        "pa_announcement": pa_announcement,
        "push_notification": push_notification,
    }
    state["audit_entries"] = state.get("audit_entries", [])
    state["audit_entries"].append({
        "agent": "passenger_comms",
        "action": "notifications_generated",
        "reasoning": (
            f"Generated passenger notifications for train {train_number}: "
            f"SMS, station PA announcement, and app push notification. "
            f"Delay communicated as {delay_minutes} min. "
            f"No technical details or severity levels disclosed. "
            f"Helpline 139 referenced in all messages."
        ),
        "confidence": 0.96,
        "timestamp": now,
    })
    return state


async def run(state: dict) -> dict:
    """Generate passenger-facing notifications for the incident."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _mock_run(state)

    client = anthropic.AsyncAnthropic()
    now = datetime.now(timezone.utc).isoformat()

    reroute = state.get("reroute", {})
    delay_minutes = reroute.get("delay_minutes", 30) if reroute else 30

    user_message = (
        f"Generate passenger notifications for this incident:\n"
        f"- Train: {state.get('train_number', '12951')} (Mumbai Rajdhani Express)\n"
        f"- Expected delay: {delay_minutes} minutes\n"
        f"- Route: Mumbai Central to New Delhi\n"
        f"- Severity (internal only, do NOT share with passengers): {state.get('severity', 'warning')}\n\n"
        f"Generate three versions:\n"
        f"1. SMS message (max 160 chars if possible, otherwise keep brief)\n"
        f"2. Station PA announcement\n"
        f"3. App push notification (title + body)\n\n"
        f"Keep messaging calm and reassuring. Include helpline 139."
    )

    messages = [{"role": "user", "content": user_message}]

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages,
    )

    final_text = ""
    for block in response.content:
        if hasattr(block, "text"):
            final_text += block.text

    state["passenger_notifications"] = {"raw": final_text}
    state["audit_entries"] = state.get("audit_entries", [])
    state["audit_entries"].append({
        "agent": "passenger_comms",
        "action": "notifications_generated",
        "reasoning": f"Passenger notifications generated for train {state.get('train_number', '12951')}.",
        "confidence": 0.96,
        "timestamp": now,
    })
    return state
