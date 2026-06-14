"use client";

import { useEffect } from "react";
import type maplibregl from "maplibre-gl";
import { MAP_STYLES } from "@/lib/mapbox";

interface SatelliteLayerProps {
  map: maplibregl.Map | null;
  visible: boolean;
}

export function SatelliteLayer({ map, visible }: SatelliteLayerProps) {
  useEffect(() => {
    if (!map) return;
    const targetStyle = visible ? MAP_STYLES.satellite : MAP_STYLES.dark;
    map.setStyle(targetStyle);
  }, [map, visible]);

  return null;
}
