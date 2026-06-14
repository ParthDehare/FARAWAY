"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import {
  AlertTriangle, Plane, Shield, Clock, Zap, Volume2,
  ChevronRight, ChevronDown, Eye, Navigation, Check,
} from "lucide-react";
import { useIncident } from "@/lib/queries";
import toast from "react-hot-toast";
import { Modal } from "@/components/ui/Modal";

const spring = { type: "spring" as const, stiffness: 300, damping: 30 };
const fadeUp = {
  hidden: { opacity: 0, y: 20, scale: 0.98 },
  show: { opacity: 1, y: 0, scale: 1, transition: { ...spring, duration: 0.55 } },
};

const gnnNodes = [
  { id: "MUM", x: 80, y: 340 }, { id: "PUN", x: 160, y: 270 },
  { id: "NAS", x: 200, y: 210 }, { id: "BPL", x: 280, y: 150 },
  { id: "AGR", x: 340, y: 110 }, { id: "DEL", x: 380, y: 55 },
  { id: "JAI", x: 260, y: 90 }, { id: "ADI", x: 60, y: 210 },
  { id: "SUR", x: 120, y: 290 },
];
const gnnEdges = [
  { from: "MUM", to: "PUN", s: "normal" }, { from: "PUN", to: "NAS", s: "normal" },
  { from: "NAS", to: "BPL", s: "blocked" }, { from: "BPL", to: "AGR", s: "normal" },
  { from: "AGR", to: "DEL", s: "normal" }, { from: "MUM", to: "SUR", s: "rerouted" },
  { from: "SUR", to: "ADI", s: "rerouted" }, { from: "ADI", to: "JAI", s: "rerouted" },
  { from: "JAI", to: "DEL", s: "rerouted" }, { from: "BPL", to: "JAI", s: "normal" },
];

