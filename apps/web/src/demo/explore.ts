import { normalizeLongitude } from "../globe/geography";
import { DAY_MS, DEMO_EPOCH_MS, demoRegions, recordsFor, type DemoRecord, type InfoKind } from "./catalog";

export interface ClusterGroup {
  id: string;
  count: number;
  longitude: number;
  latitude: number;
  west: number;
  south: number;
  east: number;
  north: number;
  memberIds: string[];
}

export interface SearchHit {
  kind: "region" | "signal";
  id: string;
  label: string;
  detail: string;
  longitude: number;
  latitude: number;
  west: number;
  south: number;
  east: number;
  north: number;
  crossesAntimeridian: boolean;
}

export interface ExplorationQuery {
  wide: boolean;
  categoryIds: readonly string[];
  infoTypeIds: readonly string[];
  timelineDays: number;
  clusterDegrees: number;
}

export function instantForDay(days: number): number {
  return DEMO_EPOCH_MS + days * DAY_MS;
}

export function recordVisibleAt(record: DemoRecord, instantMs: number): boolean {
  const from = Date.parse(record.validFrom);
  const to = Date.parse(record.validTo);
  const available = Date.parse(record.availableAt);
  if (instantMs < available || instantMs < from || instantMs >= to) {
    return false;
  }
  if (record.infoType === "forecast") {
    if (!record.initializationTime || instantMs < Date.parse(record.initializationTime)) {
      return false;
    }
  }
  return true;
}

export function visibleRecords(query: ExplorationQuery): DemoRecord[] {
  const instant = instantForDay(query.timelineDays);
  return recordsFor(query.wide).filter(
    (record) =>
      query.categoryIds.includes(record.categoryId) &&
      query.infoTypeIds.includes(record.infoType) &&
      recordVisibleAt(record, instant),
  );
}

export function countBy(records: readonly DemoRecord[], key: "categoryId" | "infoType"): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const record of records) {
    const id = record[key];
    counts[id] = (counts[id] ?? 0) + 1;
  }
  return counts;
}

export function clusterRecords(records: readonly DemoRecord[], cellDegrees: number): { singles: DemoRecord[]; clusters: ClusterGroup[] } {
  if (cellDegrees <= 0) {
    return { singles: [...records], clusters: [] };
  }
  const groups = new Map<string, DemoRecord[]>();
  for (const record of records) {
    const longitude = normalizeLongitude(record.longitude);
    const key = `${Math.floor((longitude + 180) / cellDegrees)}:${Math.floor((record.latitude + 90) / cellDegrees)}`;
    const list = groups.get(key) ?? [];
    list.push(record);
    groups.set(key, list);
  }
  const singles: DemoRecord[] = [];
  const clusters: ClusterGroup[] = [];
  for (const [key, list] of groups) {
    if (list.length === 1) {
      singles.push(list[0]!);
      continue;
    }
    const longitudes = list.map((item) => normalizeLongitude(item.longitude));
    const latitudes = list.map((item) => item.latitude);
    clusters.push({
      id: `cluster:${key}`,
      count: list.length,
      longitude: longitudes.reduce((sum, value) => sum + value, 0) / longitudes.length,
      latitude: latitudes.reduce((sum, value) => sum + value, 0) / latitudes.length,
      west: Math.min(...longitudes),
      east: Math.max(...longitudes),
      south: Math.min(...latitudes),
      north: Math.max(...latitudes),
      memberIds: list.map((item) => item.id),
    });
  }
  return { singles, clusters };
}

export function clusterDegreesFor(heightMeters: number, groupOnZoom: boolean): number {
  if (!groupOnZoom) {
    return 0;
  }
  if (heightMeters > 22_000_000) {
    return 8;
  }
  if (heightMeters > 16_000_000) {
    return 3;
  }
  return 0;
}

function fold(text: string): string {
  return text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("es");
}

export function searchDemo(text: string, records: readonly DemoRecord[]): SearchHit[] {
  const query = fold(text.trim());
  if (query.length < 2) {
    return [];
  }
  const regions = demoRegions
    .filter((region) => fold(region.name).includes(query))
    .map((region) => ({
      kind: "region" as const,
      id: region.id,
      label: region.name,
      detail: "Región del escenario",
      longitude: region.longitude,
      latitude: region.latitude,
      west: region.west,
      south: region.south,
      east: region.east,
      north: region.north,
      crossesAntimeridian: region.crossesAntimeridian,
    }));
  const signals = records
    .filter((record) => fold(`${record.title} ${record.regionName}`).includes(query))
    .slice(0, 6)
    .map((record) => ({
      kind: "signal" as const,
      id: record.id,
      label: record.title,
      detail: record.regionName,
      longitude: record.longitude,
      latitude: record.latitude,
      west: record.longitude - 1.5,
      south: record.latitude - 1.5,
      east: record.longitude + 1.5,
      north: record.latitude + 1.5,
      crossesAntimeridian: false,
    }));
  return [...regions, ...signals].slice(0, 8);
}

export function relatedRecords(record: DemoRecord, records: readonly DemoRecord[]): DemoRecord[] {
  return records.filter((item) => item.id !== record.id && item.regionId === record.regionId).slice(0, 2);
}

export interface FieldGrid {
  width: number;
  height: number;
  west: number;
  south: number;
  east: number;
  north: number;
  rgba: Uint8ClampedArray;
  missingCells: number;
}

const fieldColors = {
  soil: { low: [176, 69, 51], high: [28, 112, 186] },
  temperature: { low: [70, 120, 190], high: [196, 92, 48] },
  precipitation: { low: [214, 196, 140], high: [28, 92, 168] },
} as const;

export function buildField(layerId: "soil" | "temperature" | "precipitation"): FieldGrid {
  const width = 120;
  const height = 70;
  const west = -110;
  const south = -56;
  const east = -28;
  const north = 28;
  const rgba = new Uint8ClampedArray(width * height * 4);
  const colors = fieldColors[layerId];
  let missingCells = 0;
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const offset = (y * width + x) * 4;
      const nx = x / (width - 1);
      const ny = y / (height - 1);
      const hole = Math.sin(nx * 9 + ny * 4) * Math.cos(ny * 7) > 0.86;
      if (hole) {
        missingCells += 1;
        continue;
      }
      const wave = Math.sin(nx * Math.PI * 2 + ny * 3) * 0.5 + Math.cos(ny * Math.PI * 1.4) * 0.5;
      const mix = (wave + 1) / 2;
      rgba[offset] = Math.round(colors.low[0] + (colors.high[0] - colors.low[0]) * mix);
      rgba[offset + 1] = Math.round(colors.low[1] + (colors.high[1] - colors.low[1]) * mix);
      rgba[offset + 2] = Math.round(colors.low[2] + (colors.high[2] - colors.low[2]) * mix);
      rgba[offset + 3] = 170;
    }
  }
  return { width, height, west, south, east, north, rgba, missingCells };
}

export function infoKindLabel(kind: InfoKind): string {
  if (kind === "observation") {
    return "Observación";
  }
  if (kind === "risk") {
    return "Condición de peligro";
  }
  return "Pronóstico";
}
