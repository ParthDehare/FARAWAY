"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useTrains } from "@/lib/queries";
import {
  Train,
  Users,
  Clock,
  Gauge,
  Search,
  Filter,
  ArrowUpDown,
  ArrowUpRight,
  ArrowDownRight,
  AlertTriangle,
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

const statusConfig: Record<string, { color: string; bg: string; ring: string; label: string; dot: string }> = {
  running: { color: "text-[#30d158]", bg: "bg-[#30d158]/[0.08]", ring: "ring-[#30d158]/10", label: "Running", dot: "bg-[#30d158]" },
  rerouted: { color: "text-[#0a84ff]", bg: "bg-[#0a84ff]/[0.08]", ring: "ring-[#0a84ff]/10", label: "Rerouted", dot: "bg-[#0a84ff]" },
  stopped: { color: "text-[#ff453a]", bg: "bg-[#ff453a]/[0.08]", ring: "ring-[#ff453a]/10", label: "Stopped", dot: "bg-[#ff453a] shadow-[0_0_8px_rgba(255,69,58,0.4)]" },
  warning: { color: "text-[#ffd60a]", bg: "bg-[#ffd60a]/[0.08]", ring: "ring-[#ffd60a]/10", label: "Warning", dot: "bg-[#ffd60a]" },
};

export default function TrainFleetPage() {
  const { data } = useTrains();
  const trains = data?.trains ?? [];

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [filterOpen, setFilterOpen] = useState(false);
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortAsc, setSortAsc] = useState(true);
  const [expandedTrain, setExpandedTrain] = useState<string | null>(null);

  const filteredTrains = trains
    .filter((t: any) => {
      if (statusFilter && t.status !== statusFilter) return false;
      if (search) {
        const s = search.toLowerCase();
        return (t.number?.toLowerCase().includes(s) || t.name?.toLowerCase().includes(s) || t.origin?.toLowerCase().includes(s) || t.destination?.toLowerCase().includes(s));
      }
      return true;
    })
    .sort((a: any, b: any) => {
      if (!sortKey) return 0;
      const av = sortKey === "speed" ? a.speed_kmh : sortKey === "delay" ? a.delay_minutes : a.passenger_count;
      const bv = sortKey === "speed" ? b.speed_kmh : sortKey === "delay" ? b.delay_minutes : b.passenger_count;
      return sortAsc ? av - bv : bv - av;
    });

  const running = trains.filter((t: any) => t.status === "running").length;
  const delayed = trains.filter((t: any) => t.delay_minutes > 0).length;
  const totalPassengers = trains.reduce((a: number, t: any) => a + (t.passenger_count ?? 0), 0);

  const stats = [
    { label: "Total Tracked", value: trains.length.toString(), icon: Train, gradient: "from-[#0a84ff]/10 to-[#5e5ce6]/10", iconColor: "#0a84ff", change: "+2", up: true },
    { label: "Running", value: running.toString(), icon: Gauge, gradient: "from-[#30d158]/10 to-[#34c759]/10", iconColor: "#30d158", change: "On track", up: true },
    { label: "Delayed", value: delayed.toString(), icon: Clock, gradient: "from-[#ffd60a]/10 to-[#ff9f0a]/10", iconColor: "#ffd60a", change: `${delayed} trains`, up: false },
    { label: "Passengers", value: `${(totalPassengers / 1000).toFixed(1)}K`, icon: Users, gradient: "from-[#bf5af2]/10 to-[#af52de]/10", iconColor: "#bf5af2", change: "+1.2K", up: true },
  ];

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-5">
      <motion.div variants={fadeUp} className="flex items-end justify-between">
        <div>
          <h1 className="font-display text-[22px] font-semibold tracking-[-0.02em]">
            Train Fleet
          </h1>
          <p className="mt-0.5 text-[13px] text-white/30">
            Real-time tracking of all monitored trains
          </p>
        </div>
        <div className="flex items-center gap-1.5 rounded-full bg-[#30d158]/[0.08] px-3 py-1.5 ring-1 ring-[#30d158]/10">
          <span className="relative flex h-[5px] w-[5px]">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#30d158] opacity-40" />
            <span className="relative inline-flex h-[5px] w-[5px] rounded-full bg-[#30d158]" />
          </span>
          <span className="text-[11px] font-medium text-[#30d158]/80">Live</span>
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
                    <ArrowDownRight className="h-3 w-3 text-[#ffd60a]" />
                  )}
                  <span className={`text-[11px] font-medium ${s.up ? "text-[#30d158]/70" : "text-[#ffd60a]/70"}`}>
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

      <motion.div variants={fadeUp} className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-white/20" />
          <input
            type="text"
            placeholder="Search by train number, name, or route..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-10 w-full rounded-xl bg-white/[0.04] pl-10 pr-4 font-mono text-[13px] text-white/50 placeholder:text-white/20 ring-1 ring-white/[0.04] focus:ring-[#0a84ff]/40 focus:outline-none transition-all duration-300"
          />
        </div>
        <div className="relative">
          <button onClick={() => setFilterOpen(!filterOpen)} className="flex items-center gap-1.5 rounded-xl bg-white/[0.04] px-4 py-2.5 text-[13px] text-white/40 ring-1 ring-white/[0.04] transition-all duration-300 hover:bg-white/[0.06] hover:text-white/60">
            <Filter className="h-3.5 w-3.5" />
            {statusFilter ? statusFilter.charAt(0).toUpperCase() + statusFilter.slice(1) : "Filter"}
          </button>
          {filterOpen && (
            <div className="absolute right-0 top-full mt-1 z-20 w-40 rounded-xl bg-[#1c1c1e]/95 p-1.5 ring-1 ring-white/[0.06] backdrop-blur-xl shadow-2xl">
              {[null, "running", "rerouted", "stopped", "warning"].map((s) => (
                <button key={s ?? "all"} onClick={() => { setStatusFilter(s); setFilterOpen(false); }}
                  className={`w-full rounded-lg px-3 py-2 text-left text-[12px] transition-colors ${statusFilter === s ? "bg-[#0a84ff]/10 text-[#0a84ff]" : "text-white/40 hover:bg-white/[0.04]"}`}>
                  {s ? s.charAt(0).toUpperCase() + s.slice(1) : "All Status"}
                </button>
              ))}
            </div>
          )}
        </div>
        <button onClick={() => {
          const keys = [null, "speed", "delay", "passengers"];
          const idx = keys.indexOf(sortKey);
          const next = keys[(idx + 1) % keys.length];
          if (next === sortKey) setSortAsc(!sortAsc);
          else { setSortKey(next); setSortAsc(true); }
        }} className="flex items-center gap-1.5 rounded-xl bg-white/[0.04] px-4 py-2.5 text-[13px] text-white/40 ring-1 ring-white/[0.04] transition-all duration-300 hover:bg-white/[0.06] hover:text-white/60">
          <ArrowUpDown className="h-3.5 w-3.5" />
          {sortKey ? `Sort: ${sortKey}${sortAsc ? " ↑" : " ↓"}` : "Sort"}
        </button>
      </motion.div>

      <motion.div variants={fadeUp} className="glass rounded-2xl overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3">
          <span className="text-[13px] font-medium text-white/60">Fleet Overview</span>
          <span className="font-mono text-[10px] text-white/15">{filteredTrains.length} trains</span>
        </div>
        <div className="divider" />
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left">
                <th className="px-5 py-3 text-[10px] font-medium tracking-wide text-white/25 uppercase">Train</th>
                <th className="px-5 py-3 text-[10px] font-medium tracking-wide text-white/25 uppercase">Route</th>
                <th className="px-5 py-3 text-[10px] font-medium tracking-wide text-white/25 uppercase">Status</th>
                <th className="px-5 py-3 text-[10px] font-medium tracking-wide text-white/25 uppercase">Speed</th>
                <th className="px-5 py-3 text-[10px] font-medium tracking-wide text-white/25 uppercase">Passengers</th>
                <th className="px-5 py-3 text-[10px] font-medium tracking-wide text-white/25 uppercase">Delay</th>
                <th className="px-5 py-3 text-[10px] font-medium tracking-wide text-white/25 uppercase">Position</th>
                <th className="px-5 py-3 text-[10px] font-medium tracking-wide text-white/25 uppercase">ETA</th>
              </tr>
            </thead>
            <tbody>
              {filteredTrains.map((train, i) => {
                const sc = statusConfig[train.status];
                return (
                  <React.Fragment key={train.number}>
                  <motion.tr
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.4 + i * 0.06, ...spring }}
                    onClick={() => setExpandedTrain(expandedTrain === train.number ? null : train.number)}
                    className="transition-all duration-300 hover:bg-white/[0.02] cursor-pointer"
                  >
                    <td className="px-5 py-3">
                      <div>
                        <span className="font-mono text-[13px] font-medium text-white/50">{train.number}</span>
                        <p className="text-[11px] text-white/25">{train.name}</p>
                      </div>
                    </td>
                    <td className="px-5 py-3 text-[13px] text-white/40">
                      {train.origin} → {train.destination}
                    </td>
                    <td className="px-5 py-3">
                      <span className={`pill inline-flex items-center gap-1.5 ${sc.bg} ${sc.color} ring-1 ${sc.ring}`}>
                        <span className={`h-[5px] w-[5px] rounded-full ${sc.dot}`} />
                        {sc.label}
                      </span>
                    </td>
                    <td className="px-5 py-3 font-mono text-[13px] text-white/50">
                      {train.speed_kmh > 0 ? `${train.speed_kmh} km/h` : "—"}
                    </td>
                    <td className="px-5 py-3 font-mono text-[13px] text-white/50">
                      {train.passenger_count.toLocaleString()}
                    </td>
                    <td className="px-5 py-3">
                      {train.delay_minutes > 0 ? (
                        <span className={`font-mono text-[13px] ${train.delay_minutes > 30 ? "text-[#ff453a]" : "text-[#ffd60a]"}`}>
                          +{train.delay_minutes}m
                        </span>
                      ) : (
                        <span className="font-mono text-[13px] text-[#30d158]/70">On time</span>
                      )}
                    </td>
                    <td className="px-5 py-3 font-mono text-[13px] text-white/25">{train.current_segment || "—"}</td>
                    <td className="px-5 py-3 font-mono text-[13px] text-white/25">{"—"}</td>
                  </motion.tr>
                  <AnimatePresence>
                    {expandedTrain === train.number && (
                      <motion.tr
                        key={`${train.number}-detail`}
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.25 }}
                      >
                        <td colSpan={8} className="px-5 pb-4">
                          <div className="rounded-xl bg-white/[0.02] p-4 ring-1 ring-white/[0.04]">
                            <div className="grid grid-cols-4 gap-4">
                              <div>
                                <p className="text-[10px] text-white/25 uppercase">Train Number</p>
                                <p className="mt-1 font-mono text-[13px] text-white/50">{train.number}</p>
                              </div>
                              <div>
                                <p className="text-[10px] text-white/25 uppercase">Full Route</p>
                                <p className="mt-1 text-[13px] text-white/50">{train.origin} → {train.destination}</p>
                              </div>
                              <div>
                                <p className="text-[10px] text-white/25 uppercase">Current Speed</p>
                                <p className="mt-1 font-mono text-[13px] text-white/50">{train.speed_kmh} km/h</p>
                              </div>
                              <div>
                                <p className="text-[10px] text-white/25 uppercase">Passengers</p>
                                <p className="mt-1 font-mono text-[13px] text-white/50">{train.passenger_count.toLocaleString()}</p>
                              </div>
                            </div>
                          </div>
                        </td>
                      </motion.tr>
                    )}
                  </AnimatePresence>
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </motion.div>
    </motion.div>
  );
}
