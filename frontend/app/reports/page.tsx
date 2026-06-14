"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import { Modal } from "@/components/ui/Modal";
import {
  FileBarChart,
  Download,
  FileText,
  Calendar,
  Eye,
  Plus,
  ArrowUpRight,
  ArrowDownRight,
  AlertTriangle,
  BookOpen,
} from "lucide-react";
import { useIncident } from "@/lib/queries";

const spring = { type: "spring" as const, stiffness: 300, damping: 30 };
const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.07, delayChildren: 0.1 } },
};
const fadeUp = {
  hidden: { opacity: 0, y: 20, scale: 0.98 },
  show: { opacity: 1, y: 0, scale: 1, transition: { ...spring, duration: 0.55 } },
};

const typeConfig: Record<string, { color: string; bg: string; ring: string }> = {
  Incident: { color: "text-[#ff453a]", bg: "bg-[#ff453a]/[0.08]", ring: "ring-[#ff453a]/10" },
  Maintenance: { color: "text-[#ffd60a]", bg: "bg-[#ffd60a]/[0.08]", ring: "ring-[#ffd60a]/10" },
  Health: { color: "text-[#30d158]", bg: "bg-[#30d158]/[0.08]", ring: "ring-[#30d158]/10" },
  Compliance: { color: "text-[#0a84ff]", bg: "bg-[#0a84ff]/[0.08]", ring: "ring-[#0a84ff]/10" },
};

