"use client";

import { motion } from "framer-motion";
import { CloudRain, Cloud, Sun, Thermometer, Wind, Droplets, AlertTriangle } from "lucide-react";

const spring = { type: "spring" as const, stiffness: 300, damping: 30 };

const WEATHER_DATA = [
  { route: "MUM-DEL", condition: "Heavy Rain", icon: CloudRain, risk: 80, temp: 28, wind: 42, humidity: 92, color: "#ff453a" },
  { route: "KON-RLY", condition: "Flood Risk", icon: Droplets, risk: 72, temp: 26, wind: 38, humidity: 95, color: "#ff453a" },
  { route: "CHN-KOL", condition: "Moderate Rain", icon: CloudRain, risk: 45, temp: 31, wind: 22, humidity: 78, color: "#ffd60a" },
  { route: "DEL-JAI", condition: "Heat Stress", icon: Thermometer, risk: 35, temp: 44, wind: 15, humidity: 20, color: "#ffd60a" },
  { route: "KOL-GHY", condition: "Fog", icon: Cloud, risk: 30, temp: 24, wind: 8, humidity: 88, color: "#ffd60a" },
  { route: "BLR-TVC", condition: "Clear", icon: Sun, risk: 5, temp: 29, wind: 12, humidity: 65, color: "#30d158" },
];

interface WeatherPanelProps {
  compact?: boolean;
}

export function WeatherPanel({ compact = false }: WeatherPanelProps) {
  const items = compact ? WEATHER_DATA.slice(0, 3) : WEATHER_DATA;

  return (
    <div className="space-y-2">
      {items.map((w, i) => {
        const Icon = w.icon;
        return (
          <motion.div
            key={w.route}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05, ...spring }}
            className="rounded-xl bg-white/[0.02] p-3 ring-1 ring-white/[0.03] transition-colors hover:bg-white/[0.04]"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg" style={{ backgroundColor: `${w.color}12` }}>
                  <Icon className="h-4 w-4" style={{ color: w.color }} />
                </div>
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="font-mono text-[11px] font-semibold text-white/60">{w.route}</span>
                    <span className="text-[10px] text-white/30">{w.condition}</span>
                  </div>
                  {!compact && (
                    <div className="mt-0.5 flex items-center gap-2 text-[9px] text-white/20">
                      <span>{w.temp}°C</span>
                      <span>Wind: {w.wind}km/h</span>
                      <span>Humidity: {w.humidity}%</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2">
                {w.risk >= 60 && <AlertTriangle className="h-3 w-3 text-[#ff453a]/50" />}
                <div className="text-right">
                  <span className="font-mono text-[13px] font-bold" style={{ color: w.color }}>{w.risk}%</span>
                  <p className="text-[8px] text-white/20">risk</p>
                </div>
              </div>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
