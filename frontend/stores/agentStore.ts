import { create } from "zustand";

export type AgentId =
  | "acoustic_monitor"
  | "weather_agent"
  | "routing_coordinator"
  | "emergency_agent"
  | "incident_reporter"
  | "supervisor_agent";

export type AgentStatus = "active" | "idle" | "processing" | "error" | "offline";

export interface AgentState {
  id: AgentId;
  name: string;
  status: AgentStatus;
  lastAction?: string;
  confidence?: number;
  reasoning?: string;
  decisionsToday: number;
  avgLatencyMs: number;
  lastUpdated: string;
}

export interface AgentDecision {
  id: string;
  agentId: AgentId;
  action: string;
  reasoning: string;
  confidence: number;
  severity: "info" | "warning" | "critical";
  timestamp: string;
}

interface AgentStore {
  agents: Record<AgentId, AgentState>;
  decisions: AgentDecision[];
  streamingAgentId: AgentId | null;
  streamingTokens: string;

  updateAgent: (id: AgentId, update: Partial<AgentState>) => void;
  addDecision: (decision: AgentDecision) => void;
  setStreaming: (agentId: AgentId | null, tokens?: string) => void;
  appendStreamToken: (token: string) => void;
}

const defaultAgent = (id: AgentId, name: string): AgentState => ({
  id,
  name,
  status: "idle",
  decisionsToday: 0,
  avgLatencyMs: 0,
  lastUpdated: new Date().toISOString(),
});

export const useAgentStore = create<AgentStore>((set) => ({
  agents: {
    acoustic_monitor: defaultAgent("acoustic_monitor", "Acoustic Monitor"),
    weather_agent: defaultAgent("weather_agent", "Weather Agent"),
    routing_coordinator: defaultAgent("routing_coordinator", "Routing Coordinator"),
    emergency_agent: defaultAgent("emergency_agent", "Emergency Agent"),
    incident_reporter: defaultAgent("incident_reporter", "Incident Reporter"),
    supervisor_agent: defaultAgent("supervisor_agent", "Supervisor Agent"),
  },
  decisions: [],
  streamingAgentId: null,
  streamingTokens: "",

  updateAgent: (id, update) =>
    set((s) => ({
      agents: {
        ...s.agents,
        [id]: { ...s.agents[id], ...update, lastUpdated: new Date().toISOString() },
      },
    })),

  addDecision: (decision) =>
    set((s) => ({
      decisions: [decision, ...s.decisions].slice(0, 200),
    })),

  setStreaming: (agentId, tokens = "") =>
    set({ streamingAgentId: agentId, streamingTokens: tokens }),

  appendStreamToken: (token) =>
    set((s) => ({ streamingTokens: s.streamingTokens + token })),
}));
