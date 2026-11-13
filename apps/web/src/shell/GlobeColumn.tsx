import { useEffect, useState } from "react";
import { GlobeStage } from "../globe/GlobeStage";
import type { GlobeFactory, GlobeHandle, GlobeMarker } from "../globe/lifecycle";
import { formatCount } from "../demo/queries";
import type { FieldGrid } from "../demo/explore";
import type { ObservatoryState, Section } from "./observatoryState";
import { amazoniaFrame, type GeoExtent } from "../globe/geography";
import { Icon, SymbolMark } from "./icons";

interface GlobeColumnProps {
  state: ObservatoryState;
  createGlobe: GlobeFactory;
  catalogTotal: number | null;
  catalogState: "loading" | "ready" | "error";
  signalCount: number;
  groupCount: number;
  markers: GlobeMarker[];
  field: FieldGrid | null;
  fieldCredit: string;
  frameRequest: GeoExtent | null;
  onSelect: (id: string) => void;
  onCameraHeight: (heightMeters: number) => void;
  emptyText?: string;
  trendNote?: string;
  countLabel?: string;
}

const sectionNote: Record<Exclude<Section, "explorar">, string> = {
  tendencias: "Tendencias usa el mismo escenario demo. No hay una tendencia calculada aparte.",
  historico: "Histórico mueve el tiempo del escenario. No carga archivos por fecha.",
};

export function GlobeColumn({
  state,
  createGlobe,
  catalogTotal,
  catalogState,
  signalCount,
  groupCount,
  markers,
  field,
  fieldCredit,
  frameRequest,
  onSelect,
  onCameraHeight,
  emptyText,
  trendNote,
  countLabel,
}: GlobeColumnProps) {
  const [controls, setControls] = useState<GlobeHandle | null>(null);
  const cameraReady = Boolean(controls?.zoomIn && controls.zoomOut);
  const note = state.section === "explorar" ? null : trendNote ?? sectionNote[state.section];

  useEffect(() => {
    controls?.setSignals?.(markers);
  }, [controls, markers]);

  useEffect(() => {
    controls?.setField?.(field, fieldCredit);
  }, [controls, field, fieldCredit]);

  useEffect(() => {
    controls?.setCameraListener?.(onCameraHeight);
    return () => controls?.setCameraListener?.(null);
  }, [controls, onCameraHeight]);

  useEffect(() => {
    if (frameRequest) {
      controls?.focusRegion?.(frameRequest);
    }
  }, [controls, frameRequest]);

  return (
    <section className="stage" aria-label="Globo">
      {note ? <p className="section-note" role="status">{note}</p> : null}
      <div className="globe-wrap">
        <GlobeStage createGlobe={createGlobe} onControls={setControls} onSelect={onSelect} />
        {signalCount === 0 ? (
          <p className="empty-map" role="status">
            {emptyText ?? "No hay señales en este instante y con estos filtros. Activá una categoría o volvé a Ahora."}
          </p>
        ) : null}
        <div className="synthesis" aria-live="polite">
          <strong>{countLabel ?? `${formatCount(signalCount)} señales`}</strong>
          {groupCount > 0 ? <span>{formatCount(groupCount)} grupos</span> : null}
          <span>·</span>
          {catalogState === "ready" && catalogTotal !== null ? (
            <span>{formatCount(catalogTotal)} fenómenos</span>
          ) : (
            <span>{catalogState === "loading" ? "fenómenos…" : "fenómenos no disponibles"}</span>
          )}
        </div>
        <ul className="symbol-legend">
          <li><SymbolMark kind="observation" /> Observación</li>
          <li><SymbolMark kind="risk" /> Riesgo</li>
          <li><SymbolMark kind="forecast" /> Pronóstico</li>
          <li><SymbolMark kind="cluster" /> Agrupación</li>
        </ul>
        <div className="zoom">
          <button type="button" onClick={() => controls?.zoomIn?.()} disabled={!cameraReady} title={cameraReady ? "Acercar" : "La cámara no está disponible"}>
            <Icon name="plus" />
            <span className="sr-only">Acercar</span>
          </button>
          <button type="button" onClick={() => controls?.zoomOut?.()} disabled={!cameraReady} title={cameraReady ? "Alejar" : "La cámara no está disponible"}>
            <Icon name="minus" />
            <span className="sr-only">Alejar</span>
          </button>
          <button type="button" onClick={() => controls?.restoreView?.()} disabled={!controls?.restoreView} title="Volver a la vista de América">
            <Icon name="home" />
            <span className="sr-only">Vista inicial</span>
          </button>
          <button type="button" onClick={() => controls?.focusRegion?.(amazoniaFrame)} disabled={!controls?.focusRegion} title="Encuadrar la extensión técnica de Amazonía">
            <Icon name="layers" />
            <span className="sr-only">Encuadrar región</span>
          </button>
        </div>
      </div>
    </section>
  );
}
