"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Brain,
  Activity,
  CloudRain,
  Route,
  AlertTriangle,
  FileText,
  Shield,
  Zap,
  ChevronDown,
  ArrowRight,
} from "lucide-react";
import { useAgents } from "@/lib/queries";

const spring = { type: "spring" as const, stiffness: 300, damping: 30 };
const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.07, delayChildren: 0.1 } },
};
const fadeUp = {
  hidden: { opacity: 0, y: 20, scale: 0.98 },
  show: { opacity: 1, y: 0, scale: 1, transition: { ...spring, duration: 0.55 } },
};

const agentIconMap: Record<string, { icon: React.ElementType; color: string }> = {
  acoustic: { icon: Activity, color: "#30d158" },
  weather: { icon: CloudRain, color: "#0a84ff" },
  routing: { icon: Route, color: "#ffd60a" },
  emergency: { icon: AlertTriangle, color: "#ff453a" },
  reporter: { icon: FileText, color: "#bf5af2" },
  supervisor: { icon: Shield, color: "#5e5ce6" },
};

export default function AgentBrainPage() {
  const [expanded, setExpanded] = useState<string | null>("acoustic");
  const { data } = useAgents();

  const agentDetails = (data?.agents ?? []).map((a: any) => {
    const cfg = agentIconMap[a.id] || { icon: Zap, color: "#8e8e93" };
    return {
      id: a.id,
      name: a.name,
      icon: cfg.icon,
      color: cfg.color,
      status: a.status,
      uptime: a.uptime_pct ? `${a.uptime_pct}%` : "—",
      avgLatency: a.avg_latency_ms ? `${a.avg_latency_ms}ms` : "—",
      decisionsToday: a.decisions_today ?? 0,
      confidence: a.avg_confidence ? Math.round(a.avg_confidence * 100) : 0,
      lastAction: a.last_action || "—",
      lastActionTime: a.last_active ? new Date(a.last_active).toLocaleTimeString() : "—",
      reasoning: a.reasoning || "Awaiting next decision cycle.",
    };
  });

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-5">
      <motion.div variants={fadeUp} className="flex items-end justify-between">
        <div>
          <h1 className="font-display text-[22px] font-semibold tracking-[-0.02em]">
            Agent Brain
          </h1>
          <p className="mt-0.5 text-[13px] text-white/30">
            6-agent LangGraph orchestration — live status & reasoning
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-full bg-[#30d158]/[0.08] px-3 py-1.5 ring-1 ring-[#30d158]/10">
          <Brain className="h-3.5 w-3.5 text-[#30d158]" />
          <span className="font-mono text-[11px] font-medium text-[#30d158]/80">6/6 Online</span>
        </div>
      </motion.div>

      <motion.div variants={fadeUp} className="glass rounded-2xl overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3">
          <span className="text-[13px] font-medium text-white/60">LangGraph Agent Flow</span>
          <div className="flex items-center gap-1.5">
            <Zap className="h-3 w-3 text-[#0a84ff]" />
            <span className="font-mono text-[10px] text-white/20">Active Pipeline</span>
          </div>
        </div>
        <div className="divider" />
        <div className="flex items-center justify-center gap-2 overflow-x-auto px-5 py-6">
          {agentDetails.map((agent, i) => (
            <div key={agent.id} className="flex items-center gap-2">
              <motion.div
                whileHover={{ scale: 1.06, transition: spring }}
                whileTap={{ scale: 0.97 }}
                onClick={() => setExpanded(expanded === agent.id ? null : agent.id)}
                className={`flex cursor-pointer flex-col items-center gap-1.5 rounded-xl p-3.5 transition-all duration-300 ring-1 ${
                  expanded === agent.id
                    ? "bg-white/[0.05] ring-white/[0.08]"
                    : "bg-white/[0.02] ring-white/[0.03] hover:bg-white/[0.04] hover:ring-white/[0.06]"
                }`}
                style={{ minWidth: "96px" }}
              >
                <div
                  className="flex h-9 w-9 items-center justify-center rounded-[10px]"
                  style={{ backgroundColor: `${agent.color}12` }}
                >
                  <agent.icon className="h-[15px] w-[15px]" style={{ color: agent.color }} />
                </div>
                <span className="text-[10px] font-medium text-white/50 text-center">
                  {agent.name.split(" ")[0]}
                </span>
                <span
                  className={`font-mono text-[8px] ${
                    agent.status === "active" ? "text-[#30d158]/60" : "text-[#ffd60a]/60"
                  }`}
                >
                  {agent.status === "active" ? "● Active" : "◐ Standby"}
                </span>
              </motion.div>
              {i < agentDetails.length - 1 && (
                <ArrowRight className="h-3.5 w-3.5 text-white/10 shrink-0" />
              )}
            </div>
          ))}
        </div>
      </motion.div>

      <div className="space-y-2">
        {agentDetails.map((agent, i) => (
          <motion.div
            key={agent.id}
            variants={fadeUp}
            className="glass rounded-2xl overflow-hidden"
          >
            <button
              onClick={() => setExpanded(expanded === agent.id ? null : agent.id)}
              className="flex w-full items-center gap-4 px-5 py-3.5 text-left transition-all duration-300 hover:bg-white/[0.02]"
            >
              <div
                className="flex h-9 w-9 items-center justify-center rounded-[10px] shrink-0"
                style={{ backgroundColor: `${agent.color}12` }}
              >
                <agent.icon className="h-[15px] w-[15px]" style={{ color: agent.color }} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-[13px] font-medium text-white/60">{agent.name}</span>
                  <span
                    className={`pill text-[10px] ring-1 ${
                      agent.status === "active"
                        ? "bg-[#30d158]/[0.08] text-[#30d158]/80 ring-[#30d158]/10"
                        : "bg-[#ffd60a]/[0.08] text-[#ffd60a]/80 ring-[#ffd60a]/10"
                    }`}
                  >
                    {agent.status.toUpperCase()}
                  </span>
                </div>
                <p className="mt-0.5 text-[11px] text-white/25 truncate">{agent.lastAction}</p>
              </div>
              <div className="flex items-center gap-5 shrink-0">
                <div className="text-right">
                  <span className="font-mono text-[13px] font-semibold" style={{ color: agent.color }}>
                    {agent.confidence}%
                  </span>
                  <p className="text-[10px] text-white/20">confidence</p>
                </div>
                <div className="text-right">
                  <span className="font-mono text-[13px] text-white/50">{agent.decisionsToday}</span>
                  <p className="text-[10px] text-white/20">decisions</p>
                </div>
                <ChevronDown
                  className={`h-4 w-4 text-white/20 transition-transform duration-300 ${
                    expanded === agent.id ? "rotate-180" : ""
                  }`}
                />
              </div>
            </button>
            <AnimatePresence>
              {expanded === agent.id && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                  className="overflow-hidden"
                >
                  <div className="divider" />
                  <div className="px-5 py-4 space-y-3">
                    <div className="grid grid-cols-4 gap-2">
                      {[
                        { label: "Uptime", value: agent.uptime },
                        { label: "Avg Latency", value: agent.avgLatency },
                        { label: "Decisions Today", value: agent.decisionsToday.toString() },
                        { label: "Last Action", value: agent.lastActionTime },
                      ].map((m) => (
                        <div
                          key={m.label}
                          className="rounded-xl bg-white/[0.02] px-3 py-2.5 ring-1 ring-white/[0.03]"
                        >
                          <p className="text-[10px] text-white/20">{m.label}</p>
                          <p className="mt-0.5 font-mono text-[13px] font-medium text-white/50">{m.value}</p>
                        </div>
                      ))}
                    </div>
                    <div className="rounded-xl bg-white/[0.02] p-4 ring-1 ring-white/[0.03]">
                      <p className="mb-1.5 text-[10px] font-medium text-[#0a84ff]/70 uppercase tracking-wide">
                        Reasoning Chain
                      </p>
                      <p className="text-[11px] leading-relaxed text-white/30">{agent.reasoning}</p>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
