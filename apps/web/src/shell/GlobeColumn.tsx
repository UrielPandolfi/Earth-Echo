import { useState } from "react";
import { GlobeStage } from "../globe/GlobeStage";
import type { GlobeFactory, GlobeHandle } from "../globe/lifecycle";
import { formatCount, signalDisplayCount } from "../demo/queries";
import type { ObservatoryState, Section } from "./observatoryState";
import { amazoniaFrame } from "../globe/geography";
import { Icon, SymbolMark } from "./icons";

interface GlobeColumnProps {
  state: ObservatoryState;
  createGlobe: GlobeFactory;
  catalogTotal: number | null;
  catalogState: "loading" | "ready" | "error";
}

const sectionNote: Record<Exclude<Section, "explorar">, string> = {
  tendencias: "Tendencias todavía no calcula series. La pantalla sigue en el escenario demo.",
  historico: "El histórico todavía no carga archivos por fecha. La pantalla sigue en el escenario demo.",
};

export function GlobeColumn({ state, createGlobe, catalogTotal, catalogState }: GlobeColumnProps) {
  const [controls, setControls] = useState<GlobeHandle | null>(null);
  const cameraReady = Boolean(controls?.zoomIn && controls.zoomOut);
  const visible = signalDisplayCount(state.enabledInfoTypeIds);
  const note = state.section === "explorar" ? null : sectionNote[state.section];

  return (
    <section className="stage" aria-label="Globo">
      {note ? <p className="section-note" role="status">{note}</p> : null}
      <div className="globe-wrap">
        <GlobeStage createGlobe={createGlobe} onControls={setControls} />
        <div className="synthesis" aria-live="polite">
          <strong>{formatCount(visible)} señales</strong>
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
