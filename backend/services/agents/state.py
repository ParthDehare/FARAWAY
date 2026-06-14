"""LangGraph shared state for the RailNerv 6-agent orchestration pipeline."""

from typing import TypedDict, Optional, List


class RailNervState(TypedDict):
    incident_id: str
    segment_id: str
    anomaly_class: str  # NORMAL | FLAT_WHEEL | MICRO_CRACK | OBSTRUCTION
    confidence: float
    weather_risk: Optional[dict]  # {level, conditions, forecast}
    affected_trains: List[dict]  # [{train_number, name, passenger_count}]
    reroute_proposal: Optional[dict]  # {original_path, new_path, delay_minutes}
    emergency_protocol: Optional[dict]  # {level, actions, authorities_notified}
    crew_dispatch: Optional[dict]  # {crew_id, eta_hours, skills}
    passenger_notification: Optional[dict]  # {message, affected_count, channels}
    audit_entries: List[dict]  # [{agent, action, reasoning, confidence, timestamp}]
    human_override: Optional[dict]
    resolution: Optional[dict]
    severity: str  # info | warning | critical
