import { create } from "zustand";

export interface TrainPosition {
  id: string;
  route?: number;
  progress?: number;
  latitude?: number;
  longitude?: number;
  speed_kmh?: number;
  passenger_count?: number;
  delay_minutes?: number;
}

interface TrainStore {
  trains: Record<string, TrainPosition>;
  updateTrainPosition: (data: TrainPosition) => void;
}

export const useTrainStore = create<TrainStore>((set) => ({
  trains: {},
  updateTrainPosition: (data) =>
    set((s) => ({
      trains: { ...s.trains, [data.id]: { ...s.trains[data.id], ...data } },
    })),
}));
