"use client";

import { memo } from "react";

interface TrainMarkerProps {
  trainId: string;
  name: string;
  status?: "normal" | "warning" | "stopped" | "rerouted";
  speed?: number;
  onClick?: () => void;
}

const STATUS_COLORS = {
  normal: "#0a84ff",
  warning: "#ffd60a",
  stopped: "#ff453a",
  rerouted: "#5e5ce6",
};

export const TrainMarker = memo(function TrainMarker({ trainId, name, status = "normal", speed, onClick }: TrainMarkerProps) {
  const color = STATUS_COLORS[status];

  return (
    <div
      onClick={onClick}
      className="relative flex flex-col items-center cursor-pointer group"
      title={`${name} (${trainId})`}
    >
      <div
        className="relative flex h-[10px] w-[10px] items-center justify-center"
      >
        <span
          className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-30"
          style={{ backgroundColor: color }}
        />
        <span
          className="relative inline-flex h-[8px] w-[8px] rounded-full transition-transform group-hover:scale-150"
          style={{ backgroundColor: color, boxShadow: `0 0 10px ${color}80` }}
        />
      </div>
      <div className="absolute -top-[18px] left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
        <div className="glass rounded-md px-2 py-0.5 whitespace-nowrap">
          <span className="font-mono text-[8px] font-medium text-white/60">{trainId}</span>
          {speed !== undefined && (
            <span className="ml-1 font-mono text-[8px] text-white/30">{speed}km/h</span>
          )}
        </div>
      </div>
    </div>
  );
});
