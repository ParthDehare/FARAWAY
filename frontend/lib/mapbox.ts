// MapLibre GL — no API key, no credit card, unlimited usage
// Uses OpenFreeMap tiles (free, open-source)

export const MAP_TILE_URL = "https://tiles.openfreemap.org/styles/dark";

export const INDIA_BOUNDS: [[number, number], [number, number]] = [
  [68.1, 6.5],
  [97.4, 37.1],
];

export const MAJOR_STATIONS: Record<string, { name: string; coords: [number, number] }> = {
  NDLS: { name: "New Delhi", coords: [77.2197, 28.6448] },
  BCT: { name: "Mumbai Central", coords: [72.8196, 18.9690] },
  CSTM: { name: "Mumbai CST", coords: [72.8354, 18.9402] },
  MAS: { name: "Chennai Central", coords: [80.2752, 13.0827] },
  HWH: { name: "Howrah Junction", coords: [88.3426, 22.5839] },
  SBC: { name: "Bangalore City", coords: [77.5713, 12.9784] },
  SC: { name: "Secunderabad", coords: [78.5014, 17.4334] },
  JP: { name: "Jaipur", coords: [75.7873, 26.9196] },
  ADI: { name: "Ahmedabad", coords: [72.6008, 23.0225] },
  LKO: { name: "Lucknow", coords: [80.9462, 26.8467] },
  PNBE: { name: "Patna", coords: [85.1376, 25.6075] },
  GHY: { name: "Guwahati", coords: [91.7362, 26.1445] },
  TVC: { name: "Trivandrum", coords: [76.9520, 8.4869] },
  PUNE: { name: "Pune", coords: [73.8746, 18.5285] },
};

export const MAP_STYLES = {
  dark: MAP_TILE_URL,
  satellite: "https://tiles.openfreemap.org/styles/liberty",
} as const;
