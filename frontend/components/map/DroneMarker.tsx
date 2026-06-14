"use client";

import { memo } from "react";
import { Plane } from "lucide-react";

interface DroneMarkerProps {
  id: string;
  status: "deployed" | "ready" | "returning" | "charging";
  battery: number;
  onClick?: () => void;
}

const STATUS_COLORS = {
  deployed: "#0a84ff",
  ready: "#30d158",
  returning: "#ffd60a",
  charging: "#636366",
};

export const DroneMarker = memo(function DroneMarker({ id, status, battery, onClick }: DroneMarkerProps) {
  const color = STATUS_COLORS[status];

  return (
    <div onClick={onClick} className="relative flex flex-col items-center cursor-pointer group" title={`${id} (${status})`}>
      <div className="relative">
        {status === "deployed" && (
          <span className="absolute -inset-1 rounded-full animate-ping opacity-20" style={{ backgroundColor: color }} />
        )}
        <div className="flex h-6 w-6 items-center justify-center rounded-full" style={{ backgroundColor: `${color}30`, border: `1.5px solid ${color}60` }}>
          <Plane className="h-3 w-3" style={{ color }} />
        </div>
      </div>
      <span className="mt-1 font-mono text-[7px] font-bold" style={{ color: `${color}80` }}>{id}</span>
      <div className="absolute -top-5 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity">
        <div className="glass rounded-md px-2 py-0.5 whitespace-nowrap">
          <span className="font-mono text-[8px] text-white/40">{battery}%</span>
        </div>
      </div>
    </div>
  );
});
