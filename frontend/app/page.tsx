"use client";

import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import {
  Activity,
  CloudRain,
  Route,
  AlertTriangle,
  FileText,
  Shield,
  Train,
  MapPin,
  Users,
  Zap,
  TrendingUp,
  Eye,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import { useTrains, useTracks, useAgents, useAuditLog } from "@/lib/queries";
import { useUiStore } from "@/stores/uiStore";

const CommandMap = dynamic(
  () => import("@/components/map/CommandMap").then((m) => ({ default: m.CommandMap })),
  { ssr: false, loading: () => <div className="h-[440px] bg-[#0c0c0e] animate-pulse rounded-b-2xl" /> }
);

const spring = { type: "spring", stiffness: 300, damping: 30 };
const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.07, delayChildren: 0.1 } },
};
const fadeUp = {
  hidden: { opacity: 0, y: 20, scale: 0.98 },
  show: { opacity: 1, y: 0, scale: 1, transition: { ...spring, duration: 0.55 } },
};

const agentIcons: Record<string, { icon: React.ElementType; color: string }> = {
  acoustic: { icon: Activity, color: "#30d158" },
  weather: { icon: CloudRain, color: "#0a84ff" },
  routing: { icon: Route, color: "#ffd60a" },
  emergency: { icon: AlertTriangle, color: "#ff453a" },
  reporter: { icon: FileText, color: "#bf5af2" },
  supervisor: { icon: Shield, color: "#5e5ce6" },
};

