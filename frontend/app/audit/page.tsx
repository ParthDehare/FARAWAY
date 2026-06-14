"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { useAuditLog } from "@/lib/queries";
import toast from "react-hot-toast";
import {
  ScrollText,
  Download,
  Filter,
  ArrowUpRight,
  ArrowDownRight,
  Shield,
  AlertTriangle,
  Target,
  TrendingUp,
} from "lucide-react";

const spring = { type: "spring" as const, stiffness: 300, damping: 30 };
const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.07, delayChildren: 0.1 } },
};
const fadeUp = {
  hidden: { opacity: 0, y: 20, scale: 0.98 },
  show: { opacity: 1, y: 0, scale: 1, transition: { ...spring, duration: 0.55 } },
};

const severityConfig: Record<string, { color: string; bg: string; ring: string; dot: string }> = {
  critical: { color: "text-[#ff453a]", bg: "bg-[#ff453a]/[0.08]", ring: "ring-[#ff453a]/10", dot: "bg-[#ff453a] shadow-[0_0_8px_rgba(255,69,58,0.4)]" },
  warning: { color: "text-[#ffd60a]", bg: "bg-[#ffd60a]/[0.08]", ring: "ring-[#ffd60a]/10", dot: "bg-[#ffd60a]" },
  info: { color: "text-[#0a84ff]", bg: "bg-[#0a84ff]/[0.08]", ring: "ring-[#0a84ff]/10", dot: "bg-[#0a84ff]" },
};

