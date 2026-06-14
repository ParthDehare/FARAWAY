"use client";

import { useRef, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import * as d3 from "d3";
import { useAgentStore, type AgentId, type AgentState } from "@/stores/agentStore";
import {
  Activity, CloudRain, Route, AlertTriangle, FileText, Shield,
  ChevronDown, Zap,
} from "lucide-react";

const spring = { type: "spring" as const, stiffness: 300, damping: 30 };

const AGENT_META: Record<AgentId, { icon: React.ElementType; color: string; label: string }> = {
  acoustic_monitor: { icon: Activity, color: "#30d158", label: "Acoustic" },
  weather_agent: { icon: CloudRain, color: "#0a84ff", label: "Weather" },
  routing_coordinator: { icon: Route, color: "#ffd60a", label: "Routing" },
  emergency_agent: { icon: AlertTriangle, color: "#ff453a", label: "Emergency" },
  incident_reporter: { icon: FileText, color: "#bf5af2", label: "Reporter" },
  supervisor_agent: { icon: Shield, color: "#5e5ce6", label: "Supervisor" },
};

// GNN graph data for D3 visualization
const GNN_NODES = [
  { id: "MUM", x: 80, y: 340 }, { id: "PUN", x: 160, y: 270 },
  { id: "NAS", x: 200, y: 210 }, { id: "BPL", x: 280, y: 150 },
  { id: "AGR", x: 340, y: 110 }, { id: "DEL", x: 380, y: 55 },
  { id: "JAI", x: 260, y: 90 }, { id: "ADI", x: 60, y: 210 },
  { id: "SUR", x: 120, y: 290 },
];
const GNN_EDGES = [
  { source: "MUM", target: "PUN", status: "normal" },
  { source: "PUN", target: "NAS", status: "normal" },
  { source: "NAS", target: "BPL", status: "blocked" },
  { source: "BPL", target: "AGR", status: "normal" },
  { source: "AGR", target: "DEL", status: "normal" },
  { source: "MUM", target: "SUR", status: "rerouted" },
  { source: "SUR", target: "ADI", status: "rerouted" },
  { source: "ADI", target: "JAI", status: "rerouted" },
  { source: "JAI", target: "DEL", status: "rerouted" },
  { source: "BPL", target: "JAI", status: "normal" },
];

interface AgentBrainPanelProps {
  compact?: boolean;
  showGnn?: boolean;
}

export function AgentBrainPanel({ compact = false, showGnn = true }: AgentBrainPanelProps) {
  const { agents, decisions, streamingAgentId, streamingTokens } = useAgentStore();
  const [expanded, setExpanded] = useState<AgentId | null>(null);
  const gnnRef = useRef<SVGSVGElement>(null);

  // D3 GNN visualization
  useEffect(() => {
    if (!showGnn || !gnnRef.current) return;
    const svg = d3.select(gnnRef.current);
    svg.selectAll("*").remove();

    const nodeMap = Object.fromEntries(GNN_NODES.map((n) => [n.id, n]));

    // Edges
    const edgeGroup = svg.append("g");
    GNN_EDGES.forEach((edge, i) => {
      const source = nodeMap[edge.source];
      const target = nodeMap[edge.target];
      const color = edge.status === "blocked" ? "#ff453a" : edge.status === "rerouted" ? "#0a84ff" : "#5e5ce6";

      const line = edgeGroup.append("line")
        .attr("x1", source.x).attr("y1", source.y)
        .attr("x2", source.x).attr("y2", source.y)
        .attr("stroke", color)
        .attr("stroke-width", edge.status === "blocked" ? 2.5 : edge.status === "rerouted" ? 2 : 1)
        .attr("opacity", edge.status === "normal" ? 0.15 : 0.5);

      if (edge.status === "blocked") {
        line.attr("stroke-dasharray", "6,4");
      }

      line.transition().duration(800).delay(i * 80)
        .attr("x2", target.x).attr("y2", target.y);

      // Animated dot on rerouted edges
      if (edge.status === "rerouted") {
        const dot = edgeGroup.append("circle")
          .attr("r", 3).attr("fill", "#0a84ff")
          .attr("cx", source.x).attr("cy", source.y)
          .attr("opacity", 0);

        function animateDot() {
          dot.attr("cx", source.x).attr("cy", source.y).attr("opacity", 0.8)
            .transition().duration(2500).ease(d3.easeLinear)
            .attr("cx", target.x).attr("cy", target.y).attr("opacity", 0)
            .on("end", animateDot);
        }
        setTimeout(animateDot, i * 300 + 800);
      }
    });

    // Nodes
    const nodeGroup = svg.append("g");
    GNN_NODES.forEach((node) => {
      nodeGroup.append("circle")
        .attr("cx", node.x).attr("cy", node.y).attr("r", 18)
        .attr("fill", "#1c1c1e").attr("stroke", "rgba(255,255,255,0.06)").attr("stroke-width", 1);

      nodeGroup.append("text")
        .attr("x", node.x).attr("y", node.y + 1)
        .attr("text-anchor", "middle").attr("dominant-baseline", "middle")
        .attr("fill", "rgba(255,255,255,0.5)")
        .attr("font-family", "var(--font-mono)").attr("font-size", "8px").attr("font-weight", "600")
        .text(node.id);
    });
  }, [showGnn]);

  const agentList = Object.values(agents);

  return (
    <div className="space-y-3">
      {/* Agent status grid */}
      <div className={compact ? "grid grid-cols-3 gap-2" : "grid grid-cols-6 gap-2"}>
        {agentList.map((agent) => {
          const meta = AGENT_META[agent.id];
          const Icon = meta.icon;
          const isStreaming = streamingAgentId === agent.id;

          return (
            <motion.button
              key={agent.id}
              whileHover={{ scale: 1.04, transition: spring }}
              whileTap={{ scale: 0.97 }}
              onClick={() => setExpanded(expanded === agent.id ? null : agent.id)}
              className={`flex flex-col items-center gap-1.5 rounded-xl p-3 transition-all duration-300 ring-1 ${
                expanded === agent.id
                  ? "bg-white/[0.05] ring-white/[0.08]"
                  : "bg-white/[0.02] ring-white/[0.03] hover:bg-white/[0.04]"
              }`}
            >
              <div className="relative">
                <div className="flex h-8 w-8 items-center justify-center rounded-[10px]" style={{ backgroundColor: `${meta.color}12` }}>
                  <Icon className="h-[14px] w-[14px]" style={{ color: meta.color }} />
                </div>
                {isStreaming && (
                  <span className="absolute -top-0.5 -right-0.5 flex h-2 w-2">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#0a84ff] opacity-60" />
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-[#0a84ff]" />
                  </span>
                )}
              </div>
              <span className="text-[10px] font-medium text-white/50">{meta.label}</span>
              <span className={`font-mono text-[8px] ${
                agent.status === "active" ? "text-[#30d158]/60"
                : agent.status === "processing" ? "text-[#0a84ff]/60"
                : agent.status === "error" ? "text-[#ff453a]/60"
                : "text-white/20"
              }`}>
                {agent.status === "active" ? "● Active"
                  : agent.status === "processing" ? "◉ Working"
                  : agent.status === "error" ? "✕ Error"
                  : agent.status === "idle" ? "○ Idle"
                  : "◌ Offline"}
              </span>
            </motion.button>
          );
        })}
      </div>

      {/* Expanded agent detail */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="overflow-hidden"
          >
            <AgentDetail agent={agents[expanded]} isStreaming={streamingAgentId === expanded} streamingTokens={streamingTokens} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* GNN visualization */}
      {showGnn && (
        <div className="glass rounded-2xl overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2.5">
            <span className="text-[12px] font-medium text-white/50">GNN Routing Graph</span>
            <div className="flex items-center gap-3">
              {[
                { label: "Normal", color: "#5e5ce6" },
                { label: "Blocked", color: "#ff453a" },
                { label: "Rerouted", color: "#0a84ff" },
              ].map((l) => (
                <div key={l.label} className="flex items-center gap-1">
                  <span className="h-[5px] w-[5px] rounded-full" style={{ backgroundColor: l.color }} />
                  <span className="text-[9px] text-white/20">{l.label}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="divider" />
          <div className="bg-[#0c0c0e] p-2">
            <svg ref={gnnRef} viewBox="0 0 460 400" className="w-full" style={{ height: "280px" }} />
          </div>
        </div>
      )}

      {/* Recent decisions */}
      {!compact && decisions.length > 0 && (
        <div className="glass rounded-2xl overflow-hidden">
          <div className="px-4 py-2.5">
            <span className="text-[12px] font-medium text-white/50">Recent Decisions</span>
          </div>
          <div className="divider" />
          {decisions.slice(0, 5).map((d, i) => {
            const meta = AGENT_META[d.agentId];
            return (
              <div key={d.id} className="flex items-center gap-3 px-4 py-2.5 transition-colors hover:bg-white/[0.02]">
                <div className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: meta.color }} />
                <span className="text-[11px] text-white/40 flex-1 truncate">{d.action}</span>
                <span className="font-mono text-[10px] text-white/20">{d.confidence}%</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function AgentDetail({ agent, isStreaming, streamingTokens }: { agent: AgentState; isStreaming: boolean; streamingTokens: string }) {
  const meta = AGENT_META[agent.id];

  return (
    <div className="glass rounded-xl p-4 space-y-3">
      <div className="grid grid-cols-4 gap-2">
        {[
          { label: "Decisions", value: agent.decisionsToday.toString() },
          { label: "Avg Latency", value: `${agent.avgLatencyMs}ms` },
          { label: "Confidence", value: agent.confidence ? `${agent.confidence}%` : "—" },
          { label: "Last Update", value: new Date(agent.lastUpdated).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: false }) },
        ].map((m) => (
          <div key={m.label} className="rounded-lg bg-white/[0.02] px-2.5 py-2 ring-1 ring-white/[0.03]">
            <p className="text-[9px] text-white/20">{m.label}</p>
            <p className="mt-0.5 font-mono text-[12px] font-medium text-white/50">{m.value}</p>
          </div>
        ))}
      </div>

      {agent.lastAction && (
        <div className="rounded-lg bg-white/[0.02] p-3 ring-1 ring-white/[0.03]">
          <p className="text-[9px] font-medium uppercase tracking-wide" style={{ color: `${meta.color}99` }}>Last Action</p>
          <p className="mt-1 text-[11px] text-white/40">{agent.lastAction}</p>
        </div>
      )}

      {agent.reasoning && (
        <div className="rounded-lg bg-white/[0.02] p-3 ring-1 ring-white/[0.03]">
          <p className="text-[9px] font-medium text-[#0a84ff]/60 uppercase tracking-wide">Reasoning</p>
          <p className="mt-1 text-[11px] leading-relaxed text-white/30">{agent.reasoning}</p>
        </div>
      )}

      {isStreaming && (
        <div className="rounded-lg bg-[#0a84ff]/[0.03] p-3 ring-1 ring-[#0a84ff]/10">
          <div className="flex items-center gap-1.5 mb-1">
            <Zap className="h-3 w-3 text-[#0a84ff] animate-pulse" />
            <span className="text-[9px] font-medium text-[#0a84ff]/60 uppercase tracking-wide">Streaming</span>
          </div>
          <p className="font-mono text-[11px] text-white/40">{streamingTokens}<span className="animate-pulse">▌</span></p>
        </div>
      )}
    </div>
  );
}
