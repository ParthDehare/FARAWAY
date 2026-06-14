import { create } from "zustand";

export type AlertSeverity = "info" | "warning" | "critical";

export interface Alert {
  id: string;
  title: string;
  description: string;
  severity: AlertSeverity;
  segmentId?: string;
  agentId?: string;
  timestamp: string;
  acknowledged: boolean;
}

interface AlertStore {
  alerts: Alert[];
  redAlertActive: boolean;
  activeAlertId: string | null;

  addAlert: (alert: Omit<Alert, "acknowledged">) => void;
  acknowledgeAlert: (id: string) => void;
  dismissAlert: (id: string) => void;
  clearAll: () => void;
  triggerRedAlert: (alertId: string) => void;
  dismissRedAlert: () => void;
}

export const useAlertStore = create<AlertStore>((set) => ({
  alerts: [],
  redAlertActive: false,
  activeAlertId: null,

  addAlert: (alert) =>
    set((s) => ({
      alerts: [{ ...alert, acknowledged: false }, ...s.alerts].slice(0, 100),
    })),

  acknowledgeAlert: (id) =>
    set((s) => ({
      alerts: s.alerts.map((a) =>
        a.id === id ? { ...a, acknowledged: true } : a
      ),
    })),

  dismissAlert: (id) =>
    set((s) => ({
      alerts: s.alerts.filter((a) => a.id !== id),
    })),

  clearAll: () => set({ alerts: [] }),

  triggerRedAlert: (alertId) =>
    set({ redAlertActive: true, activeAlertId: alertId }),

  dismissRedAlert: () =>
    set({ redAlertActive: false, activeAlertId: null }),
}));
