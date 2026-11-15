import { useEffect, useRef, useState } from "react";
import { activeGlobeCount, mountGlobe, type GlobeFactory, type GlobeHandle } from "./lifecycle";
import type { PlacedMarker } from "./geography";
import type { GlobeStatus } from "./createCesiumGlobe";

interface GlobeStageProps {
  createGlobe: GlobeFactory;
  onCount?: (count: number) => void;
  onControls?: (controls: GlobeHandle | null) => void;
  onSelect?: (id: string) => void;
}

export function GlobeStage({ createGlobe, onCount, onControls, onSelect }: GlobeStageProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const onCountRef = useRef(onCount);
  const onControlsRef = useRef(onControls);
  const onSelectRef = useRef(onSelect);
  const mountedRef = useRef<GlobeHandle | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<GlobeStatus | null>(null);
  const [markers, setMarkers] = useState<PlacedMarker[]>([]);
  const [selection, setSelection] = useState<string | null>(null);
  onCountRef.current = onCount;
  onControlsRef.current = onControls;
  onSelectRef.current = onSelect;

  useEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }
    try {
      const mounted = mountGlobe(container, createGlobe);
      setError(null);
      mounted.setStatusListener?.(setStatus);
      mounted.setOverlayListener?.(setMarkers);
      mounted.setSelectionListener?.((id) => {
        setSelection(id);
        if (id && !id.startsWith("cluster:")) {
          onSelectRef.current?.(id);
        }
      });
      mountedRef.current = mounted;
      onCountRef.current?.(activeGlobeCount());
      onControlsRef.current?.(mounted);
      const observer =
        typeof ResizeObserver === "undefined"
          ? null
          : new ResizeObserver(() => {
              mounted.resize?.();
            });
      observer?.observe(container);
      return () => {
        observer?.disconnect();
        mountedRef.current = null;
        mounted.destroy();
        onControlsRef.current?.(null);
        onCountRef.current?.(activeGlobeCount());
      };
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "No se pudo montar el globo.";
      setError(message);
      onCountRef.current?.(activeGlobeCount());
      return;
    }
  }, [createGlobe]);

  return (
    <div className="globe-frame">
      <div ref={containerRef} className="globe-stage" />
      <div className="globe-labels">
        {markers.filter((marker) => marker.visible).map((marker) => (
          <button
            key={marker.id}
            type="button"
            className="globe-label"
            style={{ left: marker.x, top: marker.y }}
            onClick={() => mountedRef.current?.selectMarker?.(marker.id)}
          >
            {marker.title}
          </button>
        ))}
      </div>
      {status && status.state !== "ready" ? (
        <p className={status.state === "error" ? "globe-error" : "globe-status"} role="status">
          {status.detail}
        </p>
      ) : null}
      {selection && !selection.startsWith("demo-") && !selection.startsWith("wide-") && !/^[a-f0-9]{64}:/.test(selection) ? <p className="globe-selection">{selection}</p> : null}
      {error ? (
        <p className="globe-error" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
