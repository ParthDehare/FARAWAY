"use client";

import { useRef, useEffect, useState, useMemo } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useMapStore } from "@/stores/mapStore";
import { useAlertStore } from "@/stores/alertStore";
import { MAJOR_STATIONS, MAP_STYLES, INDIA_BOUNDS } from "@/lib/mapbox";
import { useTracks } from "@/lib/queries";

const MOCK_TRAINS = [
  { id: "12951", name: "Rajdhani Exp", route: 0, progress: 0.35 },
  { id: "12952", name: "Rajdhani Exp", route: 0, progress: 0.72 },
  { id: "12839", name: "Chennai Mail", route: 1, progress: 0.5 },
];

function interpolateRoute(coords: number[][], progress: number): [number, number] {
  if (!coords || coords.length === 0) return [0, 0];
  const totalSegments = coords.length - 1;
  const segment = Math.min(Math.floor(progress * totalSegments), totalSegments - 1);
  const t = (progress * totalSegments) - segment;
  const [lng1, lat1] = coords[segment];
  const [lng2, lat2] = coords[segment + 1];
  return [lng1 + (lng2 - lng1) * t, lat1 + (lat2 - lat1) * t];
}

const ALERT_LOCATIONS: { id: string; coords: [number, number]; severity: "warning" | "critical" }[] = [
  { id: "KM-402", coords: [74.5, 22.0], severity: "critical" },
  { id: "KM-847", coords: [84.0, 18.0], severity: "warning" },
  { id: "KM-215", coords: [76.5, 27.8], severity: "warning" },
];

interface CommandMapProps {
  className?: string;
  height?: string;
  compact?: boolean;
  onSegmentClick?: (segmentId: string) => void;
}

