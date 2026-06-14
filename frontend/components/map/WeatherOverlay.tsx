"use client";

import { useEffect } from "react";
import type maplibregl from "maplibre-gl";

const FLOOD_RISK_ZONES: GeoJSON.FeatureCollection = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      properties: { name: "Konkan Coast", risk: 72 },
      geometry: {
        type: "Polygon",
        coordinates: [[[72.5, 15.0], [74.0, 15.0], [74.0, 18.0], [72.5, 18.0], [72.5, 15.0]]],
      },
    },
    {
      type: "Feature",
      properties: { name: "Mumbai Region", risk: 80 },
      geometry: {
        type: "Polygon",
        coordinates: [[[72.5, 18.5], [73.5, 18.5], [73.5, 19.5], [72.5, 19.5], [72.5, 18.5]]],
      },
    },
    {
      type: "Feature",
      properties: { name: "NE Corridor", risk: 45 },
      geometry: {
        type: "Polygon",
        coordinates: [[[89.0, 24.0], [92.0, 24.0], [92.0, 27.0], [89.0, 27.0], [89.0, 24.0]]],
      },
    },
  ],
};

interface WeatherOverlayProps {
  map: maplibregl.Map | null;
  visible: boolean;
}

export function WeatherOverlay({ map, visible }: WeatherOverlayProps) {
  useEffect(() => {
    if (!map) return;

    const sourceId = "weather-flood-zones";
    const layerId = "weather-flood-fill";
    const borderLayerId = "weather-flood-border";

    if (!map.getSource(sourceId)) {
      map.addSource(sourceId, { type: "geojson", data: FLOOD_RISK_ZONES });

      map.addLayer({
        id: layerId,
        type: "fill",
        source: sourceId,
        paint: {
          "fill-color": [
            "interpolate", ["linear"], ["get", "risk"],
            0, "rgba(10,132,255,0.02)",
            50, "rgba(255,214,10,0.06)",
            80, "rgba(255,69,58,0.08)",
          ],
          "fill-opacity": 0,
        },
      });

      map.addLayer({
        id: borderLayerId,
        type: "line",
        source: sourceId,
        paint: {
          "line-color": [
            "interpolate", ["linear"], ["get", "risk"],
            0, "rgba(10,132,255,0.1)",
            50, "rgba(255,214,10,0.2)",
            80, "rgba(255,69,58,0.3)",
          ],
          "line-width": 1,
          "line-dasharray": [4, 4],
          "line-opacity": 0,
        },
      });
    }

    map.setPaintProperty(layerId, "fill-opacity", visible ? 1 : 0);
    map.setPaintProperty(borderLayerId, "line-opacity", visible ? 1 : 0);
  }, [map, visible]);

  return null;
}
