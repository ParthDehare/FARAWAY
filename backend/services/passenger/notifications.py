"""Passenger Safety Shield — Push Notification Service.

Real-time push notifications to passengers aboard affected trains via PWA.
Provides: current status, estimated delay, alternate station options, emergency contacts.
"""

from datetime import datetime
from typing import Optional
import uuid


class PassengerNotificationService:
    def __init__(self):
        self._subscriptions: dict[str, dict] = {}
        self._sent_notifications: list[dict] = []

    async def register_subscription(self, train_number: str, push_subscription: dict) -> dict:
        sub_id = str(uuid.uuid4())
        self._subscriptions[sub_id] = {
            "id": sub_id,
            "train_number": train_number,
            "subscription": push_subscription,
            "registered_at": datetime.utcnow().isoformat(),
            "active": True,
        }
        return {"subscription_id": sub_id, "status": "registered"}

    async def send_alert(self, train_numbers: list[str], alert: dict) -> dict:
        affected_subs = [
            s for s in self._subscriptions.values()
            if s["train_number"] in train_numbers and s["active"]
        ]

        notification = {
            "id": str(uuid.uuid4()),
            "type": alert.get("type", "disruption"),
            "severity": alert.get("severity", "warning"),
            "title": alert.get("title", "Service Update"),
            "body": alert.get("body", ""),
            "data": {
                "affected_trains": train_numbers,
                "estimated_delay_minutes": alert.get("delay_minutes"),
                "alternate_stations": alert.get("alternates", []),
                "emergency_contacts": {
                    "railway_helpline": "139",
                    "emergency": "112",
                    "women_helpline": "182",
                },
                "action_url": alert.get("action_url"),
            },
            "sent_at": datetime.utcnow().isoformat(),
            "recipients": len(affected_subs),
        }

        self._sent_notifications.append(notification)
        return notification

    async def send_reroute_notification(self, train_number: str, new_route: str, delay_minutes: int, alternate_stations: list[str]) -> dict:
        return await self.send_alert(
            [train_number],
            {
                "type": "reroute",
                "severity": "warning",
                "title": f"Train {train_number} Rerouted",
                "body": f"Your train has been rerouted via {new_route}. Estimated additional delay: {delay_minutes} minutes. Alternate stations: {', '.join(alternate_stations)}",
                "delay_minutes": delay_minutes,
                "alternates": alternate_stations,
            },
        )

    async def send_safety_alert(self, train_numbers: list[str], incident_type: str, instructions: str) -> dict:
        return await self.send_alert(
            train_numbers,
            {
                "type": "safety",
                "severity": "critical",
                "title": f"Safety Alert — {incident_type.replace('_', ' ').title()}",
                "body": instructions,
            },
        )

    async def send_resolution(self, train_numbers: list[str], message: str) -> dict:
        return await self.send_alert(
            train_numbers,
            {
                "type": "resolution",
                "severity": "info",
                "title": "Service Restored",
                "body": message,
            },
        )

    async def get_notification_history(self, limit: int = 20) -> list[dict]:
        return sorted(self._sent_notifications, key=lambda n: n["sent_at"], reverse=True)[:limit]

    async def get_stats(self) -> dict:
        return {
            "total_subscriptions": len(self._subscriptions),
            "active_subscriptions": sum(1 for s in self._subscriptions.values() if s["active"]),
            "notifications_sent_today": len(self._sent_notifications),
            "by_severity": {
                sev: sum(1 for n in self._sent_notifications if n["severity"] == sev)
                for sev in ["critical", "warning", "info"]
            },
        }