export function CommandMap({ className = "", height = "100%", compact = false, onSegmentClick }: CommandMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);
  const alertMarkersRef = useRef<maplibregl.Marker[]>([]);
  const animFrameRef = useRef<number>(0);
  const trainProgressRef = useRef<number[]>(MOCK_TRAINS.map((t) => t.progress));

  const { view, showWeatherOverlay, showHealthHeatmap, showTrainDots, showDroneMarkers, selectEntity } = useMapStore();
  const { redAlertActive } = useAlertStore();
  const [mapLoaded, setMapLoaded] = useState(false);

  const { data: trackData } = useTracks();

  const dynamicRailwayCorridors = useMemo<GeoJSON.FeatureCollection>(() => {
    const features: GeoJSON.Feature[] = (trackData?.segments || []).map((seg) => ({
      type: "Feature",
      properties: {
        name: seg.code,
        id: seg.id,
        health: seg.health_index ?? 100,
      },
      geometry: seg.geometry, 
    }));
    return { type: "FeatureCollection", features };
  }, [trackData]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: MAP_STYLES.dark,
      center: view.center,
      zoom: view.zoom,
      pitch: view.pitch,
      bearing: view.bearing,
      antialias: true,
      attributionControl: false,
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: true, showZoom: !compact }), "top-right");

    map.on("load", () => {
      map.addSource("railway-corridors", { type: "geojson", data: dynamicRailwayCorridors });

      map.addLayer({
        id: "railway-glow",
        type: "line",
        source: "railway-corridors",
        paint: {
          "line-color": "#0a84ff",
          "line-width": 6,
          "line-opacity": 0.08,
          "line-blur": 4,
        },
      });

      map.addLayer({
        id: "railway-lines",
        type: "line",
        source: "railway-corridors",
        paint: {
          "line-color": [
            "interpolate", ["linear"], ["get", "health"],
            0, "#ff453a",
            50, "#ffd60a",
            80, "#30d158",
            100, "#30d158",
          ],
          "line-width": ["interpolate", ["linear"], ["zoom"], 4, 1.5, 8, 3, 12, 5],
          "line-opacity": 0.6,
        },
      });

      Object.entries(MAJOR_STATIONS).forEach(([code, station]) => {
        const el = document.createElement("div");
        el.innerHTML = `
          <div style="position:relative;display:flex;flex-direction:column;align-items:center;cursor:pointer;">
            <div style="width:10px;height:10px;border-radius:50%;background:rgba(10,132,255,0.6);border:2px solid rgba(10,132,255,0.25);box-shadow:0 0 12px rgba(10,132,255,0.3);"></div>
            <span style="margin-top:4px;font-family:var(--font-mono);font-size:9px;font-weight:600;color:rgba(255,255,255,0.35);white-space:nowrap;">${code}</span>
          </div>
        `;

        new maplibregl.Marker({ element: el })
          .setLngLat(station.coords)
          .setPopup(new maplibregl.Popup({ offset: 15, closeButton: false, className: "railmind-popup" })
            .setHTML(`<div style="font-family:system-ui;padding:4px 0;"><strong style="font-size:13px;">${station.name}</strong><br/><span style="font-size:11px;color:#888;">${code}</span></div>`))
          .addTo(map);

        el.addEventListener("click", () => selectEntity({ type: "segment", id: code }));
      });

      map.on("click", "railway-lines", (e) => {
        const feature = e.features?.[0];
        if (feature?.properties?.id && onSegmentClick) {
          onSegmentClick(feature.properties.id as string);
        }
      });

      map.on("mouseenter", "railway-lines", () => { map.getCanvas().style.cursor = "pointer"; });
      map.on("mouseleave", "railway-lines", () => { map.getCanvas().style.cursor = ""; });

      setMapLoaded(true);
    });

    mapRef.current = map;

    return () => {
      cancelAnimationFrame(animFrameRef.current);
      markersRef.current.forEach((m) => m.remove());
      alertMarkersRef.current.forEach((m) => m.remove());
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return;
    const source = mapRef.current.getSource("railway-corridors") as maplibregl.GeoJSONSource;
    if (source) {
      source.setData(dynamicRailwayCorridors);
    }
  }, [dynamicRailwayCorridors, mapLoaded]);

  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return;
    const map = mapRef.current;

    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    if (!showTrainDots || dynamicRailwayCorridors.features.length === 0) return;

    MOCK_TRAINS.forEach((train) => {
      const el = document.createElement("div");
      el.style.cssText = "width:8px;height:8px;border-radius:50%;background:#0a84ff;box-shadow:0 0 10px rgba(10,132,255,0.5);cursor:pointer;transition:transform 0.15s;";
      el.title = `${train.name} (${train.id})`;
      el.addEventListener("mouseenter", () => { el.style.transform = "scale(1.5)"; });
      el.addEventListener("mouseleave", () => { el.style.transform = "scale(1)"; });
      el.addEventListener("click", () => selectEntity({ type: "train", id: train.id }));

      const feature = dynamicRailwayCorridors.features[train.route % dynamicRailwayCorridors.features.length];
      const coords = feature?.geometry?.type === "LineString" ? feature.geometry.coordinates : [];
      if (coords.length > 0) {
        const pos = interpolateRoute(coords as number[][], train.progress);
        const marker = new maplibregl.Marker({ element: el }).setLngLat(pos as [number, number]).addTo(map);
        markersRef.current.push(marker);
      }
    });

    const animate = () => {
      trainProgressRef.current = trainProgressRef.current.map((p) => (p + 0.0003) % 1);
      markersRef.current.forEach((marker, i) => {
        const train = MOCK_TRAINS[i];
        const feature = dynamicRailwayCorridors.features[train.route % dynamicRailwayCorridors.features.length];
        const coords = feature?.geometry?.type === "LineString" ? feature.geometry.coordinates : [];
        if (coords.length > 0) {
            const pos = interpolateRoute(coords as number[][], trainProgressRef.current[i]);
            marker.setLngLat(pos as [number, number]);
        }
      });
      animFrameRef.current = requestAnimationFrame(animate);
    };
    animFrameRef.current = requestAnimationFrame(animate);

    return () => cancelAnimationFrame(animFrameRef.current);
  }, [mapLoaded, showTrainDots, selectEntity, dynamicRailwayCorridors]);

  useEffect(() => {
    if (!mapLoaded || !mapRef.current) return;
    alertMarkersRef.current.forEach((m) => m.remove());
    alertMarkersRef.current = [];

    ALERT_LOCATIONS.forEach((alert) => {
      const color = alert.severity === "critical" ? "#ff453a" : "#ffd60a";
      const el = document.createElement("div");
      el.innerHTML = `
        <div style="position:relative;display:flex;align-items:center;justify-content:center;cursor:pointer;">
          <div style="position:absolute;width:24px;height:24px;border-radius:50%;background:${color};opacity:0.15;animation:ping 2s cubic-bezier(0,0,0.2,1) infinite;"></div>
          <div style="width:12px;height:12px;border-radius:50%;background:${color};opacity:0.7;box-shadow:0 0 12px ${color}80;"></div>
          <span style="position:absolute;top:-16px;left:50%;transform:translateX(-50%);font-family:var(--font-mono);font-size:9px;font-weight:700;color:${color}99;white-space:nowrap;">${alert.id}</span>
        </div>
      `;

      el.addEventListener("click", () => selectEntity({ type: "alert", id: alert.id }));

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat(alert.coords)
        .addTo(mapRef.current!);
      alertMarkersRef.current.push(marker);
    });
  }, [mapLoaded, selectEntity]);

  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;
    const map = mapRef.current;
    if (redAlertActive) {
      map.setPaintProperty("railway-glow", "line-color", "#ff453a");
      map.setPaintProperty("railway-glow", "line-opacity", 0.2);
    } else {
      map.setPaintProperty("railway-glow", "line-color", "#0a84ff");
      map.setPaintProperty("railway-glow", "line-opacity", 0.08);
    }
  }, [redAlertActive, mapLoaded]);

  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;
    mapRef.current.flyTo({
      center: view.center,
      zoom: view.zoom,
      pitch: view.pitch,
      bearing: view.bearing,
      duration: 2000,
      essential: true,
    });
  }, [view.center[0], view.center[1]]);

  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;
    if (mapRef.current.getLayer("railway-lines")) {
      mapRef.current.setPaintProperty("railway-lines", "line-opacity", showHealthHeatmap ? 0.6 : 0.25);
    }
  }, [showHealthHeatmap, mapLoaded]);

  return (
    <div className={`relative overflow-hidden ${className}`} style={{ height }}>
      <div ref={containerRef} className="absolute inset-0" />

      {!compact && (
        <div className="absolute bottom-4 left-4 flex flex-col gap-1.5">
          {[
            { label: "Trains", active: showTrainDots, toggle: useMapStore.getState().toggleTrainDots },
            { label: "Health", active: showHealthHeatmap, toggle: useMapStore.getState().toggleHealthHeatmap },
            { label: "Weather", active: showWeatherOverlay, toggle: useMapStore.getState().toggleWeatherOverlay },
            { label: "Drones", active: showDroneMarkers, toggle: useMapStore.getState().toggleDroneMarkers },
          ].map((ctrl) => (
            <button
              key={ctrl.label}
              onClick={ctrl.toggle}
              className={`rounded-lg px-2.5 py-1 text-[10px] font-medium transition-all duration-300 backdrop-blur-xl ${
                ctrl.active
                  ? "bg-[#0a84ff]/20 text-[#0a84ff] ring-1 ring-[#0a84ff]/20"
                  : "bg-black/40 text-white/30 ring-1 ring-white/[0.04] hover:text-white/50"
              }`}
            >
              {ctrl.label}
            </button>
          ))}
        </div>
      )}

      <style jsx global>{`
        @keyframes ping {
          75%, 100% { transform: scale(2.5); opacity: 0; }
        }
        .railmind-popup .maplibregl-popup-content {
          background: rgba(28,28,30,0.9);
          backdrop-filter: blur(16px);
          border: 1px solid rgba(255,255,255,0.08);
          border-radius: 12px;
          padding: 8px 12px;
          color: white;
          box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        }
        .railmind-popup .maplibregl-popup-tip {
          border-top-color: rgba(28,28,30,0.9);
        }
        .maplibregl-ctrl-group {
          background: rgba(28,28,30,0.8) !important;
          backdrop-filter: blur(16px);
          border: 1px solid rgba(255,255,255,0.06) !important;
          border-radius: 10px !important;
          overflow: hidden;
        }
        .maplibregl-ctrl-group button {
          border-color: rgba(255,255,255,0.04) !important;
        }
        .maplibregl-ctrl-group button .maplibregl-ctrl-icon {
          filter: invert(1) opacity(0.4);
        }
      `}</style>
    </div>
  );
}
