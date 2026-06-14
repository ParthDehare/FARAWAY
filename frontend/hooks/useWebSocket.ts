import { useEffect, useRef, useState, useCallback } from "react";
import { connectSocket, disconnectSocket } from "@/lib/socket";
import { useAlertStore } from "@/stores/alertStore";
import { useAgentStore } from "@/stores/agentStore";
import { useTrainStore } from "@/stores/trainStore";
import type { Socket } from "socket.io-client";

type ConnectionStatus = "connecting" | "connected" | "disconnected" | "error";

export function useWebSocket() {
  const [status, setStatus] = useState<ConnectionStatus>("disconnected");
  const socketRef = useRef<Socket | null>(null);
  const addAlert = useAlertStore((s) => s.addAlert);
  const triggerRedAlert = useAlertStore((s) => s.triggerRedAlert);
  const updateAgent = useAgentStore((s) => s.updateAgent);
  const addDecision = useAgentStore((s) => s.addDecision);
  const updateTrainPosition = useTrainStore((s) => s.updateTrainPosition);

  useEffect(() => {
    setStatus("connecting");
    const socket = connectSocket();
    socketRef.current = socket;

    // Ensure automatic reconnection is enabled
    socket.io.reconnection(true);
    socket.io.reconnectionAttempts(Infinity);
    socket.io.reconnectionDelay(1000);

    socket.on("connect", () => setStatus("connected"));
    socket.on("disconnect", () => setStatus("disconnected"));
    socket.on("connect_error", () => setStatus("error"));

    // EXACT EVENT: anomaly:detected
    socket.on("anomaly:detected", (data) => {
      addAlert(data);
      if (data.severity === "critical") {
        triggerRedAlert(data.id);
      }
    });

    // EXACT EVENT: agent:decision
    socket.on("agent:decision", (data) => {
      addDecision(data);
      if (data.agentId) {
          updateAgent(data.agentId, {
            status: "active",
            lastAction: data.action || data.decision?.action,
            confidence: data.confidence || data.decision?.confidence,
          });
      }
    });

    // EXACT EVENT: train:position
    socket.on("train:position", (data) => {
      updateTrainPosition(data);
    });

    return () => {
      socket.removeAllListeners();
      disconnectSocket();
      setStatus("disconnected");
    };
  }, [addAlert, triggerRedAlert, updateAgent, addDecision, updateTrainPosition]);

  const emit = useCallback((event: string, data?: unknown) => {
    socketRef.current?.emit(event, data);
  }, []);

  return { status, emit, socket: socketRef };
}
