"use client";

import { Suspense, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, PerspectiveCamera, Environment, Text } from "@react-three/drei";
import { motion } from "framer-motion";
import { Eye, CloudRain, Sun, Thermometer } from "lucide-react";

const spring = { type: "spring" as const, stiffness: 300, damping: 30 };

type SimMode = "normal" | "rain" | "heat";

function RailTrack({ health, mode }: { health: number; mode: SimMode }) {
  const healthColor = health < 40 ? "#ff453a" : health < 60 ? "#ffd60a" : "#30d158";

  return (
    <group>
      {/* Left rail */}
      <mesh position={[-0.75, 0.1, 0]}>
        <boxGeometry args={[0.08, 0.12, 12]} />
        <meshStandardMaterial color="#888" metalness={0.8} roughness={0.3} />
      </mesh>
      {/* Right rail */}
      <mesh position={[0.75, 0.1, 0]}>
        <boxGeometry args={[0.08, 0.12, 12]} />
        <meshStandardMaterial color="#888" metalness={0.8} roughness={0.3} />
      </mesh>
      {/* Sleepers */}
      {Array.from({ length: 20 }).map((_, i) => (
        <mesh key={i} position={[0, 0, -5.5 + i * 0.6]}>
          <boxGeometry args={[2, 0.08, 0.15]} />
          <meshStandardMaterial color="#4a3728" />
        </mesh>
      ))}
      {/* Ballast bed */}
      <mesh position={[0, -0.05, 0]}>
        <boxGeometry args={[2.5, 0.1, 12]} />
        <meshStandardMaterial color="#555" roughness={0.9} />
      </mesh>
      {/* Health indicator glow */}
      {health < 60 && (
        <mesh position={[0, 0.2, 0]}>
          <boxGeometry args={[1.8, 0.02, 2]} />
          <meshStandardMaterial color={healthColor} transparent opacity={0.15} emissive={healthColor} emissiveIntensity={0.5} />
        </mesh>
      )}
      {/* Crack visualization */}
      {health < 50 && (
        <mesh position={[0.3, 0.12, 1.5]} rotation={[0, 0.3, 0]}>
          <boxGeometry args={[0.02, 0.08, 0.8]} />
          <meshStandardMaterial color="#ff453a" emissive="#ff453a" emissiveIntensity={0.8} transparent opacity={0.6} />
        </mesh>
      )}
    </group>
  );
}

interface DigitalTwinViewerProps {
  segmentId?: string;
  health?: number;
  className?: string;
}

export function DigitalTwinViewer({ segmentId = "KM-402", health = 34, className = "" }: DigitalTwinViewerProps) {
  const [mode, setMode] = useState<SimMode>("normal");

  return (
    <div className={`glass rounded-2xl overflow-hidden ${className}`}>
      <div className="flex items-center justify-between px-4 py-2.5">
        <div className="flex items-center gap-2">
          <Eye className="h-3.5 w-3.5 text-[#bf5af2]" />
          <span className="text-[12px] font-medium text-white/50">Digital Twin</span>
          <span className="font-mono text-[10px] text-white/20">{segmentId}</span>
        </div>
        <div className="flex gap-1">
          {([
            { m: "normal" as SimMode, icon: Sun, label: "Normal" },
            { m: "rain" as SimMode, icon: CloudRain, label: "Rain" },
            { m: "heat" as SimMode, icon: Thermometer, label: "Heat" },
          ]).map((opt) => (
            <button
              key={opt.m}
              onClick={() => setMode(opt.m)}
              className={`flex items-center gap-1 rounded-md px-2 py-0.5 text-[9px] font-medium transition-all ${
                mode === opt.m
                  ? "bg-[#bf5af2]/15 text-[#bf5af2] ring-1 ring-[#bf5af2]/15"
                  : "bg-white/[0.03] text-white/25 hover:text-white/40"
              }`}
            >
              <opt.icon className="h-2.5 w-2.5" />
              {opt.label}
            </button>
          ))}
        </div>
      </div>
      <div className="divider" />
      <div className="h-[280px] bg-[#0c0c0e]">
        <Suspense fallback={
          <div className="flex h-full items-center justify-center">
            <span className="text-[11px] text-white/20">Loading 3D scene...</span>
          </div>
        }>
          <Canvas>
            <PerspectiveCamera makeDefault position={[3, 2.5, 5]} fov={45} />
            <OrbitControls enablePan={false} maxPolarAngle={Math.PI / 2.2} minDistance={3} maxDistance={12} />
            <ambientLight intensity={0.3} />
            <directionalLight position={[5, 8, 5]} intensity={mode === "heat" ? 1.2 : 0.7} color={mode === "heat" ? "#ffaa44" : "#ffffff"} />
            {mode === "rain" && <directionalLight position={[-3, 4, -2]} intensity={0.3} color="#4488ff" />}
            <RailTrack health={health} mode={mode} />
            <mesh position={[0, -0.15, 0]} rotation={[-Math.PI / 2, 0, 0]}>
              <planeGeometry args={[20, 20]} />
              <meshStandardMaterial color={mode === "rain" ? "#2a3a28" : "#3a3a2e"} />
            </mesh>
          </Canvas>
        </Suspense>
      </div>
      <div className="flex items-center justify-between px-4 py-2">
        <span className="text-[10px] text-white/20">Health Index</span>
        <span className={`font-mono text-[14px] font-bold ${health < 40 ? "text-[#ff453a]" : health < 60 ? "text-[#ffd60a]" : "text-[#30d158]"}`}>
          {health}/100
        </span>
      </div>
    </div>
  );
}
