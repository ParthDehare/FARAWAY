"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useAlertStore, type Alert } from "@/stores/alertStore";
import { AlertTriangle, X, Eye, Clock } from "lucide-react";

const spring = { type: "spring" as const, stiffness: 300, damping: 30 };

export function AlertBanner() {
  const { alerts, acknowledgeAlert, dismissAlert } = useAlertStore();
  const active = alerts.filter((a) => !a.acknowledged);
  const latest = active[0];

  if (!latest) return null;

  const severityStyles = {
    critical: { bg: "bg-[#ff453a]/[0.04]", ring: "ring-[#ff453a]/15", text: "text-[#ff453a]", glow: "glow-red" },
    warning: { bg: "bg-[#ffd60a]/[0.04]", ring: "ring-[#ffd60a]/15", text: "text-[#ffd60a]", glow: "glow-yellow" },
    info: { bg: "bg-[#0a84ff]/[0.04]", ring: "ring-[#0a84ff]/15", text: "text-[#0a84ff]", glow: "glow-blue" },
  };

  const style = severityStyles[latest.severity];

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={latest.id}
        initial={{ y: -16, opacity: 0, scale: 0.98 }}
        animate={{ y: 0, opacity: 1, scale: 1 }}
        exit={{ y: -16, opacity: 0, scale: 0.98 }}
        transition={spring}
        className={`relative overflow-hidden rounded-2xl ${style.bg} p-4 ring-1 ${style.ring} ${style.glow}`}
      >
        <div className="alert-shimmer absolute inset-0 pointer-events-none" />
        <div className="relative flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`flex h-9 w-9 items-center justify-center rounded-xl ${style.bg} animate-breathe`}>
              <AlertTriangle className={`h-4 w-4 ${style.text}`} />
            </div>
            <div>
              <p className="text-[13px] font-semibold tracking-[-0.01em]">
                <span className={style.text}>{latest.severity.toUpperCase()}</span>
                <span className="text-white/20 mx-2">·</span>
                <span className="text-white/60">{latest.title}</span>
              </p>
              <div className="mt-0.5 flex items-center gap-3 text-[10px] text-white/25">
                {latest.segmentId && <span className="font-mono">{latest.segmentId}</span>}
                <span className="flex items-center gap-1"><Clock className="h-2.5 w-2.5" />{new Date(latest.timestamp).toLocaleTimeString()}</span>
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => acknowledgeAlert(latest.id)}
              className={`rounded-lg ${style.bg} px-3 py-1.5 text-[11px] font-medium ${style.text} ring-1 ${style.ring} transition-all hover:brightness-125`}
            >
              Acknowledge
            </button>
            <button
              onClick={() => dismissAlert(latest.id)}
              className="rounded-lg bg-white/[0.04] p-1.5 text-white/30 ring-1 ring-white/[0.04] transition-all hover:bg-white/[0.08]"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
        {active.length > 1 && (
          <p className="mt-2 text-[10px] text-white/20">
            +{active.length - 1} more active alert{active.length > 2 ? "s" : ""}
          </p>
        )}
      </motion.div>
    </AnimatePresence>
  );
}
