"use client";

import { motion } from "framer-motion";
import { useAlertStore, type Alert } from "@/stores/alertStore";
import { AlertTriangle, Check, ChevronRight } from "lucide-react";

const spring = { type: "spring" as const, stiffness: 300, damping: 30 };

interface AlertTimelineProps {
  maxItems?: number;
  onSelect?: (alert: Alert) => void;
}

export function AlertTimeline({ maxItems = 20, onSelect }: AlertTimelineProps) {
  const { alerts } = useAlertStore();
  const items = alerts.slice(0, maxItems);

  if (items.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-[12px] text-white/20">No alerts</p>
      </div>
    );
  }

  return (
    <div className="space-y-0">
      {items.map((alert, i) => (
        <motion.button
          key={alert.id}
          initial={{ opacity: 0, x: -12 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.04, ...spring }}
          onClick={() => onSelect?.(alert)}
          className="flex w-full items-center gap-3 px-4 py-3 text-left transition-all duration-300 hover:bg-white/[0.02]"
        >
          <div className="flex flex-col items-center shrink-0">
            <div className={`flex h-6 w-6 items-center justify-center rounded-full ${
              alert.severity === "critical"
                ? "bg-[#ff453a]/10 ring-1 ring-[#ff453a]/10"
                : alert.severity === "warning"
                ? "bg-[#ffd60a]/10 ring-1 ring-[#ffd60a]/10"
                : "bg-[#0a84ff]/10 ring-1 ring-[#0a84ff]/10"
            }`}>
              {alert.acknowledged ? (
                <Check className="h-3 w-3 text-[#30d158]/50" />
              ) : (
                <AlertTriangle className={`h-3 w-3 ${
                  alert.severity === "critical" ? "text-[#ff453a]" : alert.severity === "warning" ? "text-[#ffd60a]" : "text-[#0a84ff]"
                }`} />
              )}
            </div>
            {i < items.length - 1 && <div className="my-0.5 h-6 w-px bg-white/[0.04]" />}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-[12px] font-medium text-white/60 truncate">{alert.title}</span>
              {alert.segmentId && (
                <span className="font-mono text-[9px] text-white/15">{alert.segmentId}</span>
              )}
            </div>
            <p className="mt-0.5 text-[11px] text-white/25 truncate">{alert.description}</p>
          </div>

          <span className="font-mono text-[10px] text-white/15 shrink-0">
            {new Date(alert.timestamp).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false })}
          </span>
          <ChevronRight className="h-3 w-3 text-white/10 shrink-0" />
        </motion.button>
      ))}
    </div>
  );
}
