import { useEffect, useState } from "react";
import { GlobeStage } from "../globe/GlobeStage";
import type { GlobeFactory, GlobeHandle, GlobeMarker,GeographicSelection } from "../globe/lifecycle";
import { formatCount } from "../demo/queries";
import type { FieldGrid } from "../demo/explore";
import type { ObservatoryState, Section } from "./observatoryState";
import { amazoniaFrame, type GeoExtent } from "../globe/geography";
import { Icon, SymbolMark } from "./icons";
import type { ProductTrack,ProductRegion } from '../domain/generated';

interface GlobeColumnProps {
  state: ObservatoryState;
  createGlobe: GlobeFactory;
  catalogTotal: number | null;
  catalogState: "loading" | "ready" | "error";
  signalCount: number;
  groupCount: number;
  markers: GlobeMarker[];
  field: FieldGrid | null;
  tracks?: ProductTrack[];
  regions?: ProductRegion[];
  fieldCredit: string;
  frameRequest: GeoExtent | null;
  onSelect: (id: string) => void;
  onCameraHeight: (heightMeters: number) => void;
  emptyText?: string;
  trendNote?: string;
  countLabel?: string;
  onGeographicSelect?: (position:{longitude:number;latitude:number}) => void;
  fieldSelection?: GeographicSelection|null;
}

const sectionNote: Record<Exclude<Section, "explorar">, string> = {
  tendencias: "Tendencias usa el mismo escenario demo. No hay una tendencia calculada aparte.",
  historico: "Histórico mueve el tiempo del escenario. No carga archivos por fecha.",
  pronosticos: "Pronósticos externos: seleccioná un período y tocá el campo científico.",
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
  tracks,
  regions,
  fieldCredit,
  frameRequest,
  onSelect,
  onCameraHeight,
  emptyText,
  trendNote,
  countLabel,
  onGeographicSelect,
  fieldSelection,
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

  useEffect(() => { controls?.setTracks?.(tracks ?? []); },[controls,tracks]);
  useEffect(() => { controls?.setRegions?.(regions ?? []); },[controls,regions]);
  useEffect(()=>{controls?.setGeographicListener?.(onGeographicSelect ?? null);return ()=>controls?.setGeographicListener?.(null);},[controls,onGeographicSelect]);
  useEffect(()=>{controls?.setFieldSelection?.(fieldSelection ?? null);},[controls,fieldSelection]);

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
          <small>del catálogo</small>
        </div>
        <ul className="symbol-legend">
          {state.section==='pronosticos' && state.dataMode==='real' ? <>
            <li><SymbolMark kind="forecast"/> Área para explorar · pronóstico</li>
            <li><SymbolMark kind="cluster"/> Agrupación visual de áreas</li>
            <li><span>□</span> Celda seleccionada · soporte de malla</li>
          </> : <>
          {state.dataMode==='real' ? <li><span style={{color:'#acb5c3'}}>●</span> Inventario (si seleccionado)</li> : null}
          {tracks?.length ? <li><span style={{color:'#e7bf74'}}>━</span> Trayectoria histórica</li> : null}
          {regions?.length ? <li><span style={{color:'#e7bf74'}}>▱</span> Geometría publicada · ver ficha</li> : null}
          <li><SymbolMark kind="observation" /> Observación</li>
          <li><SymbolMark kind="risk" /> Riesgo</li>
          <li><SymbolMark kind="forecast" /> Pronóstico</li>
          <li><SymbolMark kind="cluster" /> Agrupación</li>
          </>}
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
