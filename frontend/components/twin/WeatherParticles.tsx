"use client";

import { useRef, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

interface WeatherParticlesProps {
  type: "rain" | "snow" | "fog";
  intensity?: number;
}

export function WeatherParticles({ type, intensity = 1 }: WeatherParticlesProps) {
  const ref = useRef<THREE.Points>(null);
  const count = type === "fog" ? 200 : Math.floor(500 * intensity);

  const positions = useMemo(() => {
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      arr[i * 3] = (Math.random() - 0.5) * 10;
      arr[i * 3 + 1] = Math.random() * 8;
      arr[i * 3 + 2] = (Math.random() - 0.5) * 10;
    }
    return arr;
  }, [count]);

  useFrame(() => {
    if (!ref.current) return;
    const pos = ref.current.geometry.attributes.position;
    const arr = pos.array as Float32Array;

    for (let i = 0; i < count; i++) {
      if (type === "rain") {
        arr[i * 3 + 1] -= 0.15 * intensity;
        if (arr[i * 3 + 1] < 0) arr[i * 3 + 1] = 8;
      } else if (type === "snow") {
        arr[i * 3 + 1] -= 0.03 * intensity;
        arr[i * 3] += Math.sin(arr[i * 3 + 1] * 2) * 0.005;
        if (arr[i * 3 + 1] < 0) arr[i * 3 + 1] = 8;
      } else {
        arr[i * 3] += Math.sin(arr[i * 3 + 1] + performance.now() * 0.001) * 0.003;
      }
    }
    pos.needsUpdate = true;
  });

  const color = type === "rain" ? "#6688cc" : type === "snow" ? "#ffffff" : "#aaaaaa";
  const size = type === "rain" ? 0.03 : type === "snow" ? 0.06 : 0.15;
  const opacity = type === "fog" ? 0.1 : 0.4;

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} count={count} />
      </bufferGeometry>
      <pointsMaterial color={color} size={size} transparent opacity={opacity} sizeAttenuation />
    </points>
  );
}
