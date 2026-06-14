import { create } from "zustand";

interface MapViewState {
  center: [number, number];
  zoom: number;
  pitch: number;
  bearing: number;
}

interface SelectedEntity {
  type: "train" | "segment" | "drone" | "alert";
  id: string;
}

interface MapStore {
  view: MapViewState;
  selectedEntity: SelectedEntity | null;
  showWeatherOverlay: boolean;
  showHealthHeatmap: boolean;
  showSatelliteLayer: boolean;
  showDroneMarkers: boolean;
  showTrainDots: boolean;

  setView: (view: Partial<MapViewState>) => void;
  flyTo: (center: [number, number], zoom?: number) => void;
  selectEntity: (entity: SelectedEntity | null) => void;
  toggleWeatherOverlay: () => void;
  toggleHealthHeatmap: () => void;
  toggleSatelliteLayer: () => void;
  toggleDroneMarkers: () => void;
  toggleTrainDots: () => void;
  resetView: () => void;
}

const DEFAULT_VIEW: MapViewState = {
  center: [78.9629, 22.5937],
  zoom: 5,
  pitch: 45,
  bearing: -15,
};

export const useMapStore = create<MapStore>((set) => ({
  view: DEFAULT_VIEW,
  selectedEntity: null,
  showWeatherOverlay: false,
  showHealthHeatmap: true,
  showSatelliteLayer: false,
  showDroneMarkers: true,
  showTrainDots: true,

  setView: (partial) =>
    set((s) => ({ view: { ...s.view, ...partial } })),

  flyTo: (center, zoom) =>
    set((s) => ({ view: { ...s.view, center, ...(zoom ? { zoom } : {}) } })),

  selectEntity: (entity) => set({ selectedEntity: entity }),

  toggleWeatherOverlay: () =>
    set((s) => ({ showWeatherOverlay: !s.showWeatherOverlay })),
  toggleHealthHeatmap: () =>
    set((s) => ({ showHealthHeatmap: !s.showHealthHeatmap })),
  toggleSatelliteLayer: () =>
    set((s) => ({ showSatelliteLayer: !s.showSatelliteLayer })),
  toggleDroneMarkers: () =>
    set((s) => ({ showDroneMarkers: !s.showDroneMarkers })),
  toggleTrainDots: () =>
    set((s) => ({ showTrainDots: !s.showTrainDots })),

  resetView: () => set({ view: DEFAULT_VIEW, selectedEntity: null }),
}));