export default function AlertsPage() {
  const { data: inc1 } = useIncident("IR-2026-0042");
  const { data: inc2 } = useIncident("IR-2026-0041");

  const alerts = [inc1, inc2].filter(Boolean).map((inc: any) => ({
    id: inc.id,
    type: inc.type?.replace(/_/g, ' ').toUpperCase() || "UNKNOWN",
    segment: inc.segment_code || inc.segment || "\u2014",
    confidence: inc.agent_decisions?.[0]?.confidence ?? 90,
    severity: inc.severity || "warning",
    time: inc.created_at?.slice(11, 19) || "\u2014",
    description: inc.description || "\u2014",
    chain: (inc.agent_decisions || []).map((d: any) => ({
      agent: d.agent_name || d.agent || "Agent",
      action: d.action_taken || d.action || "\u2014",
      time: d.created_at?.slice(11, 19) || "\u2014",
    })),
  }));

  const [selected, setSelected] = useState<any>(null);
  const [chainOpen, setChainOpen] = useState(true);
  const [acknowledged, setAcknowledged] = useState<Set<string>>(new Set());
  const [overrideOpen, setOverrideOpen] = useState(false);
  const [deployOpen, setDeployOpen] = useState(false);
  const [overrideReason, setOverrideReason] = useState("");
  const nodeMap = Object.fromEntries(gnnNodes.map((n) => [n.id, n]));

  useEffect(() => {
    if (alerts.length > 0 && !selected) {
      setSelected(alerts[0]);
    }
  }, [alerts.length]);

  if (alerts.length === 0) {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center justify-center h-64">
        <p className="text-[15px] text-white/30">No active alerts</p>
      </motion.div>
    );
  }

  if (!selected) return null;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-5">
      {/* Critical Banner */}
      {selected.severity === "critical" && (
        <motion.div
          initial={{ y: -16, opacity: 0, scale: 0.98 }}
          animate={{ y: 0, opacity: 1, scale: 1 }}
          transition={spring}
          className="relative overflow-hidden rounded-2xl bg-[#ff453a]/[0.04] p-5 ring-1 ring-[#ff453a]/15 glow-red"
        >
          <div className="alert-shimmer absolute inset-0 pointer-events-none" />
          <div className="relative flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#ff453a]/10 animate-breathe">
                <AlertTriangle className="h-5 w-5 text-[#ff453a]" />
              </div>
              <div>
                <p className="text-[15px] font-semibold tracking-[-0.01em]">
                  <span className="text-[#ff453a]">CRITICAL</span>
                  <span className="text-white/30 mx-2">·</span>
                  Obstruction Detected — {selected.segment}
                </p>
                <div className="mt-1 flex items-center gap-4 text-[11px] text-white/25">
                  <span className="flex items-center gap-1"><Eye className="h-3 w-3" />{selected.confidence}% confidence</span>
                  <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{selected.time} IST</span>
                  <span className="flex items-center gap-1"><Volume2 className="h-3 w-3" />Voice alert active</span>
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => { setAcknowledged(prev => new Set(prev).add(selected.id)); toast.success(`Alert ${selected.id} acknowledged`); }}
                disabled={acknowledged.has(selected.id)}
                className={`rounded-xl bg-[#ff453a]/10 px-4 py-2 text-[12px] font-medium text-[#ff453a] ring-1 ring-[#ff453a]/10 transition-all hover:bg-[#ff453a]/20 ${acknowledged.has(selected.id) ? "opacity-40 pointer-events-none" : ""}`}>
                {acknowledged.has(selected.id) ? "\u2713 Acknowledged" : "Acknowledge"}
              </button>
              <button onClick={() => setOverrideOpen(true)} className="rounded-xl bg-white/[0.04] px-4 py-2 text-[12px] font-medium text-white/50 ring-1 ring-white/[0.04] transition-all hover:bg-white/[0.08]">
                Override
              </button>
            </div>
          </div>
        </motion.div>
      )}

      <div className="grid grid-cols-12 gap-3">
        {/* GNN Visualization */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1, ...spring }} className="col-span-8 glass rounded-2xl overflow-hidden">
          <div className="flex items-center justify-between px-5 py-3">
            <span className="text-[13px] font-medium text-white/60">GNN Rerouting</span>
            <div className="flex items-center gap-4">
              {[
                { label: "Normal", color: "#5e5ce6" },
                { label: "Blocked", color: "#ff453a" },
                { label: "Rerouted", color: "#0a84ff" },
              ].map((l) => (
                <div key={l.label} className="flex items-center gap-1.5">
                  <span className="h-[6px] w-[6px] rounded-full" style={{ backgroundColor: l.color }} />
                  <span className="text-[10px] text-white/20">{l.label}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="divider" />
          <div className="relative h-[400px] bg-[#0c0c0e]">
            <svg viewBox="0 0 460 400" className="h-full w-full">
              {gnnEdges.map((e, i) => {
                const from = nodeMap[e.from], to = nodeMap[e.to];
                const color = e.s === "blocked" ? "#ff453a" : e.s === "rerouted" ? "#0a84ff" : "#5e5ce6";
                return (
                  <g key={i}>
                    <motion.line x1={from.x} y1={from.y} x2={to.x} y2={to.y}
                      stroke={color} strokeWidth={e.s === "blocked" ? 2.5 : e.s === "rerouted" ? 2 : 1}
                      strokeDasharray={e.s === "blocked" ? "6,4" : "none"}
                      opacity={e.s === "normal" ? 0.15 : 0.5}
                      initial={{ pathLength: 0 }} animate={{ pathLength: 1 }}
                      transition={{ duration: 1, delay: i * 0.08 }}
                    />
                    {e.s === "rerouted" && (
                      <motion.circle r="3" fill="#0a84ff"
                        animate={{ cx: [from.x, to.x], cy: [from.y, to.y], opacity: [0, 0.8, 0] }}
                        transition={{ duration: 2.5, repeat: Infinity, delay: i * 0.3 }}
                      />
                    )}
                  </g>
                );
              })}
              {gnnNodes.map((n) => (
                <g key={n.id}>
                  <circle cx={n.x} cy={n.y} r="18" fill="#1c1c1e" stroke="rgba(255,255,255,0.06)" strokeWidth="1" />
                  <text x={n.x} y={n.y + 1} textAnchor="middle" dominantBaseline="middle"
                    className="fill-white/50 font-mono text-[8px] font-semibold">{n.id}</text>
                </g>
              ))}
            </svg>
          </div>
        </motion.div>

        {/* Right: UAV + Actions */}
        <div className="col-span-4 space-y-3">
          <motion.div initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2, ...spring }} className="glass rounded-2xl p-4">
            <span className="text-[13px] font-medium text-white/60">Deploy UAV</span>
            <div className="mt-3 space-y-1.5">
              {[
                { l: "UAV", v: "Sentinel-B4" }, { l: "Status", v: "● Ready", c: "text-[#30d158]/70" },
                { l: "ETA", v: "4m 32s" }, { l: "Battery", v: "94%", c: "text-[#30d158]/70" },
              ].map((r) => (
                <div key={r.l} className="flex items-center justify-between rounded-xl bg-white/[0.02] px-3.5 py-2.5 ring-1 ring-white/[0.03]">
                  <span className="text-[11px] text-white/25">{r.l}</span>
                  <span className={`font-mono text-[12px] font-medium ${r.c || "text-white/60"}`}>{r.v}</span>
                </div>
              ))}
              <button onClick={() => setDeployOpen(true)} className="mt-2 w-full rounded-xl bg-[#0a84ff] py-2.5 text-[13px] font-semibold text-white transition-all hover:bg-[#0a84ff]/80 active:scale-[0.98]">
                Deploy UAV
              </button>
            </div>
          </motion.div>

          <motion.div initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3, ...spring }} className="glass rounded-2xl p-4">
            <span className="text-[13px] font-medium text-white/60">Actions Taken</span>
            <div className="mt-3 space-y-1.5">
              {["Emergency services notified", "Speed restriction KM-398-406", "Passenger advisory issued", "Maintenance crew dispatched"].map((a, i) => (
                <div key={i} className="flex items-center gap-2.5 rounded-xl bg-white/[0.02] px-3 py-2.5 ring-1 ring-white/[0.03]">
                  <Check className="h-3.5 w-3.5 text-[#30d158]/50 shrink-0" />
                  <span className="text-[11px] text-white/40">{a}</span>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>

      {/* Reasoning Chain */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4, ...spring }} className="glass rounded-2xl overflow-hidden">
        <button onClick={() => setChainOpen(!chainOpen)} className="flex w-full items-center justify-between px-5 py-3.5">
          <span className="text-[13px] font-medium text-white/60">Agent Reasoning Chain</span>
          <ChevronDown className={`h-4 w-4 text-white/20 transition-transform duration-300 ${chainOpen ? "rotate-180" : ""}`} />
        </button>
        <AnimatePresence>
          {chainOpen && (
            <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}>
              <div className="divider" />
              <div className="p-5 space-y-0">
                {selected.chain.map((step: any, i: number) => (
                  <motion.div key={i} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.1, ...spring }}
                    className="flex items-start gap-4 relative">
                    <div className="flex flex-col items-center">
                      <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[#0a84ff]/10 ring-1 ring-[#0a84ff]/10">
                        <span className="font-mono text-[10px] font-bold text-[#0a84ff]/70">{i + 1}</span>
                      </div>
                      {i < selected.chain.length - 1 && <div className="my-1 h-8 w-px bg-white/[0.04]" />}
                    </div>
                    <div className="flex-1 pb-4">
                      <div className="flex items-center gap-2">
                        <span className="text-[12px] font-medium text-white/60">{step.agent}</span>
                        <span className="font-mono text-[10px] text-white/15">{step.time}</span>
                      </div>
                      <p className="mt-0.5 text-[12px] text-white/30">{step.action}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Alert List */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5, ...spring }} className="glass rounded-2xl overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3">
          <span className="text-[13px] font-medium text-white/60">All Active Alerts</span>
          <span className="pill bg-[#ff453a]/[0.08] text-[#ff453a]/60 ring-1 ring-[#ff453a]/10 text-[10px]">{alerts.length} Active</span>
        </div>
        <div className="divider" />
        {alerts.map((a) => (
          <button key={a.id} onClick={() => setSelected(a)}
            className={`flex w-full items-center gap-4 px-5 py-3.5 text-left transition-all duration-300 hover:bg-white/[0.02] ${selected.id === a.id ? "bg-white/[0.03]" : ""}`}>
            <span className={`h-[7px] w-[7px] rounded-full ${a.severity === "critical" ? "bg-[#ff453a] shadow-[0_0_8px_rgba(255,69,58,0.4)]" : "bg-[#ffd60a]"}`} />
            <div className="flex-1 min-w-0">
              <span className="text-[12px] font-medium text-white/60">{a.type}</span>
              <span className="ml-2 font-mono text-[10px] text-white/15">{a.segment}</span>
              <p className="mt-0.5 text-[11px] text-white/20 line-clamp-1">{a.description}</p>
            </div>
            <span className="font-mono text-[11px] text-white/20">{a.confidence}%</span>
            <ChevronRight className="h-3.5 w-3.5 text-white/10" />
          </button>
        ))}
      </motion.div>
      <Modal open={overrideOpen} onOpenChange={setOverrideOpen} title="Override Alert">
        <div className="space-y-4">
          <div className="rounded-xl bg-[#ff453a]/[0.06] p-3 ring-1 ring-[#ff453a]/10">
            <p className="text-[12px] text-[#ff453a]/70">Warning: This will override the AI decision and log to audit trail.</p>
          </div>
          <div>
            <label className="text-[11px] text-white/25 uppercase">Reason</label>
            <textarea value={overrideReason} onChange={(e) => setOverrideReason(e.target.value)} className="mt-1 w-full rounded-xl bg-white/[0.04] px-3 py-2.5 text-[13px] text-white/50 ring-1 ring-white/[0.04] focus:outline-none focus:ring-[#0a84ff]/40 resize-none h-20" placeholder="Enter override reason..." />
          </div>
          <button onClick={() => { if (!overrideReason.trim()) { toast.error("Please enter a reason for override"); return; } setOverrideOpen(false); toast("Alert overridden — logged to audit", { icon: "\u26A0\uFE0F" }); setOverrideReason(""); }}
            className="w-full rounded-xl bg-[#ff453a] py-2.5 text-[13px] font-semibold text-white hover:bg-[#ff453a]/80 transition-colors">
            Confirm Override
          </button>
        </div>
      </Modal>

      <Modal open={deployOpen} onOpenChange={setDeployOpen} title="Deploy UAV">
        <div className="space-y-4">
          <div className="space-y-2">
            {[{ l: "UAV", v: "Sentinel-B4" }, { l: "Battery", v: "94%" }, { l: "ETA to target", v: "4m 32s" }, { l: "Target", v: selected.segment }].map((r) => (
              <div key={r.l} className="flex items-center justify-between rounded-xl bg-white/[0.02] px-3.5 py-2.5 ring-1 ring-white/[0.03]">
                <span className="text-[11px] text-white/25">{r.l}</span>
                <span className="font-mono text-[12px] text-white/60">{r.v}</span>
              </div>
            ))}
          </div>
          <button onClick={() => { setDeployOpen(false); toast.success(`UAV Sentinel-B4 deployed to ${selected.segment}`); }}
            className="w-full rounded-xl bg-[#0a84ff] py-2.5 text-[13px] font-semibold text-white hover:bg-[#0a84ff]/80 transition-colors">
            Confirm Deployment
          </button>
        </div>
      </Modal>
    </motion.div>
  );
}
