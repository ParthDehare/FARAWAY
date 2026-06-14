import { useRef, useEffect, useCallback } from "react";
import maplibregl from "maplibre-gl";
import { useMapStore } from "@/stores/mapStore";
import { MAP_STYLES } from "@/lib/mapbox";

export function useMapbox(containerRef: React.RefObject<HTMLDivElement | null>) {
  const mapRef = useRef<maplibregl.Map | null>(null);
  const { view, setView } = useMapStore();

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

    map.on("moveend", () => {
      const c = map.getCenter();
      setView({
        center: [c.lng, c.lat],
        zoom: map.getZoom(),
        pitch: map.getPitch(),
        bearing: map.getBearing(),
      });
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [containerRef]);

  const flyTo = useCallback(
    (center: [number, number], zoom = 12) => {
      mapRef.current?.flyTo({
        center,
        zoom,
        pitch: 45,
        bearing: -15,
        duration: 2000,
        essential: true,
      });
    },
    []
  );

  return { map: mapRef, flyTo };
}
