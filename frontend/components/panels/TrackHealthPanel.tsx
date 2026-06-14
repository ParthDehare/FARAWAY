"use client";

import { motion } from "framer-motion";
import { HeartPulse, TrendingDown, TrendingUp, Wrench } from "lucide-react";

const spring = { type: "spring" as const, stiffness: 300, damping: 30 };

const SEGMENTS = [
  { id: "KM-402", route: "MUM-DEL", score: 34, status: "critical" as const, trend: -8, weather: "Flood Risk", incidents: 5 },
  { id: "KM-847", route: "CHN-KOL", score: 48, status: "warning" as const, trend: -3, weather: "Heavy Rain", incidents: 3 },
  { id: "KM-215", route: "DEL-JAI", score: 56, status: "warning" as const, trend: -5, weather: "Heat Stress", incidents: 2 },
  { id: "KM-1102", route: "KON-RLY", score: 62, status: "warning" as const, trend: 2, weather: "Clear", incidents: 4 },
  { id: "KM-530", route: "MUM-GOA", score: 78, status: "normal" as const, trend: 1, weather: "Clear", incidents: 1 },
  { id: "KM-298", route: "KOL-GHY", score: 81, status: "normal" as const, trend: 0, weather: "Fog", incidents: 0 },
  { id: "KM-655", route: "BLR-TVC", score: 91, status: "normal" as const, trend: 3, weather: "Clear", incidents: 0 },
];

const statusColor = (s: string) =>
  s === "critical" ? "#ff453a" : s === "warning" ? "#ffd60a" : "#30d158";

interface TrackHealthPanelProps {
  compact?: boolean;
  onDispatch?: (segmentId: string) => void;
}

export function TrackHealthPanel({ compact = false, onDispatch }: TrackHealthPanelProps) {
  const items = compact ? SEGMENTS.slice(0, 4) : SEGMENTS;

  return (
    <div className="space-y-2">
      {items.map((seg, i) => (
        <motion.div
          key={seg.id}
          initial={{ opacity: 0, x: -12 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.05, ...spring }}
          className="flex items-center gap-3 rounded-xl bg-white/[0.02] px-3 py-2.5 ring-1 ring-white/[0.03] transition-colors hover:bg-white/[0.04]"
        >
          <span className="font-mono text-[14px] font-bold tabular-nums w-8 text-center"
            style={{ color: statusColor(seg.status) }}>
            {seg.score}
          </span>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="text-[11px] font-medium text-white/60">{seg.id}</span>
              <span className="font-mono text-[9px] text-white/15">{seg.route}</span>
              {seg.weather !== "Clear" && (
                <span className="rounded-full bg-[#ffd60a]/[0.08] px-1.5 py-0.5 text-[8px] font-medium text-[#ffd60a]/60 ring-1 ring-[#ffd60a]/10">
                  {seg.weather}
                </span>
              )}
            </div>
            <div className="mt-1.5 h-[3px] w-full rounded-full bg-white/[0.04]">
              <motion.div
                className="h-full rounded-full"
                style={{ backgroundColor: statusColor(seg.status) }}
                initial={{ width: 0 }}
                animate={{ width: `${seg.score}%` }}
                transition={{ duration: 1, delay: i * 0.05 + 0.2, ease: [0.16, 1, 0.3, 1] }}
              />
            </div>
          </div>

          <div className="flex items-center gap-1 shrink-0">
            {seg.trend < 0 ? (
              <TrendingDown className="h-3 w-3 text-[#ff453a]/50" />
            ) : (
              <TrendingUp className="h-3 w-3 text-[#30d158]/50" />
            )}
            <span className={`font-mono text-[10px] ${seg.trend < 0 ? "text-[#ff453a]/50" : "text-[#30d158]/50"}`}>
              {seg.trend > 0 ? "+" : ""}{seg.trend}
            </span>
          </div>

          {!compact && seg.status !== "normal" && (
            <button
              onClick={() => onDispatch?.(seg.id)}
              className="rounded-lg bg-[#0a84ff]/10 px-2 py-1 text-[9px] font-medium text-[#0a84ff] ring-1 ring-[#0a84ff]/10 transition-all hover:bg-[#0a84ff]/20 shrink-0"
            >
              <Wrench className="h-3 w-3 inline-block mr-0.5" />
              Dispatch
            </button>
          )}
        </motion.div>
      ))}
    </div>
  );
}
