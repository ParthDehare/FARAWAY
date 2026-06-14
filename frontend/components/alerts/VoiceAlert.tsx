"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Volume2, VolumeX } from "lucide-react";
import { useAlertStore } from "@/stores/alertStore";
import { speakAlert } from "@/lib/elevenlabs";

export function VoiceAlert() {
  const { redAlertActive, alerts } = useAlertStore();
  const [muted, setMuted] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const spokenRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (muted) return;

    const criticalAlerts = alerts.filter(
      (a) => a.severity === "critical" && !a.acknowledged && !spokenRef.current.has(a.id)
    );

    if (criticalAlerts.length === 0) return;

    const alert = criticalAlerts[0];
    spokenRef.current.add(alert.id);

    setSpeaking(true);
    speakAlert(
      `Critical alert. ${alert.title}. ${alert.description}`
    ).finally(() => setSpeaking(false));
  }, [alerts, muted]);

  return (
    <AnimatePresence>
      {(speaking || redAlertActive) && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
          className="flex items-center gap-2"
        >
          <button
            onClick={() => setMuted(!muted)}
            className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-medium transition-all ${
              muted
                ? "bg-white/[0.04] text-white/30 ring-1 ring-white/[0.04]"
                : "bg-[#ff453a]/10 text-[#ff453a] ring-1 ring-[#ff453a]/10"
            }`}
          >
            {muted ? <VolumeX className="h-3 w-3" /> : <Volume2 className="h-3 w-3 animate-pulse" />}
            {muted ? "Muted" : "Voice Active"}
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
