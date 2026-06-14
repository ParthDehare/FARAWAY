import { create } from "zustand";

export type Role = "admin" | "maintenance" | "drone_op" | null;

interface UiStore {
  sidebarCollapsed: boolean;
  commandPaletteOpen: boolean;
  activePanel: string | null;
  demoMode: boolean;
  userRole: Role;

  toggleSidebar: () => void;
  setCommandPalette: (open: boolean) => void;
  setActivePanel: (panel: string | null) => void;
  toggleDemoMode: () => void;
  setUserRole: (role: Role) => void;
}

export const useUiStore = create<UiStore>((set) => ({
  sidebarCollapsed: false,
  commandPaletteOpen: false,
  activePanel: null,
  demoMode: true,
  userRole: null, // Start unauthenticated

  toggleSidebar: () =>
    set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setCommandPalette: (open) => set({ commandPaletteOpen: open }),
  setActivePanel: (panel) => set({ activePanel: panel }),
  toggleDemoMode: () =>
    set((s) => ({ demoMode: !s.demoMode })),
  setUserRole: (role) => set({ userRole: role }),
}));
