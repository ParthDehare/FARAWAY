"use client";

import { motion } from "framer-motion";
import { useAgentStore } from "@/stores/agentStore";
import { Activity, CloudRain, Route, AlertTriangle, FileText, Shield, Download } from "lucide-react";

const spring = { type: "spring" as const, stiffness: 300, damping: 30 };

const AGENT_ICONS: Record<string, React.ElementType> = {
  acoustic_monitor: Activity,
  weather_agent: CloudRain,
  routing_coordinator: Route,
  emergency_agent: AlertTriangle,
  incident_reporter: FileText,
  supervisor_agent: Shield,
};

const AGENT_COLORS: Record<string, string> = {
  acoustic_monitor: "#30d158",
  weather_agent: "#0a84ff",
  routing_coordinator: "#ffd60a",
  emergency_agent: "#ff453a",
  incident_reporter: "#bf5af2",
  supervisor_agent: "#5e5ce6",
};

const MOCK_ENTRIES = [
  { id: "1", agentId: "acoustic_monitor" as const, action: "Classified: Heavy Obstruction — 97.3%", reasoning: "Mel-spectrogram 14.2kHz spike matches OBSTRUCTION pattern", confidence: 97.3, severity: "critical" as const, timestamp: "2026-06-11T13:55:10Z" },
  { id: "2", agentId: "weather_agent" as const, action: "Alternate route rain risk assessed at 80%", reasoning: "OpenWeatherMap + ISRO satellite confirms cloud formation over Nashik corridor", confidence: 94.1, severity: "warning" as const, timestamp: "2026-06-11T13:55:12Z" },
  { id: "3", agentId: "routing_coordinator" as const, action: "Rerouting 6 trains via Jaipur corridor", reasoning: "GNN cost: Jaipur 0.42 vs Nashik 0.78. Lowest delay 22min avg", confidence: 91.8, severity: "info" as const, timestamp: "2026-06-11T13:55:14Z" },
  { id: "4", agentId: "emergency_agent" as const, action: "UAV-B4 dispatched to KM-402", reasoning: "Protocol E-7. Visual confirmation required. ETA 4m32s", confidence: 99.2, severity: "critical" as const, timestamp: "2026-06-11T13:55:15Z" },
  { id: "5", agentId: "supervisor_agent" as const, action: "All actions approved. No escalation required.", reasoning: "All agent confidence >70%. No conflicts. Consensus confirmed.", confidence: 96.7, severity: "info" as const, timestamp: "2026-06-11T13:55:16Z" },
  { id: "6", agentId: "incident_reporter" as const, action: "Generated report IR-2026-0611-003", reasoning: "Compiled 5-agent data. 1,247 passengers protected.", confidence: 88.5, severity: "info" as const, timestamp: "2026-06-11T14:02:33Z" },
];

interface AuditTrailPanelProps {
  maxItems?: number;
  compact?: boolean;
}

export function AuditTrailPanel({ maxItems = 20, compact = false }: AuditTrailPanelProps) {
  const { decisions } = useAgentStore();
  const entries = decisions.length > 0 ? decisions.slice(0, maxItems) : MOCK_ENTRIES.slice(0, maxItems);

  return (
    <div>
      {entries.map((entry, i) => {
        const Icon = AGENT_ICONS[entry.agentId] || Activity;
        const color = AGENT_COLORS[entry.agentId] || "#0a84ff";

        return (
          <motion.div
            key={entry.id}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.04, ...spring }}
            className="flex items-start gap-3 px-4 py-3 transition-colors hover:bg-white/[0.02]"
          >
            <div className="flex flex-col items-center shrink-0 mt-0.5">
              <div className="flex h-6 w-6 items-center justify-center rounded-full" style={{ backgroundColor: `${color}15` }}>
                <Icon className="h-3 w-3" style={{ color }} />
              </div>
              {i < entries.length - 1 && <div className="my-0.5 h-8 w-px bg-white/[0.04]" />}
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-medium text-white/50">{entry.action}</span>
                <span className={`flex h-[14px] items-center rounded-full px-1.5 text-[8px] font-medium ${
                  entry.severity === "critical"
                    ? "bg-[#ff453a]/10 text-[#ff453a]/70"
                    : entry.severity === "warning"
                    ? "bg-[#ffd60a]/10 text-[#ffd60a]/70"
                    : "bg-white/[0.04] text-white/25"
                }`}>
                  {entry.confidence}%
                </span>
              </div>
              {!compact && "reasoning" in entry && (
                <p className="mt-0.5 text-[10px] text-white/20 line-clamp-1">{(entry as typeof MOCK_ENTRIES[0]).reasoning}</p>
              )}
            </div>

            <span className="font-mono text-[9px] text-white/15 shrink-0">
              {new Date(entry.timestamp).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false })}
            </span>
          </motion.div>
        );
      })}
    </div>
  );
}
