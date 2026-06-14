import { useEffect, useState, useRef } from "react";
import { getSocket } from "@/lib/socket";

interface TrainPosition {
  trainNumber: string;
  latitude: number;
  longitude: number;
  bearing: number;
  speed: number;
  timestamp: string;
}

export function useTrainPositions() {
  const [positions, setPositions] = useState<Map<string, TrainPosition>>(new Map());
  const mapRef = useRef(positions);

  useEffect(() => {
    const socket = getSocket();

    socket.on("train:position", (data: TrainPosition) => {
      const next = new Map(mapRef.current);
      next.set(data.trainNumber, data);
      mapRef.current = next;
      setPositions(next);
    });

    socket.on("train:positions:batch", (batch: TrainPosition[]) => {
      const next = new Map(mapRef.current);
      for (const pos of batch) next.set(pos.trainNumber, pos);
      mapRef.current = next;
      setPositions(next);
    });

    return () => {
      socket.off("train:position");
      socket.off("train:positions:batch");
    };
  }, []);

  return positions;
}
