"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

interface TrackSegment3DProps {
  length?: number;
  health?: number;
  showCrack?: boolean;
}

export function TrackSegment3D({ length = 12, health = 80, showCrack = false }: TrackSegment3DProps) {
  const crackRef = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    if (crackRef.current && showCrack) {
      crackRef.current.material = crackRef.current.material as THREE.MeshStandardMaterial;
      (crackRef.current.material as THREE.MeshStandardMaterial).emissiveIntensity =
        0.5 + Math.sin(clock.elapsedTime * 3) * 0.3;
    }
  });

  const railColor = health < 40 ? "#883333" : health < 60 ? "#886633" : "#888888";

  return (
    <group>
      <mesh position={[-0.75, 0.1, 0]}>
        <boxGeometry args={[0.08, 0.12, length]} />
        <meshStandardMaterial color={railColor} metalness={0.8} roughness={0.3} />
      </mesh>
      <mesh position={[0.75, 0.1, 0]}>
        <boxGeometry args={[0.08, 0.12, length]} />
        <meshStandardMaterial color={railColor} metalness={0.8} roughness={0.3} />
      </mesh>

      {Array.from({ length: Math.floor(length / 0.6) }).map((_, i) => (
        <mesh key={i} position={[0, 0, -(length / 2) + 0.3 + i * 0.6]}>
          <boxGeometry args={[2, 0.08, 0.15]} />
          <meshStandardMaterial color="#4a3728" />
        </mesh>
      ))}

      <mesh position={[0, -0.05, 0]}>
        <boxGeometry args={[2.5, 0.1, length]} />
        <meshStandardMaterial color="#555" roughness={0.9} />
      </mesh>

      {showCrack && (
        <mesh ref={crackRef} position={[0.3, 0.12, 1.5]} rotation={[0, 0.3, 0]}>
          <boxGeometry args={[0.02, 0.08, 0.8]} />
          <meshStandardMaterial color="#ff453a" emissive="#ff453a" emissiveIntensity={0.5} transparent opacity={0.6} />
        </mesh>
      )}
    </group>
  );
}