export default function ReportsPage() {
  const { data: incident1 } = useIncident("IR-2026-0042");
  const { data: incident2 } = useIncident("IR-2026-0041");

  const reports = [incident1, incident2].filter(Boolean).map((inc: any) => ({
    id: inc.id,
    title: `${inc.type?.replace(/_/g, ' ')} — ${inc.segment_code || inc.segment || ''}`,
    type: "Incident",
    date: inc.created_at?.slice(0, 10) || "—",
    time: inc.created_at?.slice(11, 16) || "—",
    status: inc.resolved ? "generated" : "generating",
    pages: inc.timeline?.length * 3 || 8,
    severity: inc.severity || "warning",
  }));

  const incidentCount = reports.length;
  const criticalCount = reports.filter((r) => r.severity === "critical").length;
  const pendingCount = reports.filter((r) => r.status === "generating").length;

  const stats = [
    { label: "Total Reports", value: reports.length.toString(), icon: FileBarChart, gradient: "from-[#0a84ff]/10 to-[#5e5ce6]/10", iconColor: "#0a84ff", change: `${reports.length} loaded`, up: true },
    { label: "This Week", value: reports.length.toString(), icon: Calendar, gradient: "from-[#30d158]/10 to-[#34c759]/10", iconColor: "#30d158", change: `+${reports.length}`, up: true },
    { label: "Incident Reports", value: incidentCount.toString(), icon: AlertTriangle, gradient: "from-[#ff453a]/10 to-[#ff6961]/10", iconColor: "#ff453a", change: criticalCount > 0 ? `${criticalCount} critical` : "0 critical", up: false },
    { label: "Pending Export", value: pendingCount.toString(), icon: BookOpen, gradient: "from-[#ffd60a]/10 to-[#ff9f0a]/10", iconColor: "#ffd60a", change: pendingCount > 0 ? "Generating" : "All done", up: false },
  ];

  const [generateOpen, setGenerateOpen] = useState(false);
  const [viewReport, setViewReport] = useState<any>(null);
  const [reportType, setReportType] = useState("Incident");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-5">
      <motion.div variants={fadeUp} className="flex items-end justify-between">
        <div>
          <h1 className="font-display text-[22px] font-semibold tracking-[-0.02em]">
            Reports
          </h1>
          <p className="mt-0.5 text-[13px] text-white/30">
            AI-generated incident, maintenance & compliance reports
          </p>
        </div>
        <button onClick={() => setGenerateOpen(true)} className="flex items-center gap-1.5 rounded-xl bg-[#0a84ff] px-4 py-2.5 text-[13px] font-medium text-white transition-all duration-300 hover:bg-[#0a84ff]/80">
          <Plus className="h-3.5 w-3.5" />
          Generate Report
        </button>
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
          <span className="text-[13px] font-medium text-white/60">All Reports</span>
          <span className="font-mono text-[10px] text-white/15">{reports.length} reports</span>
        </div>
        <div className="divider" />
        <div>
          {reports.map((report, i) => {
            const tc = typeConfig[report.type];
            return (
              <motion.div
                key={report.id}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + i * 0.06, ...spring }}
                className="flex items-center gap-4 px-5 py-3.5 transition-all duration-300 hover:bg-white/[0.02] cursor-pointer"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/[0.02] ring-1 ring-white/[0.03] shrink-0">
                  <FileText className="h-[18px] w-[18px] text-white/25" />
                </div>
                <div className="flex-1 min-w-0">
                  <span className="text-[13px] font-medium text-white/50">{report.title}</span>
                  <div className="mt-1 flex items-center gap-3 text-[11px] text-white/20">
                    <span className="font-mono">{report.id}</span>
                    <span className={`pill text-[10px] ring-1 ${tc.bg} ${tc.color} ${tc.ring}`}>
                      {report.type}
                    </span>
                    <span className="flex items-center gap-1">
                      <Calendar className="h-2.5 w-2.5" />
                      {report.date}
                    </span>
                    <span>{report.pages} pages</span>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {report.status === "generated" ? (
                    <>
                      <button onClick={() => setViewReport(report)} className="flex items-center gap-1 rounded-xl bg-[#0a84ff]/[0.08] px-3 py-1.5 text-[11px] font-medium text-[#0a84ff]/80 ring-1 ring-[#0a84ff]/10 transition-all duration-300 hover:bg-[#0a84ff]/[0.14]">
                        <Eye className="h-3 w-3" />
                        View
                      </button>
                      <button onClick={() => { const content = `RailMind - ${report.type} Report\nID: ${report.id}\nDate: ${report.date}\nSeverity: ${report.severity}\n\nReport: ${report.title}\nPages: ${report.pages}\n\nGenerated by RailMind AI`; const blob = new Blob([content], { type: "text/plain" }); const url = URL.createObjectURL(blob); const a = document.createElement("a"); a.href = url; a.download = `${report.id}-report.txt`; a.click(); URL.revokeObjectURL(url); toast.success("Report downloaded: " + report.id); }} className="flex items-center gap-1 rounded-xl bg-white/[0.04] px-3 py-1.5 text-[11px] font-medium text-white/40 ring-1 ring-white/[0.04] transition-all duration-300 hover:bg-white/[0.06] hover:text-white/60">
                        <Download className="h-3 w-3" />
                        PDF
                      </button>
                    </>
                  ) : (
                    <span className="pill text-[10px] bg-[#ffd60a]/[0.08] text-[#ffd60a]/80 ring-1 ring-[#ffd60a]/10 animate-pulse">
                      Generating...
                    </span>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      </motion.div>

      <Modal open={generateOpen} onOpenChange={setGenerateOpen} title="Generate Report">
        <div className="space-y-4">
          <div>
            <label className="text-[11px] text-white/25 uppercase">Report Type</label>
            <div className="mt-1 grid grid-cols-2 gap-2">
              {["Incident", "Maintenance", "Health", "Compliance"].map((t) => (
                <button key={t} onClick={() => setReportType(t)} className={`rounded-xl py-2.5 text-[12px] ring-1 transition-colors ${reportType === t ? "bg-[#0a84ff]/20 text-[#0a84ff] ring-[#0a84ff]/30" : "bg-white/[0.04] text-white/40 ring-white/[0.04] hover:bg-white/[0.06]"}`}>{t}</button>
              ))}
            </div>
          </div>
          <div>
            <label className="text-[11px] text-white/25 uppercase">Date Range</label>
            <div className="mt-1 flex gap-2">
              <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="flex-1 rounded-xl bg-white/[0.04] px-3 py-2.5 text-[13px] text-white/50 ring-1 ring-white/[0.04] focus:outline-none focus:ring-[#0a84ff]/40" />
              <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="flex-1 rounded-xl bg-white/[0.04] px-3 py-2.5 text-[13px] text-white/50 ring-1 ring-white/[0.04] focus:outline-none focus:ring-[#0a84ff]/40" />
            </div>
          </div>
          <button onClick={() => { setGenerateOpen(false); toast.success(`${reportType} report generation started${dateFrom ? ` (${dateFrom} to ${dateTo || "now"})` : ""}`); setReportType("Incident"); setDateFrom(""); setDateTo(""); }}
            className="w-full rounded-xl bg-[#0a84ff] py-2.5 text-[13px] font-semibold text-white hover:bg-[#0a84ff]/80 transition-colors">
            Generate Report
          </button>
        </div>
      </Modal>

      <Modal open={!!viewReport} onOpenChange={() => setViewReport(null)} title={viewReport?.title ?? "Report"} size="lg">
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-[10px] text-white/25 uppercase">Report ID</p>
              <p className="mt-1 font-mono text-[13px] text-white/50">{viewReport?.id}</p>
            </div>
            <div>
              <p className="text-[10px] text-white/25 uppercase">Type</p>
              <p className="mt-1 text-[13px] text-white/50">{viewReport?.type}</p>
            </div>
            <div>
              <p className="text-[10px] text-white/25 uppercase">Date</p>
              <p className="mt-1 font-mono text-[13px] text-white/50">{viewReport?.date}</p>
            </div>
          </div>
          <div className="rounded-xl bg-white/[0.02] p-4 ring-1 ring-white/[0.04]">
            <p className="text-[12px] text-white/30 leading-relaxed">
              This incident report covers the events on {viewReport?.date} regarding {viewReport?.title}.
              The AI agents detected and responded to this {viewReport?.severity} severity event with automated protocols.
              Full analysis includes timeline reconstruction, agent decision chain, and recommended follow-up actions.
            </p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => { const content = `RailMind - ${viewReport?.type} Report\nID: ${viewReport?.id}\nDate: ${viewReport?.date}\nSeverity: ${viewReport?.severity}\n\nReport: ${viewReport?.title}\nPages: ${viewReport?.pages}\n\nThis incident report covers the events on ${viewReport?.date} regarding ${viewReport?.title}.\nThe AI agents detected and responded to this ${viewReport?.severity} severity event with automated protocols.\nFull analysis includes timeline reconstruction, agent decision chain, and recommended follow-up actions.\n\nGenerated by RailMind AI`; const blob = new Blob([content], { type: "text/plain" }); const url = URL.createObjectURL(blob); const a = document.createElement("a"); a.href = url; a.download = `${viewReport?.id}-full-report.txt`; a.click(); URL.revokeObjectURL(url); toast.success("Report downloaded"); }} className="flex-1 rounded-xl bg-white/[0.04] py-2.5 text-[13px] text-white/40 ring-1 ring-white/[0.04] hover:bg-white/[0.06] transition-colors">
              Download PDF
            </button>
            <button onClick={() => setViewReport(null)} className="flex-1 rounded-xl bg-[#0a84ff] py-2.5 text-[13px] font-semibold text-white hover:bg-[#0a84ff]/80 transition-colors">
              Close
            </button>
          </div>
        </div>
      </Modal>
    </motion.div>
  );
}
