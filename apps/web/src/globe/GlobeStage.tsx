import { useEffect, useRef, useState } from "react";
import { activeGlobeCount, mountGlobe, type GlobeFactory, type GlobeHandle } from "./lifecycle";

interface GlobeStageProps {
  createGlobe: GlobeFactory;
  onCount?: (count: number) => void;
  onControls?: (controls: GlobeHandle | null) => void;
}

export function GlobeStage({ createGlobe, onCount, onControls }: GlobeStageProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const onCountRef = useRef(onCount);
  const onControlsRef = useRef(onControls);
  const [error, setError] = useState<string | null>(null);
  onCountRef.current = onCount;
  onControlsRef.current = onControls;

  useEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }
    try {
      const mounted = mountGlobe(container, createGlobe);
      setError(null);
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
      {error ? (
        <p className="globe-error" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
