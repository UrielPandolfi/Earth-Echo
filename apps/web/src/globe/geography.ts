/** Traducción geográfica propia. Cesium solo entra en el adaptador del visor. */

export const WGS84_EQUATORIAL_RADIUS_M = 6_378_137;

export interface GeoExtent {
  west: number;
  south: number;
  east: number;
  north: number;
  crossesAntimeridian: boolean;
}

export interface CameraView {
  longitude: number;
  latitude: number;
  heightMeters: number;
}

export type FrameResult =
  | { status: "framed"; view: CameraView }
  | { status: "unavailable"; reason: string };

export interface ProjectedMarker {
  id: string;
  title: string;
  x: number;
  y: number;
  facing: boolean;
  priority: number;
}

export interface PlacedMarker extends ProjectedMarker {
  visible: boolean;
}

/** El modo demo no sigue al sol. La luz astronómica queda para una fase posterior. */
export const lightingMode = "presentation" as const;

/** Encuadre inicial: América del Sur como centro, norte arriba, Atlántico al este. */
export const americasPreset: CameraView = {
  longitude: -64,
  latitude: -14,
  heightMeters: 13_200_000,
};

export const cameraLimits = {
  minimumHeightMeters: 250_000,
  maximumHeightMeters: 28_000_000,
};

export interface TechnicalMarker {
  id: string;
  title: string;
  longitude: number;
  latitude: number;
  priority: number;
  note: string;
}

export const technicalMarkers: TechnicalMarker[] = [
  {
    id: "tech-amazonia-anchor",
    title: "Ancla técnica",
    longitude: -60,
    latitude: -3,
    priority: 3,
    note: "Punto de encuadre. No es una medición.",
  },
  {
    id: "tech-antimeridian",
    title: "Antimeridiano",
    longitude: 180,
    latitude: 0,
    priority: 2,
    note: "Costura longitudinal. No es un fenómeno.",
  },
  {
    id: "tech-backside",
    title: "Cara oculta",
    longitude: 120,
    latitude: 15,
    priority: 1,
    note: "Queda detrás del planeta al mirar América.",
  },
];

export const amazoniaFrame: GeoExtent = {
  west: -78,
  south: -18,
  east: -48,
  north: 8,
  crossesAntimeridian: false,
};

export const antimeridianFrame: GeoExtent = {
  west: 168,
  south: -12,
  east: -168,
  north: 12,
  crossesAntimeridian: true,
};

export function normalizeLongitude(longitude: number): number {
  if (!Number.isFinite(longitude)) {
    return Number.NaN;
  }
  let value = ((longitude + 180) % 360 + 360) % 360 - 180;
  if (value === -180) {
    return 180;
  }
  return value;
}

export function isClick(dx: number, dy: number, threshold = 6): boolean {
  return Math.hypot(dx, dy) <= threshold;
}

export function facingCamera(
  cameraLongitude: number,
  cameraLatitude: number,
  pointLongitude: number,
  pointLatitude: number,
): boolean {
  const camera = unitVector(cameraLongitude, cameraLatitude);
  const point = unitVector(pointLongitude, pointLatitude);
  return dot(camera, point) > 0.05;
}

export function frameExtent(extent: GeoExtent): FrameResult {
  if (!Number.isFinite(extent.west) || !Number.isFinite(extent.east) || !Number.isFinite(extent.south) || !Number.isFinite(extent.north)) {
    return { status: "unavailable", reason: "La extensión tiene coordenadas que no son números." };
  }
  if (extent.south < -90 || extent.north > 90 || extent.south > extent.north) {
    return { status: "unavailable", reason: "El rango de latitud no es válido." };
  }
  const width = spanWidth(extent);
  if (width === null) {
    return {
      status: "unavailable",
      reason: extent.crossesAntimeridian
        ? "El cruce del antimeridiano exige que el oeste sea mayor que el este."
        : "El oeste supera al este sin marcar el cruce del antimeridiano.",
    };
  }
  const height = extent.north - extent.south;
  const centerLat = (extent.south + extent.north) / 2;
  const centerLon = spanCenter(extent, width);
  const largest = Math.max(width, height);
  const alpha = Math.min(((largest * Math.PI) / 180) / 2, 1.15);
  const fovScale = Math.tan(((55 * Math.PI) / 180) * 0.42);
  const heightMeters = clamp(
    alpha === 0 ? cameraLimits.minimumHeightMeters : (WGS84_EQUATORIAL_RADIUS_M * Math.sin(alpha)) / fovScale,
    cameraLimits.minimumHeightMeters,
    cameraLimits.maximumHeightMeters,
  );
  return {
    status: "framed",
    view: {
      longitude: normalizeLongitude(centerLon),
      latitude: clamp(centerLat, -85, 85),
      heightMeters,
    },
  };
}

export function placeMarkers(markers: ProjectedMarker[], width: number, height: number): PlacedMarker[] {
  const ranked = [...markers].sort((a, b) => b.priority - a.priority);
  const placed: PlacedMarker[] = [];
  for (const marker of ranked) {
    const inside =
      marker.facing &&
      marker.x >= 16 &&
      marker.y >= 56 &&
      marker.x <= width - 16 &&
      marker.y <= height - 78;
    const crowded = placed.some(
      (other) => other.visible && Math.hypot(other.x - marker.x, other.y - marker.y) < 28,
    );
    placed.push({ ...marker, visible: inside && !crowded });
  }
  return markers.map((marker) => placed.find((item) => item.id === marker.id) ?? { ...marker, visible: false });
}

function spanWidth(extent: GeoExtent): number | null {
  if (extent.crossesAntimeridian) {
    if (extent.west <= extent.east) {
      return null;
    }
    return 180 - extent.west + (extent.east + 180);
  }
  if (extent.west > extent.east) {
    return null;
  }
  return extent.east - extent.west;
}

function spanCenter(extent: GeoExtent, width: number): number {
  if (!extent.crossesAntimeridian) {
    return (extent.west + extent.east) / 2;
  }
  return normalizeLongitude(extent.west + width / 2);
}

function unitVector(longitude: number, latitude: number): [number, number, number] {
  const lon = (longitude * Math.PI) / 180;
  const lat = (latitude * Math.PI) / 180;
  return [Math.cos(lat) * Math.cos(lon), Math.cos(lat) * Math.sin(lon), Math.sin(lat)];
}

function dot(a: [number, number, number], b: [number, number, number]): number {
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}
