"use client";

import { useEffect } from "react";
import type maplibregl from "maplibre-gl";

const HEALTH_POINTS: GeoJSON.FeatureCollection = {
  type: "FeatureCollection",
  features: [
    { type: "Feature", properties: { health: 34, id: "KM-402" }, geometry: { type: "Point", coordinates: [74.5, 22.0] } },
    { type: "Feature", properties: { health: 48, id: "KM-847" }, geometry: { type: "Point", coordinates: [84.0, 18.0] } },
    { type: "Feature", properties: { health: 56, id: "KM-215" }, geometry: { type: "Point", coordinates: [76.5, 27.8] } },
    { type: "Feature", properties: { health: 62, id: "KM-1102" }, geometry: { type: "Point", coordinates: [73.2, 16.5] } },
    { type: "Feature", properties: { health: 78, id: "KM-530" }, geometry: { type: "Point", coordinates: [73.5, 16.8] } },
    { type: "Feature", properties: { health: 81, id: "KM-298" }, geometry: { type: "Point", coordinates: [89.5, 24.5] } },
    { type: "Feature", properties: { health: 91, id: "KM-655" }, geometry: { type: "Point", coordinates: [77.2, 10.7] } },
  ],
};

interface HealthHeatmapProps {
  map: maplibregl.Map | null;
  visible: boolean;
}

export function HealthHeatmap({ map, visible }: HealthHeatmapProps) {
  useEffect(() => {
    if (!map) return;

    const sourceId = "health-heatmap";
    const layerId = "health-heatmap-layer";

    if (!map.getSource(sourceId)) {
      map.addSource(sourceId, { type: "geojson", data: HEALTH_POINTS });

      map.addLayer({
        id: layerId,
        type: "heatmap",
        source: sourceId,
        paint: {
          "heatmap-weight": ["interpolate", ["linear"], ["get", "health"], 0, 1, 50, 0.6, 100, 0],
          "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 4, 0.6, 10, 1.5],
          "heatmap-color": [
            "interpolate", ["linear"], ["heatmap-density"],
            0, "rgba(0,0,0,0)",
            0.2, "rgba(48,209,88,0.1)",
            0.4, "rgba(255,214,10,0.2)",
            0.6, "rgba(255,159,10,0.3)",
            0.8, "rgba(255,69,58,0.4)",
            1, "rgba(255,69,58,0.6)",
          ],
          "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 4, 30, 10, 60],
          "heatmap-opacity": 0,
        },
      });
    }

    map.setPaintProperty(layerId, "heatmap-opacity", visible ? 0.7 : 0);
  }, [map, visible]);

  return null;
}
