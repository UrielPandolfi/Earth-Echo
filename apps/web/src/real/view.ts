import type { FieldGrid, SearchHit } from "../demo/explore";

export interface RealObservation {
  id: string;
  asset_id: string;
  measurement:
    | { status: "present"; value: number; unit: string }
    | { status: "missing"; value: null; unit: null };
  observed: { kind: "instant"; start: string };
  spatial: {
    extent: { west: number; south: number; east: number; north: number };
    geometry?: { coordinates: number[] } | null;
    resolution_note?: string | null;
  };
  quality: { summary: string | null };
  provenance: { source_ids: string[]; note: string | null };
}

export interface RealSourceView {
  status: "available" | "unavailable";
  reason_code: string | null;
  reason: string | null;
  product_version: string | null;
  cadence: string | null;
  freshness: "within_cadence" | "recent_archive" | "historical" | null;
  latest_observation: string | null;
  latest_ingest: string | null;
  checksum_sha256: string | null;
  byte_size: number | null;
  asset_id: string | null;
  coverage: { west: number; south: number; east: number; north: number; crosses_antimeridian?: boolean } | null;
  observations: RealObservation[];
}

export interface RealField {
  observation_id: string;
  unit: string;
  width: number;
  height: number;
  west: number;
  south: number;
  east: number;
  north: number;
  minimum: number | null;
  maximum: number | null;
  missing_cells: number;
  values: Array<number | null>;
  color_scale?: 'linear' | 'log10';
  reverse_colors?: boolean;
  color_center?: number | null;
}

export function fieldColorBounds(field:Pick<RealField,'minimum'|'maximum'|'color_center'>):[number,number] {
  const low=field.minimum ?? 0,high=field.maximum ?? low+1;
  if(field.color_center==null)return [low,high];
  const radius=Math.max(Math.abs(low-field.color_center),Math.abs(high-field.color_center)) || 1;
  return [field.color_center-radius,field.color_center+radius];
}

export function isRealSourceView(value: unknown): value is RealSourceView {
  if (!value || typeof value !== "object") {
    return false;
  }
  const status = (value as { status?: unknown }).status;
  return status === "available" || status === "unavailable";
}

export function paintSstField(field: RealField): FieldGrid {
  const rgba = new Uint8ClampedArray(field.width * field.height * 4);
  const [minimum,maximum]=fieldColorBounds(field);
  const normalize=(value:number)=>field.color_scale==='log10' ? Math.log10(value) : value;
  const low=normalize(minimum),high=normalize(maximum);
  const span = high-low || 1;
  field.values.forEach((value, index) => {
    if (value === null) {
      return;
    }
    const normalized = Math.min(1, Math.max(0, (normalize(value) - low) / span));
    const mix = field.reverse_colors ? 1-normalized : normalized;
    const offset = index * 4;
    if(field.color_center!=null) {
      const signed=Math.max(-1,Math.min(1,(value-field.color_center)/((maximum-minimum)/2)));
      const target=signed<0 ? [48,132,186] : [224,92,56];
      const neutral=[225,232,229];
      for(let channel=0;channel<3;channel++)rgba[offset+channel]=Math.round(neutral[channel]+Math.abs(signed)*(target[channel]-neutral[channel]));
      rgba[offset+3]=220;
      return;
    }
    rgba[offset] = Math.round(48 + mix * 176);
    rgba[offset + 1] = Math.round(132 - mix * 40);
    rgba[offset + 2] = Math.round(186 - mix * 130);
    rgba[offset + 3] = 220;
  });
  return {
    width: field.width,
    height: field.height,
    west: field.west,
    south: field.south,
    east: field.east,
    north: field.north,
    rgba,
    missingCells: field.missing_cells,
  };
}

function fold(text: string): string {
  return text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("es");
}

export function searchReal(text: string, view: RealSourceView | null): SearchHit[] {
  const query = fold(text.trim());
  if (query.length < 2 || !view || view.status !== "available" || !view.coverage) {
    return [];
  }
  const hits: SearchHit[] = [];
  if (fold("Caribe occidental").includes(query) || fold("coraltemp").includes(query)) {
    hits.push({
      kind: "region",
      id: "caribe-occidental",
      label: "Caribe occidental",
      detail: "Recorte real de SST",
      longitude: (view.coverage.west + view.coverage.east) / 2,
      latitude: (view.coverage.south + view.coverage.north) / 2,
      west: view.coverage.west,
      south: view.coverage.south,
      east: view.coverage.east,
      north: view.coverage.north,
      crossesAntimeridian: false,
    });
  }
  view.observations.forEach((item, index) => {
    const label = `SST ${item.observed.start.slice(0, 10)}`;
    if (fold(label).includes(query) || fold(item.id).includes(query)) {
      hits.push({
        kind: "signal",
        id: String(index),
        label,
        detail: "Observación real",
        longitude: item.spatial.geometry?.coordinates[0] ?? 0,
        latitude: item.spatial.geometry?.coordinates[1] ?? 0,
        west: item.spatial.extent.west,
        south: item.spatial.extent.south,
        east: item.spatial.extent.east,
        north: item.spatial.extent.north,
        crossesAntimeridian: false,
      });
    }
  });
  return hits.slice(0, 8);
}

export function freshnessLabel(value: RealSourceView["freshness"]): string {
  if (value === "within_cadence") {
    return "Dentro de la cadencia diaria. El valor sigue siendo el análisis de las 12:00 UTC, no este instante.";
  }
  if (value === "recent_archive") {
    return "Archivo reciente. No es la observación de este instante.";
  }
  return "Archivo histórico. No es la observación actual.";
}
