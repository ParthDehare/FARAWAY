import { useEffect, useRef, useCallback } from "react";
import { getSocket } from "@/lib/socket";
import { useAgentStore, type AgentId } from "@/stores/agentStore";

export function useAgentStream() {
  const { setStreaming, appendStreamToken, addDecision, updateAgent } = useAgentStore();
  const socketRef = useRef(getSocket());

  useEffect(() => {
    const socket = socketRef.current;

    socket.on("agent:stream:start", (data: { agentId: AgentId }) => {
      setStreaming(data.agentId);
      updateAgent(data.agentId, { status: "processing" });
    });

    socket.on("agent:stream:token", (data: { token: string }) => {
      appendStreamToken(data.token);
    });

    socket.on("agent:stream:end", (data: { agentId: AgentId; decision: any }) => {
      setStreaming(null);
      updateAgent(data.agentId, { status: "active" });
      if (data.decision) addDecision(data.decision);
    });

    return () => {
      socket.off("agent:stream:start");
      socket.off("agent:stream:token");
      socket.off("agent:stream:end");
    };
  }, [setStreaming, appendStreamToken, addDecision, updateAgent]);

  const invokeAgent = useCallback((agentId: AgentId, payload?: unknown) => {
    socketRef.current.emit("agent:invoke", { agentId, payload });
  }, []);

  return { invokeAgent };
}
