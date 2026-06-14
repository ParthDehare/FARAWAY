"use client";

import { useEffect, useState, useRef } from "react";
import { motion } from "framer-motion";
import { Activity, Mic, MicOff, Layers } from "lucide-react";
import { useAcousticCapture } from "@/hooks/useAcousticCapture";

const spring = { type: "spring" as const, stiffness: 300, damping: 30 };

const MEL_DATA = Array.from({ length: 40 }, (_, row) =>
  Array.from({ length: 64 }, (_, col) => {
    const base = Math.sin(row * 0.3 + col * 0.1) * 0.5 + 0.5;
    const spike = col > 28 && col < 36 && row > 10 && row < 30 ? 0.8 : 0;
    return Math.min(1, base * 0.4 + spike + Math.random() * 0.15);
  })
);

function getHeatColor(v: number): string {
  if (v > 0.8) return "#ff453a";
  if (v > 0.65) return "#ffd60a";
  if (v > 0.5) return "#bf5af2";
  if (v > 0.35) return "#5e5ce6";
  if (v > 0.2) return "#1c1c2e";
  return "#0c0c0e";
}

interface AcousticMonitorProps {
  compact?: boolean;
}

export function AcousticMonitor({ compact = false }: AcousticMonitorProps) {
  const { isCapturing, data, start, stop } = useAcousticCapture();
  const [waveform, setWaveform] = useState<number[]>(() =>
    Array.from({ length: 128 }, () => Math.random() * 0.3)
  );

  useEffect(() => {
    if (data?.frequencyData) {
      const normalized = Array.from(data.frequencyData.slice(0, 128)).map(
        (v) => Math.max(0, (v + 100) / 100)
      );
      setWaveform(normalized);
      return;
    }

    const id = setInterval(() => {
      setWaveform((prev) => {
        const next = [...prev.slice(1)];
        const spikeZone = next.length > 80 && next.length < 100;
        next.push(spikeZone ? Math.random() * 0.7 + 0.3 : Math.random() * 0.3);
        return next;
      });
    }, 60);
    return () => clearInterval(id);
  }, [data]);

  return (
    <div className="space-y-3">
      {/* Waveform */}
      <div className="glass rounded-2xl overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2.5">
          <div className="flex items-center gap-2">
            <Activity className="h-3.5 w-3.5 text-[#0a84ff]" />
            <span className="text-[12px] font-medium text-white/50">FFT Spectrogram</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => isCapturing ? stop() : start()}
              className={`flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium transition-all ${
                isCapturing
                  ? "bg-[#ff453a]/10 text-[#ff453a] ring-1 ring-[#ff453a]/10"
                  : "bg-white/[0.04] text-white/30 ring-1 ring-white/[0.04] hover:text-white/50"
              }`}
            >
              {isCapturing ? <MicOff className="h-2.5 w-2.5" /> : <Mic className="h-2.5 w-2.5" />}
              {isCapturing ? "Stop" : "Mic"}
            </button>
            <span className="h-1.5 w-1.5 rounded-full bg-[#30d158] animate-pulse" />
          </div>
        </div>
        <div className="divider" />
        <div className={`relative bg-[#0c0c0e] p-3 ${compact ? "h-[120px]" : "h-[180px]"}`}>
          <svg viewBox="0 0 640 160" className="h-full w-full" preserveAspectRatio="none">
            {[0, 40, 80, 120, 160].map((y) => (
              <line key={y} x1="0" y1={y} x2="640" y2={y} stroke="rgba(255,255,255,0.03)" strokeWidth="0.5" />
            ))}
            <polyline fill="none" stroke="#0a84ff" strokeWidth="1.5"
              points={waveform.map((v, i) => `${(i / 128) * 640},${80 - v * 80}`).join(" ")} />
            <polyline fill="none" stroke="#0a84ff" strokeWidth="1.5" opacity="0.2"
              points={waveform.map((v, i) => `${(i / 128) * 640},${80 + v * 80}`).join(" ")} />
            <rect x="400" y="0" width="100" height="160" fill="#ff453a" opacity="0.04" />
          </svg>
          <div className="absolute top-2 right-3 rounded-md bg-[#ff453a]/10 px-2 py-0.5 font-mono text-[9px] font-medium text-[#ff453a]">
            ANOMALY
          </div>
        </div>
      </div>

      {/* Mel spectrogram */}
      {!compact && (
        <div className="glass rounded-2xl overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2.5">
            <div className="flex items-center gap-2">
              <Layers className="h-3.5 w-3.5 text-[#ffd60a]" />
              <span className="text-[12px] font-medium text-white/50">Mel-Spectrogram</span>
            </div>
            <span className="font-mono text-[9px] text-white/20">40 mel × 64 frames</span>
          </div>
          <div className="divider" />
          <div className="p-3">
            <div className="overflow-hidden rounded-lg bg-[#0c0c0e] ring-1 ring-white/[0.03]">
              <svg viewBox="0 0 640 200" className="w-full" style={{ height: "140px" }}>
                {MEL_DATA.map((row, ri) =>
                  row.map((val, ci) => (
                    <rect key={`${ri}-${ci}`} x={ci * 10} y={ri * 5} width="10" height="5" fill={getHeatColor(val)} />
                  ))
                )}
              </svg>
            </div>
            <div className="mt-2 flex items-center justify-between">
              <span className="font-mono text-[8px] text-white/20">Time →</span>
              <div className="flex items-center gap-1">
                <span className="font-mono text-[8px] text-white/20">Low</span>
                <div className="flex rounded-sm overflow-hidden">
                  {["#0c0c0e", "#1c1c2e", "#5e5ce6", "#bf5af2", "#ffd60a", "#ff453a"].map((c) => (
                    <div key={c} className="h-1.5 w-3" style={{ backgroundColor: c }} />
                  ))}
                </div>
                <span className="font-mono text-[8px] text-white/20">High</span>
              </div>
              <span className="font-mono text-[8px] text-white/20">↑ Freq</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