export default function AuditTrailPage() {
  const { data } = useAuditLog();

  const auditEntries = (data?.entries ?? []).map((e: any, i: number) => ({
    id: e.id || `AUD-${i}`,
    time: e.timestamp?.slice(11, 19) || e.time || "—",
    agent: e.agent || e.agent_name || "—",
    action: e.action || e.action_taken || "—",
    confidence: e.confidence ?? 0,
    severity: e.severity || "info",
    overridden: e.human_override ?? e.overridden ?? false,
  }));

  const criticalCount = auditEntries.filter((e: any) => e.severity === "critical").length;
  const overrideCount = auditEntries.filter((e: any) => e.overridden).length;
  const avgConfidence = auditEntries.length > 0 ? (auditEntries.reduce((a: number, e: any) => a + e.confidence, 0) / auditEntries.length).toFixed(1) : "0";

  const stats = [
    { label: "Total Decisions", value: String(auditEntries.length), icon: ScrollText, gradient: "from-[#0a84ff]/10 to-[#5e5ce6]/10", iconColor: "#0a84ff", change: "+84", up: true },
    { label: "Critical", value: String(criticalCount), icon: AlertTriangle, gradient: "from-[#ff453a]/10 to-[#ff6961]/10", iconColor: "#ff453a", change: `${criticalCount} today`, up: false },
    { label: "Overrides", value: String(overrideCount), icon: Shield, gradient: "from-[#ffd60a]/10 to-[#ff9f0a]/10", iconColor: "#ffd60a", change: "Manual", up: false },
    { label: "Avg Confidence", value: `${avgConfidence}%`, icon: TrendingUp, gradient: "from-[#30d158]/10 to-[#34c759]/10", iconColor: "#30d158", change: "+1.2%", up: true },
  ];

  const [filterOpen, setFilterOpen] = useState(false);
  const [severityFilter, setSeverityFilter] = useState<string | null>(null);

  const filteredEntries = severityFilter
    ? auditEntries.filter((e: any) => e.severity === severityFilter)
    : auditEntries;

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-5">
      <motion.div variants={fadeUp} className="flex items-end justify-between">
        <div>
          <h1 className="font-display text-[22px] font-semibold tracking-[-0.02em]">
            Audit Trail
          </h1>
          <p className="mt-0.5 text-[13px] text-white/30">
            Complete decision log — every AI action with reasoning chain
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <button onClick={() => setFilterOpen(!filterOpen)} className="flex items-center gap-1.5 rounded-xl bg-white/[0.04] px-4 py-2.5 text-[13px] text-white/40 ring-1 ring-white/[0.04] transition-all duration-300 hover:bg-white/[0.06] hover:text-white/60">
              <Filter className="h-3.5 w-3.5" />
              {severityFilter ? severityFilter.charAt(0).toUpperCase() + severityFilter.slice(1) : "Filter"}
            </button>
            {filterOpen && (
              <div className="absolute right-0 top-full mt-1 z-20 w-36 rounded-xl bg-[#1c1c1e]/95 p-1.5 ring-1 ring-white/[0.06] backdrop-blur-xl shadow-2xl">
                {[null, "critical", "warning", "info"].map((s) => (
                  <button key={s ?? "all"} onClick={() => { setSeverityFilter(s); setFilterOpen(false); }}
                    className={`w-full rounded-lg px-3 py-2 text-left text-[12px] transition-colors ${severityFilter === s ? "bg-[#0a84ff]/10 text-[#0a84ff]" : "text-white/40 hover:bg-white/[0.04]"}`}>
                    {s ? s.charAt(0).toUpperCase() + s.slice(1) : "All"}
                  </button>
                ))}
              </div>
            )}
          </div>
          <button onClick={() => {
            const headers = "ID,Time,Agent,Action,Confidence,Severity,Overridden";
            const rows = auditEntries.map((e: any) => `${e.id},${e.time},${e.agent},"${e.action}",${e.confidence},${e.severity},${e.overridden}`);
            const csv = [headers, ...rows].join("\n");
            const blob = new Blob([csv], { type: "text/csv" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url; a.download = "railmind-audit-trail.csv"; a.click();
            URL.revokeObjectURL(url);
            toast.success("CSV exported successfully");
          }} className="flex items-center gap-1.5 rounded-xl bg-[#0a84ff] px-4 py-2.5 text-[13px] font-medium text-white transition-all duration-300 hover:bg-[#0a84ff]/80">
            <Download className="h-3.5 w-3.5" />
            Export CSV
          </button>
        </div>
      </motion.div>

      <motion.div variants={fadeUp} className="grid grid-cols-4 gap-3">
        {stats.map((s) => (
          <motion.div
            key={s.label}
            whileHover={{ y: -3, transition: spring }}
            className="glass glass-hover rounded-2xl p-4"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-[11px] font-medium tracking-wide text-white/25 uppercase">
                  {s.label}
                </p>
                <p className="mt-1.5 font-display text-[26px] font-semibold tracking-[-0.03em] text-white">
                  {s.value}
                </p>
                <div className="mt-1 flex items-center gap-1">
                  {s.up ? (
                    <ArrowUpRight className="h-3 w-3 text-[#30d158]" />
                  ) : (
                    <ArrowDownRight className="h-3 w-3 text-[#ff453a]" />
                  )}
                  <span className={`text-[11px] font-medium ${s.up ? "text-[#30d158]/70" : "text-[#ff453a]/70"}`}>
                    {s.change}
                  </span>
                </div>
              </div>
              <div className={`rounded-xl bg-gradient-to-br ${s.gradient} p-2.5`}>
                <s.icon className="h-[18px] w-[18px]" style={{ color: s.iconColor }} />
              </div>
            </div>
          </motion.div>
        ))}
      </motion.div>

      <motion.div variants={fadeUp} className="glass rounded-2xl overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3">
          <span className="text-[13px] font-medium text-white/60">Decision Feed</span>
          <span className="font-mono text-[10px] text-white/15">Last 1 hour</span>
        </div>
        <div className="divider" />
        <div>
          {filteredEntries.map((entry, i) => {
            const sc = severityConfig[entry.severity];
            return (
              <motion.div
                key={entry.id}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + i * 0.06, ...spring }}
                className="flex items-start gap-4 px-5 py-3.5 transition-all duration-300 hover:bg-white/[0.02] cursor-pointer"
              >
                <div className="flex flex-col items-center pt-1 shrink-0">
                  <span className={`h-[6px] w-[6px] rounded-full ${sc.dot}`} />
                  {i < auditEntries.length - 1 && (
                    <div className="mt-1.5 h-8 w-px bg-white/[0.04]" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-mono text-[11px] tabular-nums text-white/20">{entry.time}</span>
                    <span className={`pill text-[10px] ring-1 ${sc.bg} ${sc.color} ${sc.ring}`}>
                      {entry.severity.toUpperCase()}
                    </span>
                    <span className="rounded-[6px] bg-white/[0.03] px-2 py-[3px] font-mono text-[10px] text-white/25 ring-1 ring-white/[0.03]">
                      {entry.agent}
                    </span>
                    {entry.overridden && (
                      <span className="pill text-[10px] bg-[#ffd60a]/[0.08] text-[#ffd60a]/80 ring-1 ring-[#ffd60a]/10">
                        OVERRIDDEN
                      </span>
                    )}
                  </div>
                  <p className="mt-1.5 text-[13px] text-white/40">{entry.action}</p>
                </div>
                <div className="text-right shrink-0">
                  <span className="font-mono text-[13px] font-semibold text-[#30d158]/70">
                    {entry.confidence}%
                  </span>
                  <p className="text-[10px] text-white/15">confidence</p>
                </div>
              </motion.div>
            );
          })}
        </div>
      </motion.div>
    </motion.div>
  );
}