export default function NetworkOverview() {
  const { userRole } = useUiStore();
  const { data: trainData } = useTrains();
  const { data: trackData } = useTracks();
  const { data: agentData } = useAgents();
  const { data: auditData } = useAuditLog(undefined, 5);

  const trains = trainData?.trains ?? [];
  const segments = trackData?.segments ?? [];
  const agentList = agentData?.agents ?? [];
  const events = auditData?.entries ?? [];

  const runningTrains = trains.filter((t: any) => t.status === "running").length;
  const totalPassengers = trains.reduce((a: number, t: any) => a + (t.passenger_count || 0), 0);
  const alertCount = segments.filter((s: any) => s.status === "critical" || s.status === "warning").length;

  const stats = [
    { label: "Active Trains", value: trains.length.toString(), change: `${runningTrains} running`, up: true, icon: Train, gradient: "from-[#0a84ff]/10 to-[#5e5ce6]/10", iconColor: "#0a84ff" },
    { label: "Track Segments", value: segments.length.toString(), change: "Monitored", up: true, icon: MapPin, gradient: "from-[#30d158]/10 to-[#34c759]/10", iconColor: "#30d158" },
    { label: "Passengers", value: totalPassengers > 1000 ? `${(totalPassengers / 1000).toFixed(1)}K` : totalPassengers.toString(), change: "Live", up: true, icon: Users, gradient: "from-[#bf5af2]/10 to-[#af52de]/10", iconColor: "#bf5af2" },
    { label: "Alerts", value: alertCount.toString(), change: alertCount > 0 ? `${alertCount} active` : "All clear", up: alertCount === 0, icon: AlertTriangle, gradient: "from-[#ff453a]/10 to-[#ff6961]/10", iconColor: "#ff453a" },
  ];

  const healthSegments = segments
    .filter((s: any) => s.status !== "normal")
    .slice(0, 5)
    .map((s: any) => ({
      id: s.code || s.id,
      route: s.route || "",
      score: s.health_index ?? s.health ?? 0,
      status: s.status,
    }));

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-5">
      {/* Header */}
      <motion.div variants={fadeUp} className="flex items-end justify-between">
        <div>
          <h1 className="font-display text-[22px] font-semibold tracking-[-0.02em]">
            Network Overview
          </h1>
          <p className="mt-0.5 text-[13px] text-white/30">
            Real-time railway intelligence across India
          </p>
        </div>
        <div className="flex items-center gap-1.5 rounded-full bg-[#30d158]/[0.08] px-3 py-1.5 ring-1 ring-[#30d158]/10">
          <span className="relative flex h-[5px] w-[5px]">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#30d158] opacity-40" />
            <span className="relative inline-flex h-[5px] w-[5px] rounded-full bg-[#30d158]" />
          </span>
          <span className="text-[11px] font-medium text-[#30d158]/80">Monitoring</span>
        </div>
      </motion.div>

      {/* Stat Cards */}
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

      {/* Map + Right panels */}
      <div className="grid grid-cols-12 gap-3">
        {/* Map */}
        <motion.div variants={fadeUp} className="col-span-8 glass rounded-2xl overflow-hidden">
          <div className="flex items-center justify-between px-5 py-3">
            <span className="text-[13px] font-medium text-white/60">Live Network Map</span>
            <div className="flex items-center gap-1.5">
              <span className="relative flex h-[5px] w-[5px]">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#30d158] opacity-40" />
                <span className="relative inline-flex h-[5px] w-[5px] rounded-full bg-[#30d158]" />
              </span>
              <span className="font-mono text-[10px] text-white/20">Real-time</span>
            </div>
          </div>
          <div className="divider" />
          <CommandMap height="440px" compact />
        </motion.div>

        {/* Right Panels */}
        <div className="col-span-4 space-y-3">
          {/* Agent Grid */}
          <motion.div variants={fadeUp} className="glass rounded-2xl p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[13px] font-medium text-white/60">Agent Grid</span>
              <span className="pill bg-[#30d158]/[0.08] text-[#30d158]/70 ring-1 ring-[#30d158]/10 text-[10px]">
                {agentData?.total_active ?? 0}/{agentList.length} ONLINE
              </span>
            </div>
            {userRole !== "maintenance" && userRole !== "drone_op" ? (
              <div className="grid grid-cols-3 gap-2">
                {agentList.map((a: any) => {
                  const cfg = agentIcons[a.id] || agentIcons[a.name?.split(" ")[0]?.toLowerCase()] || { icon: Zap, color: "#8e8e93" };
                  const Icon = cfg.icon;
                  return (
                    <motion.div
                      key={a.id || a.name}
                      whileHover={{ scale: 1.04, transition: spring }}
                      whileTap={{ scale: 0.98 }}
                      className="flex flex-col items-center gap-1.5 rounded-xl bg-white/[0.02] p-3 ring-1 ring-white/[0.04] transition-all duration-300 hover:bg-white/[0.05] hover:ring-white/[0.08] cursor-pointer"
                    >
                      <div className="flex h-8 w-8 items-center justify-center rounded-[10px]" style={{ backgroundColor: `${cfg.color}12` }}>
                        <Icon className="h-[15px] w-[15px]" style={{ color: cfg.color }} />
                      </div>
                      <span className="text-[10px] font-medium text-white/50">{(a.name || a.id).split(" ")[0]}</span>
                      <span className={`font-mono text-[8px] ${a.status === "active" ? "text-[#30d158]/60" : "text-[#ffd60a]/60"}`}>
                        {a.status === "active" ? "● Active" : "◐ Standby"}
                      </span>
                    </motion.div>
                  );
                })}
              </div>
            ) : (
              <div className="flex h-24 items-center justify-center rounded-xl border border-dashed border-white/10 text-[11px] text-white/30">
                Restricted Access
              </div>
            )}
          </motion.div>

          {/* Track Health */}
          <motion.div variants={fadeUp} className="glass rounded-2xl p-4">
            <span className="text-[13px] font-medium text-white/60">Track Health</span>
            <div className="mt-3 space-y-2">
              {healthSegments.length === 0 && (
                <p className="text-[11px] text-white/20 py-4 text-center">All segments healthy</p>
              )}
              {healthSegments.map((seg: any) => (
                <div key={seg.id} className="flex items-center gap-3 rounded-xl bg-white/[0.02] px-3 py-2.5 ring-1 ring-white/[0.03]">
                  <span className={`font-mono text-[13px] font-bold tabular-nums ${
                    seg.status === "critical" ? "text-[#ff453a]" : seg.status === "warning" ? "text-[#ffd60a]" : "text-[#30d158]"
                  }`}>
                    {seg.score}
                  </span>
                  <div className="flex-1">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[11px] font-medium text-white/60">{seg.id}</span>
                      <span className="font-mono text-[9px] text-white/15">{seg.route}</span>
                    </div>
                    <div className="mt-1.5 h-[3px] w-full rounded-full bg-white/[0.04]">
                      <motion.div
                        className="h-full rounded-full"
                        style={{
                          backgroundColor: seg.status === "critical" ? "#ff453a" : seg.status === "warning" ? "#ffd60a" : "#30d158",
                        }}
                        initial={{ width: 0 }}
                        animate={{ width: `${seg.score}%` }}
                        transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>

      {/* Event Feed */}
      <motion.div variants={fadeUp} className="glass rounded-2xl overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3">
          <span className="text-[13px] font-medium text-white/60">Live Event Feed</span>
          <span className="font-mono text-[10px] text-white/15">Recent</span>
        </div>
        <div className="divider" />
        <div>
          {events.length === 0 && (
            <p className="text-[13px] text-white/20 py-6 text-center">No recent events</p>
          )}
          {events.map((ev: any, i: number) => (
            <motion.div
              key={ev.id || i}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.6 + i * 0.08, ...spring }}
              className="flex items-center gap-4 px-5 py-3 transition-colors duration-300 hover:bg-white/[0.02]"
            >
              <span className="font-mono text-[11px] tabular-nums text-white/20 w-[52px] shrink-0">
                {ev.time || ev.timestamp?.slice(11, 19) || "—"}
              </span>
              <span className={`h-[6px] w-[6px] shrink-0 rounded-full ${
                ev.severity === "critical"
                  ? "bg-[#ff453a] shadow-[0_0_8px_rgba(255,69,58,0.4)]"
                  : ev.severity === "warning"
                  ? "bg-[#ffd60a]"
                  : "bg-[#30d158]"
              }`} />
              <span className="flex-1 text-[13px] text-white/50">{ev.action}</span>
              <span className="rounded-[6px] bg-white/[0.03] px-2 py-[3px] font-mono text-[10px] text-white/25">
                {ev.agent}
              </span>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
}
