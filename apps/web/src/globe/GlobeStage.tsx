import { useEffect, useRef, useState } from "react";
import { activeGlobeCount, mountGlobe, type GlobeFactory } from "./lifecycle";

interface GlobeStageProps {
  createGlobe: GlobeFactory;
  onCount?: (count: number) => void;
}

export function GlobeStage({ createGlobe, onCount }: GlobeStageProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const onCountRef = useRef(onCount);
  const [error, setError] = useState<string | null>(null);
  onCountRef.current = onCount;

  useEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }
    try {
      const mounted = mountGlobe(container, createGlobe);
      setError(null);
      onCountRef.current?.(activeGlobeCount());
      return () => {
        mounted.destroy();
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
