"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import gsap from "gsap";
import { useAlertStore } from "@/stores/alertStore";
import { useMapStore } from "@/stores/mapStore";
import { speakAlert } from "@/lib/elevenlabs";
import { AlertTriangle, Shield, Volume2, X } from "lucide-react";

interface RedAlertSequenceProps {
  onComplete?: () => void;
}

const DEMO_INCIDENT = {
  segment: "MUM-DEL-KM402",
  location: [74.5, 22.0] as [number, number],
  type: "BOULDER_OBSTRUCTION",
  confidence: 97.3,
  affectedTrains: 6,
  passengersProtected: 1247,
  delayPrevented: "4.2 hours",
};

type Stage = "idle" | "vignette" | "detection" | "classification" | "alert" | "voice" | "reroute" | "uav" | "resolution";

export function RedAlertSequence({ onComplete }: RedAlertSequenceProps) {
  const { redAlertActive, dismissRedAlert, activeAlertId } = useAlertStore();
  const { flyTo } = useMapStore();
  const containerRef = useRef<HTMLDivElement>(null);
  const timelineRef = useRef<gsap.core.Timeline | null>(null);
  const [stage, setStage] = useState<Stage>("idle");
  const [counter, setCounter] = useState(0);
  const [confidence, setConfidence] = useState(0);

  const runSequence = useCallback(() => {
    if (!containerRef.current) return;

    const tl = gsap.timeline({
      onComplete: () => {
        setTimeout(() => {
          onComplete?.();
        }, 3000);
      },
    });
    timelineRef.current = tl;

    // Stage 1: Vignette darkens
    tl.call(() => setStage("vignette"), [], 0);

    // Stage 2: Detection — map zooms to incident
    tl.call(() => {
      setStage("detection");
      flyTo(DEMO_INCIDENT.location, 12);
    }, [], 0.8);

    // Stage 3: Classification — spectrogram spike, confidence counter
    tl.call(() => {
      setStage("classification");
      gsap.to({ val: 0 }, {
        val: DEMO_INCIDENT.confidence,
        duration: 1.2,
        ease: "power2.out",
        onUpdate() { setConfidence(Math.round(this.targets()[0].val * 10) / 10); },
      });
    }, [], 2.5);

    // Stage 4: Alert — track turns red
    tl.call(() => setStage("alert"), [], 4.5);

    // Stage 5: Voice alert
    tl.call(() => {
      setStage("voice");
      speakAlert(
        `Critical alert. Boulder obstruction detected at kilometer 402 on the Mumbai-Delhi corridor. Confidence ${DEMO_INCIDENT.confidence} percent. ${DEMO_INCIDENT.affectedTrains} trains rerouting.`
      );
    }, [], 5.5);

    // Stage 6: Reroute animation
    tl.call(() => setStage("reroute"), [], 8);

    // Stage 7: UAV dispatch
    tl.call(() => setStage("uav"), [], 10.5);

    // Stage 8: Resolution — passengers protected counter
    tl.call(() => {
      setStage("resolution");
      gsap.to({ val: 0 }, {
        val: DEMO_INCIDENT.passengersProtected,
        duration: 2,
        ease: "power2.out",
        onUpdate() { setCounter(Math.round(this.targets()[0].val)); },
      });
    }, [], 12.5);
  }, [flyTo, onComplete]);

  useEffect(() => {
    if (redAlertActive) {
      runSequence();
    } else {
      timelineRef.current?.kill();
      setStage("idle");
      setCounter(0);
      setConfidence(0);
    }
    return () => { timelineRef.current?.kill(); };
  }, [redAlertActive, runSequence]);

  if (!redAlertActive) return null;

  const stageIndex = ["idle", "vignette", "detection", "classification", "alert", "voice", "reroute", "uav", "resolution"].indexOf(stage);

  return (
    <AnimatePresence>
      <motion.div
        ref={containerRef}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 pointer-events-none"
      >
        {/* Vignette overlay */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: stageIndex >= 1 ? 1 : 0 }}
          transition={{ duration: 0.6 }}
          className="absolute inset-0 pointer-events-none"
          style={{
            background: "radial-gradient(ellipse at center, transparent 30%, rgba(255,69,58,0.08) 70%, rgba(255,69,58,0.15) 100%)",
          }}
        />

        {/* Screen edge pulse */}
        {stageIndex >= 4 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: [0, 0.4, 0] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="absolute inset-0 pointer-events-none"
            style={{ boxShadow: "inset 0 0 80px rgba(255,69,58,0.15)" }}
          />
        )}

        {/* Detection card */}
        <AnimatePresence>
          {stageIndex >= 2 && stageIndex < 8 && (
            <motion.div
              initial={{ y: -60, opacity: 0, scale: 0.95 }}
              animate={{ y: 0, opacity: 1, scale: 1 }}
              exit={{ y: -60, opacity: 0 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="absolute top-4 left-1/2 -translate-x-1/2 pointer-events-auto"
            >
              <div className="glass rounded-2xl px-6 py-4 glow-red min-w-[480px]">
                <div className="flex items-center gap-4">
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#ff453a]/10">
                    <AlertTriangle className="h-5 w-5 text-[#ff453a] animate-pulse" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-[14px] font-semibold text-[#ff453a]">RED ALERT</span>
                      <span className="text-white/20">·</span>
                      <span className="text-[13px] text-white/60">{DEMO_INCIDENT.type.replace("_", " ")}</span>
                    </div>
                    <div className="mt-0.5 flex items-center gap-3 text-[11px] text-white/30">
                      <span className="font-mono">{DEMO_INCIDENT.segment}</span>
                      {stageIndex >= 3 && (
                        <span className="font-mono text-[#ff453a]">{confidence}% confidence</span>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => dismissRedAlert()}
                    className="rounded-lg p-1.5 text-white/20 hover:bg-white/[0.05] hover:text-white/40 transition-all pointer-events-auto"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>

                {/* Stage progress */}
                <div className="mt-3 flex gap-1">
                  {["Detect", "Classify", "Alert", "Voice", "Reroute", "UAV", "Resolve"].map((s, i) => (
                    <div key={s} className="flex-1">
                      <div className={`h-[3px] rounded-full transition-all duration-500 ${
                        i + 2 <= stageIndex ? "bg-[#ff453a]" : "bg-white/[0.06]"
                      }`} />
                      <p className={`mt-1 text-center text-[8px] font-medium transition-colors ${
                        i + 2 <= stageIndex ? "text-[#ff453a]/60" : "text-white/15"
                      }`}>{s}</p>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Voice indicator */}
        <AnimatePresence>
          {stage === "voice" && (
            <motion.div
              initial={{ x: 60, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 60, opacity: 0 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="absolute top-24 right-4 pointer-events-auto"
            >
              <div className="glass rounded-xl px-4 py-3 flex items-center gap-3">
                <Volume2 className="h-4 w-4 text-[#ff453a] animate-pulse" />
                <span className="text-[12px] text-white/50">Voice alert active</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Reroute indicator */}
        <AnimatePresence>
          {stage === "reroute" && (
            <motion.div
              initial={{ x: 60, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 60, opacity: 0 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="absolute top-24 right-4 pointer-events-auto"
            >
              <div className="glass rounded-xl px-4 py-3 glow-blue">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-[#0a84ff] animate-pulse" />
                  <span className="font-mono text-[12px] text-[#0a84ff]">Recalculating Kinetic Flow...</span>
                </div>
                <p className="mt-1 text-[11px] text-white/30">
                  Rerouting {DEMO_INCIDENT.affectedTrains} trains via Jaipur corridor
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* UAV dispatch */}
        <AnimatePresence>
          {stage === "uav" && (
            <motion.div
              initial={{ x: 60, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 60, opacity: 0 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="absolute top-24 right-4 pointer-events-auto"
            >
              <div className="glass rounded-xl px-4 py-3">
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-[#30d158]" />
                  <span className="text-[12px] text-white/50">UAV-B4 dispatched</span>
                </div>
                <p className="mt-1 font-mono text-[11px] text-white/25">ETA: 4m 32s · Battery: 94%</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Resolution counter */}
        <AnimatePresence>
          {stage === "resolution" && (
            <motion.div
              initial={{ y: 40, opacity: 0, scale: 0.9 }}
              animate={{ y: 0, opacity: 1, scale: 1 }}
              exit={{ y: 40, opacity: 0 }}
              transition={{ type: "spring", stiffness: 200, damping: 25 }}
              className="absolute bottom-8 left-1/2 -translate-x-1/2 pointer-events-auto"
            >
              <div className="glass rounded-2xl px-8 py-6 text-center glow-green min-w-[400px]">
                <p className="text-[11px] font-medium tracking-widest text-[#30d158]/60 uppercase">
                  Passengers Protected
                </p>
                <p className="mt-2 font-display text-[48px] font-bold tracking-[-0.04em] text-[#30d158]">
                  {counter.toLocaleString()}
                </p>
                <p className="mt-1 text-[13px] text-white/30">
                  Delay prevented: {DEMO_INCIDENT.delayPrevented}
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </AnimatePresence>
  );
}
