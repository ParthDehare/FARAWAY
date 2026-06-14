"use client";

import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useAcousticEvents } from "@/lib/queries";
import {
  Activity,
  Mic,
  BarChart3,
  Eye,
  Layers,
  TrendingUp,
  Pause,
  Play,
} from "lucide-react";

const spring = { type: "spring" as const, stiffness: 300, damping: 30 };

const fadeUp = {
  hidden: { opacity: 0, y: 20, scale: 0.98 },
  show: { opacity: 1, y: 0, scale: 1 },
};


const melSpectrogramData = Array.from({ length: 40 }, (_, row) =>
  Array.from({ length: 64 }, (_, col) => {
    const base = Math.sin(row * 0.3 + col * 0.1) * 0.5 + 0.5;
    const spike = col > 28 && col < 36 && row > 10 && row < 30 ? 0.8 : 0;
    return Math.min(1, base * 0.4 + spike + Math.random() * 0.15);
  })
);

function getHeatColor(value: number): string {
  if (value > 0.8) return "#ff453a";
  if (value > 0.65) return "#ffd60a";
  if (value > 0.5) return "#bf5af2";
  if (value > 0.35) return "#5e5ce6";
  if (value > 0.2) return "#1c1c2e";
  return "#0c0c0e";
}

const statsItems = [
  { label: "Frequency Peak", value: "14.2 kHz" },
  { label: "SNR Ratio", value: "34.7 dB" },
  { label: "Event Duration", value: "2.3s" },
  { label: "Fiber Node", value: "#KM402-N7" },
  { label: "Health Index", value: "34/100" },
  { label: "Last Inspect", value: "3d ago" },
];

