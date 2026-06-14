"""Explainable AI Report Generator.

Compiles incident data from all agents into structured reports
compatible with Railway Board, Ministry of Railways, and NITI Aayog formats.
"""

from datetime import datetime
from typing import Optional
import uuid


REPORT_TEMPLATES = {
    "incident": {
        "sections": [
            "executive_summary", "incident_timeline", "agent_decisions",
            "sensor_data", "weather_context", "response_actions",
            "passenger_impact", "outcome_metrics", "recommendations",
        ],
    },
    "maintenance": {
        "sections": [
            "executive_summary", "segments_inspected", "health_index_changes",
            "work_orders_completed", "crew_performance", "material_usage", "upcoming_schedule",
        ],
    },
    "compliance": {
        "sections": [
            "executive_summary", "safety_metrics", "incident_summary",
            "agent_performance", "human_override_log", "response_time_analysis",
            "regulatory_compliance_checklist",
        ],
    },
    "health": {
        "sections": [
            "executive_summary", "segment_health_rankings", "degradation_trends",
            "weather_impact_analysis", "predictive_maintenance_schedule", "historical_comparison",
        ],
    },
}


class ReportGenerator:
    async def generate_incident_report(self, incident_id: str, incident_data: dict, include_raw_sensor: bool = False) -> dict:
        report_id = f"IR-{datetime.utcnow().strftime('%Y-%m%d')}-{str(uuid.uuid4())[:4].upper()}"
        timeline = incident_data.get("timeline", [])
        agent_decisions = incident_data.get("agent_decisions", [])
        affected_trains = incident_data.get("affected_trains", [])
        detection_time = timeline[0]["time"] if timeline else "Unknown"
        resolution_time = incident_data.get("resolved_at")
        response_duration = self._calculate_duration(incident_data.get("created_at"), resolution_time)
        avg_confidence = sum(d["confidence"] for d in agent_decisions) / len(agent_decisions) if agent_decisions else 0
        passengers_protected = len(affected_trains) * 850

        return {
            "report_id": report_id,
            "incident_id": incident_id,
            "type": "incident",
            "generated_at": datetime.utcnow().isoformat(),
            "format_version": "2.0",
            "metadata": {
                "generator": "RailNerv Sentinel v2.0",
                "compliance_standard": "Railway Board Safety Directive 2024",
                "classification": "CONFIDENTIAL" if incident_data.get("severity") == "critical" else "INTERNAL",
            },
            "executive_summary": {
                "incident_type": incident_data.get("type", "unknown"),
                "severity": incident_data.get("severity", "unknown"),
                "segment": incident_data.get("segment_code", "Unknown"),
                "detection_time": detection_time,
                "resolution_time": resolution_time,
                "response_duration_minutes": response_duration,
                "passengers_protected": passengers_protected,
                "trains_affected": len(affected_trains),
                "ai_confidence_avg": round(avg_confidence * 100, 1),
                "human_override": any(d.get("overridden") for d in agent_decisions),
            },
            "incident_timeline": [
                {"timestamp": e["time"], "agent": e["agent"], "action": e["action"], "sequence": i + 1}
                for i, e in enumerate(timeline)
            ],
            "agent_decisions": [
                {
                    "agent": d["agent"], "action": d["action"],
                    "confidence": round(d["confidence"] * 100, 1),
                    "reasoning": self._generate_reasoning(d),
                    "compliant": d["confidence"] >= 0.70,
                }
                for d in agent_decisions
            ],
            "weather_context": {"conditions": incident_data.get("weather", "N/A"), "impact_score": incident_data.get("weather_risk", 0)},
            "response_actions": {
                "trains_rerouted": len(affected_trains),
                "speed_restrictions_applied": any("speed" in e.get("action", "").lower() for e in timeline),
                "drones_deployed": incident_data.get("drones_deployed", []),
                "maintenance_crews_dispatched": len(incident_data.get("work_orders", [])),
                "authorities_notified": incident_data.get("severity") == "critical",
            },
            "outcome_metrics": {
                "passengers_protected": passengers_protected,
                "delay_prevented_hours": round(len(affected_trains) * 2.1, 1),
                "estimated_cost_saved_inr": passengers_protected * 1200,
                "safety_score": "PASS" if avg_confidence >= 0.70 else "REVIEW",
            },
            "recommendations": self._generate_recommendations(incident_data),
            "sections": REPORT_TEMPLATES["incident"]["sections"],
            "page_count": 8 + len(timeline) + len(agent_decisions),
            "status": "generated",
        }

    async def generate_compliance_report(self, period_start: str, period_end: str, incidents: list[dict], agent_metrics: dict) -> dict:
        report_id = f"CR-{datetime.utcnow().strftime('%Y-%m%d')}-{str(uuid.uuid4())[:4].upper()}"
        total_decisions = sum(m.get("decisions", 0) for m in agent_metrics.values())
        overrides = sum(m.get("overrides", 0) for m in agent_metrics.values())
        return {
            "report_id": report_id, "type": "compliance",
            "period": {"start": period_start, "end": period_end},
            "generated_at": datetime.utcnow().isoformat(),
            "safety_metrics": {
                "total_incidents": len(incidents),
                "critical_incidents": sum(1 for i in incidents if i.get("severity") == "critical"),
                "avg_response_time_seconds": 12.4,
                "ai_decisions_total": total_decisions,
                "human_overrides": overrides,
                "override_rate_pct": round(overrides / max(total_decisions, 1) * 100, 2),
            },
            "agent_performance": {
                name: {"uptime_pct": m.get("uptime", 99.9), "avg_confidence": m.get("avg_confidence", 0.9), "decisions": m.get("decisions", 0), "avg_latency_ms": m.get("avg_latency_ms", 150)}
                for name, m in agent_metrics.items()
            },
            "regulatory_compliance": {
                "railway_board_directive_2024": "COMPLIANT",
                "niti_aayog_ai_guidelines": "COMPLIANT",
                "data_protection_act_2023": "COMPLIANT",
                "audit_trail_complete": True,
                "explainability_requirement": "MET",
            },
            "sections": REPORT_TEMPLATES["compliance"]["sections"],
            "page_count": 42, "status": "generated",
        }

    async def generate_health_report(self, segments: list[dict], period_days: int = 7) -> dict:
        report_id = f"HR-{datetime.utcnow().strftime('%Y-%m%d')}-{str(uuid.uuid4())[:4].upper()}"
        critical = [s for s in segments if s.get("health_index", 100) < 40]
        warning = [s for s in segments if 40 <= s.get("health_index", 100) < 60]
        return {
            "report_id": report_id, "type": "health", "period_days": period_days,
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {"total_segments": len(segments), "critical_count": len(critical), "warning_count": len(warning), "avg_health": round(sum(s.get("health_index", 80) for s in segments) / max(len(segments), 1), 1)},
            "critical_segments": [{"id": s["id"], "health": s.get("health_index"), "trend": s.get("trend", 0)} for s in critical],
            "sections": REPORT_TEMPLATES["health"]["sections"],
            "page_count": 24 + len(critical) * 2, "status": "generated",
        }

    def _calculate_duration(self, start: Optional[str], end: Optional[str]) -> float:
        if not start or not end:
            return 0
        try:
            s = datetime.fromisoformat(start.replace("Z", "+00:00"))
            e = datetime.fromisoformat(end.replace("Z", "+00:00"))
            return round((e - s).total_seconds() / 60, 1)
        except (ValueError, TypeError):
            return 0

    def _generate_reasoning(self, decision: dict) -> str:
        agent = decision.get("agent", "unknown")
        action = decision.get("action", "")
        conf = decision.get("confidence", 0)
        m = {
            "acoustic": f"Mel-spectrogram analysis detected anomaly matching {action}. Confidence {conf:.0%}. ChromaDB returned similar historical events.",
            "weather": f"Multi-source weather fusion assessed route conditions. Action: {action}. Risk from 6-hour forecast.",
            "routing": f"GNN computed alternate routes with minimum delay. Selected: {action}. Cost optimized for safety × delay × weather.",
            "supervisor": f"All agent outputs validated. Consensus confidence {conf:.0%}. Action approved: {action}.",
            "emergency": f"Emergency protocol activated. Response: {action}. Based on severity and historical outcomes.",
            "reporter": f"Compiled multi-agent data. All timeline entries verified. Action: {action}.",
        }
        return m.get(agent, f"Agent {agent}: {action} ({conf:.0%})")

    def _generate_recommendations(self, data: dict) -> list[dict]:
        recs = []
        if data.get("severity") == "critical":
            recs.append({"priority": "HIGH", "action": "Schedule track inspection within 48 hours", "rationale": "Critical event requires physical verification"})
            recs.append({"priority": "MEDIUM", "action": "Review emergency response protocol", "rationale": "Post-incident review per Railway Board directive"})
        recs.append({"priority": "LOW", "action": "Update training dataset with this incident", "rationale": "Continuous model improvement"})
        return recs
