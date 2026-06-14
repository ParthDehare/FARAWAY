"use client";

import { motion } from "framer-motion";
import { Plane, Battery, MapPin, Clock, Wifi } from "lucide-react";

const spring = { type: "spring" as const, stiffness: 300, damping: 30 };

const DRONES = [
  { id: "UAV-B4", status: "deployed" as const, battery: 94, mission: "Visual confirm KM-402", eta: "2m 18s", location: "MUM-DEL corridor" },
  { id: "UAV-A1", status: "ready" as const, battery: 100, mission: "Standby", eta: "—", location: "Mumbai depot" },
  { id: "UAV-C2", status: "returning" as const, battery: 23, mission: "Inspection complete", eta: "7m 45s", location: "KON-RLY" },
  { id: "UAV-A3", status: "charging" as const, battery: 56, mission: "Charging", eta: "32m", location: "Delhi depot" },
  { id: "UAV-B1", status: "ready" as const, battery: 88, mission: "Standby", eta: "—", location: "Chennai depot" },
  { id: "UAV-D1", status: "deployed" as const, battery: 71, mission: "Perimeter patrol", eta: "14m", location: "KOL-GHY" },
];

const statusConfig = {
  deployed: { color: "#0a84ff", label: "DEPLOYED", dot: "bg-[#0a84ff]" },
  ready: { color: "#30d158", label: "READY", dot: "bg-[#30d158]" },
  returning: { color: "#ffd60a", label: "RETURNING", dot: "bg-[#ffd60a]" },
  charging: { color: "#636366", label: "CHARGING", dot: "bg-[#636366]" },
};

interface DroneFleetPanelProps {
  compact?: boolean;
  onDispatch?: (droneId: string) => void;
}

export function DroneFleetPanel({ compact = false, onDispatch }: DroneFleetPanelProps) {
  const items = compact ? DRONES.slice(0, 3) : DRONES;

  return (
    <div className={compact ? "space-y-2" : "grid grid-cols-2 gap-2"}>
      {items.map((drone, i) => {
        const cfg = statusConfig[drone.status];
        return (
          <motion.div
            key={drone.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06, ...spring }}
            className="glass rounded-xl p-3 ring-1 ring-white/[0.03]"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg" style={{ backgroundColor: `${cfg.color}15` }}>
                  <Plane className="h-3.5 w-3.5" style={{ color: cfg.color }} />
                </div>
                <div>
                  <span className="font-mono text-[12px] font-semibold text-white/60">{drone.id}</span>
                  <p className="text-[9px] font-medium" style={{ color: `${cfg.color}99` }}>{cfg.label}</p>
                </div>
              </div>
              {drone.status === "deployed" && (
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-40" style={{ backgroundColor: cfg.color }} />
                  <span className="relative inline-flex h-2 w-2 rounded-full" style={{ backgroundColor: cfg.color }} />
                </span>
              )}
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center gap-2 text-[10px]">
                <Battery className="h-3 w-3 text-white/20" />
                <div className="flex-1 h-[3px] rounded-full bg-white/[0.04]">
                  <div className="h-full rounded-full transition-all"
                    style={{
                      width: `${drone.battery}%`,
                      backgroundColor: drone.battery > 50 ? "#30d158" : drone.battery > 20 ? "#ffd60a" : "#ff453a",
                    }} />
                </div>
                <span className="font-mono text-white/30">{drone.battery}%</span>
              </div>

              <div className="flex items-center gap-2 text-[10px] text-white/25">
                <MapPin className="h-3 w-3" />
                <span className="truncate">{drone.location}</span>
              </div>

              {!compact && (
                <>
                  <div className="flex items-center gap-2 text-[10px] text-white/25">
                    <Wifi className="h-3 w-3" />
                    <span className="truncate">{drone.mission}</span>
                  </div>
                  <div className="flex items-center gap-2 text-[10px] text-white/25">
                    <Clock className="h-3 w-3" />
                    <span>ETA: {drone.eta}</span>
                  </div>
                </>
              )}

              {drone.status === "ready" && onDispatch && (
                <button
                  onClick={() => onDispatch(drone.id)}
                  className="mt-1 w-full rounded-lg bg-[#0a84ff] py-1.5 text-[10px] font-semibold text-white transition-all hover:bg-[#0a84ff]/80 active:scale-[0.98]"
                >
                  Deploy
                </button>
              )}
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