export default function AcousticMonitorPage() {
  const { data } = useAcousticEvents();
  const events = data?.events ?? [];

  const classificationResults = events.length > 0 ? [
    { label: events[0]?.classification?.toUpperCase() || "UNKNOWN", confidence: (events[0]?.confidence ?? 0) * 100, color: events[0]?.severity === "critical" ? "#ff453a" : events[0]?.severity === "warning" ? "#ffd60a" : "#30d158" },
    ...events.slice(1, 4).map((e: any) => ({
      label: e.classification?.toUpperCase() || "UNKNOWN",
      confidence: (e.confidence ?? 0) * 100,
      color: e.severity === "critical" ? "#ff453a" : e.severity === "warning" ? "#ffd60a" : "#30d158",
    }))
  ] : [
    { label: "NORMAL", confidence: 97, color: "#30d158" },
  ];

  const historicalComparisons = events.slice(0, 3).map((e: any) => ({
    label: `${e.classification?.toUpperCase()} (ref)`,
    freq: "—",
    amplitude: e.severity === "critical" ? "High" : e.severity === "warning" ? "Medium" : "Low",
    match: Math.round((e.confidence ?? 0) * 100),
  }));

  const [isLive, setIsLive] = useState(true);
  const [micActive, setMicActive] = useState(false);
  const [waveform, setWaveform] = useState<number[]>(() =>
    Array.from({ length: 128 }, () => Math.random() * 0.3)
  );

  useEffect(() => {
    if (!isLive) return;
    const id = setInterval(() => {
      setWaveform((prev) => {
        const next = [...prev.slice(1)];
        const spikeZone = next.length > 80 && next.length < 100;
        const val = spikeZone
          ? Math.random() * 0.7 + 0.3
          : Math.random() * 0.3;
        next.push(val);
        return next;
      });
    }, 60);
    return () => clearInterval(id);
  }, [isLive]);

  return (
    <motion.div
      initial="hidden"
      animate="show"
      transition={{ staggerChildren: 0.08 }}
      className="space-y-5"
    >
      {/* Header */}
      <motion.div
        variants={fadeUp}
        transition={spring}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-[22px] font-semibold tracking-tight text-white/60">
            Acoustic Monitor
          </h1>
          <p className="mt-0.5 text-[13px] text-white/25">
            RailMind FFT/MEL Spectrogram — Real-time vibration analysis
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setIsLive(!isLive)}
            className={`pill flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-[11px] font-medium tracking-wide transition-all ${
              isLive
                ? "bg-[#30d158]/10 text-[#30d158] ring-1 ring-[#30d158]/20"
                : "bg-white/[0.04] text-white/40 ring-1 ring-white/[0.04]"
            }`}
          >
            {isLive ? <Play className="h-3 w-3" /> : <Pause className="h-3 w-3" />}
            {isLive ? "LIVE" : "PAUSED"}
          </button>
          <button onClick={() => { setMicActive(!micActive); toast.success(micActive ? "Mic Input disconnected" : "Sensor connected — Mic Input active"); }} className={`pill flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-[11px] font-medium transition-all ${micActive ? "bg-[#30d158]/10 text-[#30d158] ring-1 ring-[#30d158]/20" : "bg-white/[0.04] text-white/40 ring-1 ring-white/[0.04] hover:bg-white/[0.06] hover:text-white/60"}`}>
            <Mic className="h-3 w-3" />
            {micActive ? "Mic Active" : "Mic Input"}
          </button>
        </div>
      </motion.div>

      <div className="grid grid-cols-12 gap-4">
        {/* Live FFT Spectrogram */}
        <motion.div
          variants={fadeUp}
          transition={spring}
          className="col-span-8 glass rounded-2xl ring-1 ring-white/[0.03] overflow-hidden"
        >
          <div className="flex items-center justify-between px-5 py-3">
            <div className="flex items-center gap-2.5">
              <Activity className="h-3.5 w-3.5 text-[#0a84ff]" />
              <span className="text-[13px] font-medium text-white/60">
                RailMind FFT/MEL Spectrogram
              </span>
            </div>
            <div className="flex items-center gap-3">
              <span className="font-mono text-[10px] text-white/25">
                Segment: MUM-DEL-KM402
              </span>
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  isLive ? "bg-[#30d158] animate-pulse" : "bg-white/20"
                }`}
              />
            </div>
          </div>

          <div className="divider" />

          {/* Waveform Display */}
          <div className="relative h-[200px] bg-[#0c0c0e] p-4">
            <svg
              viewBox="0 0 640 160"
              className="h-full w-full"
              preserveAspectRatio="none"
            >
              {[0, 40, 80, 120, 160].map((y) => (
                <line
                  key={y}
                  x1="0"
                  y1={y}
                  x2="640"
                  y2={y}
                  stroke="rgba(255,255,255,0.03)"
                  strokeWidth="0.5"
                />
              ))}
              <polyline
                fill="none"
                stroke="#0a84ff"
                strokeWidth="1.5"
                points={waveform
                  .map((v, i) => `${(i / 128) * 640},${80 - v * 80}`)
                  .join(" ")}
              />
              <polyline
                fill="none"
                stroke="#0a84ff"
                strokeWidth="1.5"
                opacity="0.2"
                points={waveform
                  .map((v, i) => `${(i / 128) * 640},${80 + v * 80}`)
                  .join(" ")}
              />
              <rect
                x="400"
                y="0"
                width="100"
                height="160"
                fill="#ff453a"
                opacity="0.04"
              />
              <line
                x1="400"
                y1="0"
                x2="400"
                y2="160"
                stroke="#ff453a"
                strokeWidth="0.5"
                strokeDasharray="4,2"
                opacity="0.4"
              />
            </svg>
            <div className="absolute bottom-1 left-4 font-mono text-[8px] text-white/25">
              0 Hz
            </div>
            <div className="absolute bottom-1 right-4 font-mono text-[8px] text-white/25">
              22.05 kHz
            </div>
            <div className="absolute top-2 left-4 font-mono text-[8px] text-white/25">
              Amplitude
            </div>
            <div className="absolute top-2 right-4 rounded-md bg-[#ff453a]/10 px-2 py-0.5 font-mono text-[10px] font-medium text-[#ff453a]">
              ANOMALY ZONE
            </div>
          </div>

          {/* Mel Spectrogram Heatmap */}
          <div className="divider" />
          <div className="px-5 py-3 flex items-center justify-between">
            <span className="flex items-center gap-2 text-[13px] font-medium text-white/60">
              <Layers className="h-3.5 w-3.5 text-[#ffd60a]" />
              Mel-Spectrogram Heatmap
            </span>
            <span className="font-mono text-[10px] text-white/25">
              40 mel bands × 64 time frames
            </span>
          </div>
          <div className="px-5 pb-5">
            <div className="overflow-hidden rounded-xl bg-[#0c0c0e] ring-1 ring-white/[0.03]">
              <svg
                viewBox="0 0 640 200"
                className="w-full"
                style={{ height: "180px" }}
              >
                {melSpectrogramData.map((row, ri) =>
                  row.map((val, ci) => (
                    <rect
                      key={`${ri}-${ci}`}
                      x={ci * 10}
                      y={ri * 5}
                      width="10"
                      height="5"
                      fill={getHeatColor(val)}
                    />
                  ))
                )}
              </svg>
            </div>
            <div className="mt-2.5 flex items-center justify-between">
              <span className="font-mono text-[8px] text-white/25">
                Time →
              </span>
              <div className="flex items-center gap-1.5">
                <span className="font-mono text-[8px] text-white/25">Low</span>
                <div className="flex rounded-sm overflow-hidden">
                  {["#0c0c0e", "#1c1c2e", "#5e5ce6", "#bf5af2", "#ffd60a", "#ff453a"].map(
                    (c) => (
                      <div
                        key={c}
                        className="h-2 w-4"
                        style={{ backgroundColor: c }}
                      />
                    )
                  )}
                </div>
                <span className="font-mono text-[8px] text-white/25">High</span>
              </div>
              <span className="font-mono text-[8px] text-white/25">
                ↑ Frequency
              </span>
            </div>
          </div>
        </motion.div>

        {/* Right Panel */}
        <div className="col-span-4 space-y-4">
          {/* Classification Result */}
          <motion.div
            variants={fadeUp}
            transition={spring}
            className="glass glass-hover rounded-2xl p-5 ring-1 ring-white/[0.03]"
          >
            <h3 className="mb-4 flex items-center gap-2 text-[13px] font-medium text-white/60">
              <Eye className="h-3.5 w-3.5 text-[#ff453a]" />
              Classification Result
            </h3>
            <div className="space-y-3.5">
              {classificationResults.map((r, idx) => (
                <div key={`${r.label}-${idx}`}>
                  <div className="mb-1.5 flex items-center justify-between">
                    <span className="font-mono text-[11px] font-medium text-white/50">
                      {r.label}
                    </span>
                    <span
                      className="font-mono text-[13px] font-semibold"
                      style={{ color: r.color }}
                    >
                      {r.confidence}%
                    </span>
                  </div>
                  <div className="h-[6px] w-full rounded-full bg-white/[0.04]">
                    <motion.div
                      className="h-full rounded-full"
                      style={{ backgroundColor: r.color }}
                      initial={{ width: 0 }}
                      animate={{ width: `${r.confidence}%` }}
                      transition={{ duration: 1, delay: 0.3, ...spring }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Historical Analysis Comparison */}
          <motion.div
            variants={fadeUp}
            transition={spring}
            className="glass glass-hover rounded-2xl p-5 ring-1 ring-white/[0.03]"
          >
            <h3 className="mb-3 flex items-center gap-2 text-[13px] font-medium text-white/60">
              <BarChart3 className="h-3.5 w-3.5 text-[#0a84ff]" />
              Historical Analysis Comparison
            </h3>
            <p className="mb-3 text-[10px] uppercase tracking-widest text-white/25">
              Past Incidents
            </p>
            <div className="space-y-2">
              {historicalComparisons.map((h, idx) => (
                <div
                  key={`${h.label}-${idx}`}
                  className="rounded-xl bg-white/[0.02] px-3.5 py-2.5 ring-1 ring-white/[0.03]"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[10px] font-medium text-white/50">
                      {h.label}
                    </span>
                    <span className="pill rounded-full bg-[#30d158]/10 px-2 py-0.5 font-mono text-[10px] font-medium text-[#30d158]">
                      {h.match}% match
                    </span>
                  </div>
                  <div className="mt-1.5 flex items-center gap-3 text-[10px] text-white/25">
                    <span>{h.freq}</span>
                    <span>Amp: {h.amplitude}</span>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Multivariate Analysis */}
          <motion.div
            variants={fadeUp}
            transition={spring}
            className="glass glass-hover rounded-2xl p-5 ring-1 ring-white/[0.03]"
          >
            <h3 className="mb-4 flex items-center gap-2 text-[13px] font-medium text-white/60">
              <TrendingUp className="h-3.5 w-3.5 text-[#ffd60a]" />
              Multivariate Analysis
            </h3>
            <div className="grid grid-cols-2 gap-2">
              {statsItems.map((item) => (
                <div
                  key={item.label}
                  className="rounded-xl bg-white/[0.02] px-3 py-2.5 ring-1 ring-white/[0.04]"
                >
                  <p className="text-[10px] text-white/25">{item.label}</p>
                  <p className="mt-0.5 font-mono text-[13px] font-medium text-white/50">
                    {item.value}
                  </p>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
}
