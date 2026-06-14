"use client";

import { motion } from "framer-motion";
import { Wrench, Clock, User, MapPin, CheckCircle } from "lucide-react";

const spring = { type: "spring" as const, stiffness: 300, damping: 30 };

const WORK_ORDERS = [
  { id: "WO-001", segment: "KM-402", priority: "P0" as const, status: "dispatched" as const, crew: "Team Alpha-3", eta: "45m", health: 34 },
  { id: "WO-002", segment: "KM-847", priority: "P1" as const, status: "in_progress" as const, crew: "Team Beta-1", eta: "2h 10m", health: 48 },
  { id: "WO-003", segment: "KM-215", priority: "P1" as const, status: "pending" as const, crew: "Unassigned", eta: "—", health: 56 },
  { id: "WO-004", segment: "KM-1102", priority: "P2" as const, status: "complete" as const, crew: "Team Gamma-2", eta: "Done", health: 62 },
];

const priorityColors = { P0: "#ff453a", P1: "#ffd60a", P2: "#0a84ff" };
const statusLabels = { pending: "Pending", dispatched: "Dispatched", in_progress: "In Progress", complete: "Complete" };

interface MaintenancePanelProps {
  compact?: boolean;
}

export function MaintenancePanel({ compact = false }: MaintenancePanelProps) {
  const items = compact ? WORK_ORDERS.slice(0, 3) : WORK_ORDERS;

  return (
    <div className="space-y-2">
      {items.map((wo, i) => (
        <motion.div
          key={wo.id}
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.05, ...spring }}
          className="rounded-xl bg-white/[0.02] p-3 ring-1 ring-white/[0.03] transition-colors hover:bg-white/[0.04]"
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded-md"
                style={{ backgroundColor: `${priorityColors[wo.priority]}15`, color: priorityColors[wo.priority] }}>
                {wo.priority}
              </span>
              <span className="font-mono text-[11px] font-medium text-white/50">{wo.id}</span>
            </div>
            <span className={`text-[9px] font-medium ${
              wo.status === "complete" ? "text-[#30d158]/60"
                : wo.status === "in_progress" ? "text-[#0a84ff]/60"
                : wo.status === "dispatched" ? "text-[#ffd60a]/60"
                : "text-white/25"
            }`}>
              {wo.status === "complete" && <CheckCircle className="h-3 w-3 inline mr-0.5" />}
              {statusLabels[wo.status]}
            </span>
          </div>

          <div className="space-y-1">
            <div className="flex items-center gap-2 text-[10px] text-white/25">
              <MapPin className="h-3 w-3" />
              <span>Segment: {wo.segment}</span>
              <span className="font-mono text-white/15">Health: {wo.health}</span>
            </div>
            <div className="flex items-center gap-2 text-[10px] text-white/25">
              <User className="h-3 w-3" />
              <span>{wo.crew}</span>
            </div>
            <div className="flex items-center gap-2 text-[10px] text-white/25">
              <Clock className="h-3 w-3" />
              <span>ETA: {wo.eta}</span>
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}
