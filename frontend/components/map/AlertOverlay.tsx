"use client";

import { memo } from "react";

interface AlertOverlayProps {
  id: string;
  severity: "warning" | "critical";
  label?: string;
  onClick?: () => void;
}

export const AlertOverlay = memo(function AlertOverlay({ id, severity, label, onClick }: AlertOverlayProps) {
  const color = severity === "critical" ? "#ff453a" : "#ffd60a";

  return (
    <div
      onClick={onClick}
      className="relative flex items-center justify-center cursor-pointer"
      title={label || id}
    >
      <span
        className="absolute h-6 w-6 rounded-full animate-ping"
        style={{ backgroundColor: color, opacity: 0.15 }}
      />
      <span
        className="absolute h-4 w-4 rounded-full animate-pulse"
        style={{ backgroundColor: color, opacity: 0.25 }}
      />
      <span
        className="relative h-3 w-3 rounded-full"
        style={{ backgroundColor: color, opacity: 0.7, boxShadow: `0 0 12px ${color}80` }}
      />
      <span
        className="absolute -top-4 left-1/2 -translate-x-1/2 whitespace-nowrap font-mono text-[9px] font-bold"
        style={{ color: `${color}99` }}
      >
        {id}
      </span>
    </div>
  );
});
