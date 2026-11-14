import type { FrameResult, GeoExtent, PlacedMarker } from "./geography";
import type { GlobeStatus } from "./createCesiumGlobe";
import type { ProductTrack,ProductRegion } from '../domain/generated';

export interface GlobeMarker {
  id: string;
  title: string;
  longitude: number;
  latitude: number;
  priority: number;
  note: string;
  symbol?: "observation" | "risk" | "forecast" | "cluster" | "context";
  count?: number;
}

export interface GlobeHandle {
  destroy: () => void;
  zoomIn?: () => void;
  zoomOut?: () => void;
  resize?: () => void;
  restoreView?: () => void;
  focusRegion?: (extent: GeoExtent) => FrameResult;
  addSignal?: (signal: GlobeMarker) => void;
  updateSignal?: (id: string, signal: Partial<GlobeMarker> & { id: string }) => void;
  removeSignal?: (id: string) => void;
  setOverlayListener?: (listener: ((markers: PlacedMarker[]) => void) | null) => void;
  setStatusListener?: (listener: ((status: GlobeStatus) => void) | null) => void;
  setSelectionListener?: (listener: ((selection: string | null) => void) | null) => void;
  selectMarker?: (id: string | null) => void;
  setSignals?: (signals: GlobeMarker[]) => void;
  setField?: (field: import("../demo/explore").FieldGrid | null, credit?: string) => void;
  setTracks?: (tracks: ProductTrack[]) => void;
  setRegions?: (regions: ProductRegion[]) => void;
  setCameraListener?: (listener: ((heightMeters: number) => void) | null) => void;
}

export type GlobeFactory = (container: HTMLElement) => GlobeHandle;

const active = new Set<GlobeHandle>();

export function activeGlobeCount(): number {
  return active.size;
}

export function mountGlobe(container: HTMLElement, createGlobe: GlobeFactory): GlobeHandle {
  if (container.dataset.earthEchoGlobe === "live") {
    throw new Error("El contenedor ya tiene un globo activo.");
  }
  const handle = createGlobe(container);
  let closed = false;
  const mounted: GlobeHandle = {
    destroy() {
      if (closed) {
        return;
      }
      closed = true;
      try {
        handle.destroy();
      } finally {
        active.delete(handle);
        delete container.dataset.earthEchoGlobe;
      }
    },
    zoomIn: () => handle.zoomIn?.(),
    zoomOut: () => handle.zoomOut?.(),
    resize: () => handle.resize?.(),
    restoreView: () => handle.restoreView?.(),
    focusRegion: (extent) => handle.focusRegion?.(extent) ?? { status: "unavailable", reason: "Este motor no encuadra regiones." },
    addSignal: (signal) => handle.addSignal?.(signal),
    updateSignal: (id, signal) => handle.updateSignal?.(id, signal),
    removeSignal: (id) => handle.removeSignal?.(id),
    setOverlayListener: (listener) => handle.setOverlayListener?.(listener),
    setStatusListener: (listener) => handle.setStatusListener?.(listener),
    setSelectionListener: (listener) => handle.setSelectionListener?.(listener),
    selectMarker: (id) => handle.selectMarker?.(id),
    setSignals: (signals) => handle.setSignals?.(signals),
    setField: (field, credit) => handle.setField?.(field, credit),
    setTracks: (tracks) => handle.setTracks?.(tracks),
    setRegions: (regions) => handle.setRegions?.(regions),
    setCameraListener: (listener) => handle.setCameraListener?.(listener),
  };
  container.dataset.earthEchoGlobe = "live";
  active.add(handle);
  return mounted;
}
