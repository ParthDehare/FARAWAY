"""Work order management for Indian Railway maintenance."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import uuid4

IST = timezone(timedelta(hours=5, minutes=30))

PRIORITY_LABELS = {
    "P0": "Emergency — immediate action required, potential derailment risk",
    "P1": "Urgent — maintenance within 48 hours, speed restriction in effect",
    "P2": "Scheduled — planned maintenance within 30 days",
}

VALID_STATUSES = ["created", "assigned", "in_progress", "completed", "cancelled"]


@dataclass
class WorkOrder:
    order_id: str
    segment_id: str
    priority: str  # P0, P1, P2
    priority_label: str
    health_index: int
    description: str
    status: str
    assigned_crew: str | None
    created_at: str
    updated_at: str
    history: list[dict] = field(default_factory=list)


class WorkOrderManager:
    """Manages maintenance work orders."""

    def __init__(self):
        self._orders: dict[str, WorkOrder] = {}
        self._seed_demo_orders()

    def _seed_demo_orders(self):
        """Pre-populate with realistic demo work orders."""
        demos = [
            {
                "segment_id": "SEG-HWH-GHY-002",
                "priority": "P0",
                "health_index": 18,
                "description": "Rail fracture detected via acoustic sensor at km 342. NF Railway Lumding-Badarpur hill section. Immediate rail replacement required.",
                "status": "in_progress",
                "crew": "CRW-008",
            },
            {
                "segment_id": "SEG-MUM-GOA-001",
                "priority": "P1",
                "health_index": 42,
                "description": "Ballast degradation on Konkan Railway ghat section. Monsoon waterlogging reported. Speed restriction 45 km/h imposed.",
                "status": "assigned",
                "crew": "CRW-001",
            },
            {
                "segment_id": "SEG-DEL-JAI-001",
                "priority": "P2",
                "health_index": 68,
                "description": "Scheduled rail grinding and weld inspection on Delhi-Jaipur Shatabdi corridor.",
                "status": "created",
                "crew": None,
            },
        ]
        for d in demos:
            wo = WorkOrder(
                order_id=f"WO-{uuid4().hex[:8].upper()}",
                segment_id=d["segment_id"],
                priority=d["priority"],
                priority_label=PRIORITY_LABELS[d["priority"]],
                health_index=d["health_index"],
                description=d["description"],
                status=d["status"],
                assigned_crew=d["crew"],
                created_at=datetime.now(IST).isoformat(),
                updated_at=datetime.now(IST).isoformat(),
                history=[{"status": d["status"], "timestamp": datetime.now(IST).isoformat(), "note": "Seeded for demo"}],
            )
            self._orders[wo.order_id] = wo

    def create_work_order(
        self,
        segment_id: str,
        priority: str,
        health_index: int,
        description: str,
    ) -> WorkOrder:
        """Create a new maintenance work order."""
        if priority not in PRIORITY_LABELS:
            raise ValueError(f"Invalid priority '{priority}'. Must be one of: {list(PRIORITY_LABELS.keys())}")

        now = datetime.now(IST).isoformat()
        wo = WorkOrder(
            order_id=f"WO-{uuid4().hex[:8].upper()}",
            segment_id=segment_id,
            priority=priority,
            priority_label=PRIORITY_LABELS[priority],
            health_index=health_index,
            description=description,
            status="created",
            assigned_crew=None,
            created_at=now,
            updated_at=now,
            history=[{"status": "created", "timestamp": now, "note": "Work order created"}],
        )
        self._orders[wo.order_id] = wo
        return wo

    def get_active_orders(self) -> list[WorkOrder]:
        """List all non-completed, non-cancelled work orders, sorted by priority."""
        priority_sort = {"P0": 0, "P1": 1, "P2": 2}
        active = [wo for wo in self._orders.values() if wo.status not in ("completed", "cancelled")]
        active.sort(key=lambda w: (priority_sort.get(w.priority, 9), w.created_at))
        return active

    def get_all_orders(self) -> list[WorkOrder]:
        """List all work orders."""
        return list(self._orders.values())

    def get_order(self, order_id: str) -> WorkOrder | None:
        return self._orders.get(order_id)

    def update_order_status(self, order_id: str, status: str, note: str = "") -> WorkOrder | None:
        """Update a work order's status."""
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {VALID_STATUSES}")

        wo = self._orders.get(order_id)
        if wo is None:
            return None

        now = datetime.now(IST).isoformat()
        wo.status = status
        wo.updated_at = now
        wo.history.append({"status": status, "timestamp": now, "note": note or f"Status changed to {status}"})
        return wo

    def assign_crew(self, order_id: str, crew_id: str) -> WorkOrder | None:
        """Assign a crew to a work order."""
        wo = self._orders.get(order_id)
        if wo is None:
            return None

        now = datetime.now(IST).isoformat()
        wo.assigned_crew = crew_id
        wo.status = "assigned"
        wo.updated_at = now
        wo.history.append({"status": "assigned", "timestamp": now, "note": f"Crew {crew_id} assigned"})
        return wo
