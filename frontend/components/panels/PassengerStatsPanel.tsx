"use client";

import { motion, useSpring, useTransform } from "framer-motion";
import { Users, Shield, TrendingUp, Clock } from "lucide-react";
import { useTrainStore } from "@/stores/trainStore";
import { useEffect, useState } from "react";

const spring = { type: "spring" as const, stiffness: 300, damping: 30 };

function AnimatedNumber({ value }: { value: number }) {
  const springValue = useSpring(value, { stiffness: 100, damping: 20 });
  
  useEffect(() => {
    springValue.set(value);
  }, [value, springValue]);

  const display = useTransform(springValue, (current) => 
    Math.round(current).toLocaleString()
  );

  return <motion.span>{display}</motion.span>;
}

export function PassengerStatsPanel() {
  const trains = useTrainStore((s) => s.trains);
  const [totalPassengers, setTotalPassengers] = useState(0);

  useEffect(() => {
    let sum = 0;
    Object.values(trains).forEach(t => {
      if (t.passenger_count) sum += t.passenger_count;
    });
    // Add base 8.2M for demo scale, plus our live trains
    setTotalPassengers(8200000 + sum);
  }, [trains]);

  const STATS = [
    { label: "Total Protected", value: "23,412,892", static: true, icon: Shield, color: "#30d158", sub: "today" },
    { label: "Active Passengers", value: totalPassengers, static: false, icon: Users, color: "#0a84ff", sub: "on trains now" },
    { label: "Rerouted", value: "12,847", static: true, icon: TrendingUp, color: "#ffd60a", sub: "this week" },
    { label: "Avg Delay Saved", value: "2.8h", static: true, icon: Clock, color: "#bf5af2", sub: "per incident" },
  ];

  return (
    <div className="grid grid-cols-2 gap-2">
      {STATS.map((stat, i) => {
        const Icon = stat.icon;
        return (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.06, ...spring }}
            className="rounded-xl bg-white/[0.02] p-3 ring-1 ring-white/[0.03]"
          >
            <div className="flex items-center gap-2 mb-2">
              <div className="flex h-6 w-6 items-center justify-center rounded-md" style={{ backgroundColor: `${stat.color}12` }}>
                <Icon className="h-3 w-3" style={{ color: stat.color }} />
              </div>
              <span className="text-[9px] text-white/25 uppercase tracking-wide">{stat.label}</span>
            </div>
            <p className="font-display text-[20px] font-bold tracking-[-0.03em]" style={{ color: stat.color }}>
              {stat.static ? stat.value : <AnimatedNumber value={stat.value as number} />}
            </p>
            <p className="text-[9px] text-white/20">{stat.sub}</p>
          </motion.div>
        );
      })}
    </div>
  );
}
