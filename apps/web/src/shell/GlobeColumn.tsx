import { useEffect, useState } from "react";
import { GlobeStage } from "../globe/GlobeStage";
import type { GlobeFactory, GlobeHandle, GlobeMarker,GeographicSelection } from "../globe/lifecycle";
import { formatCount } from "../demo/queries";
import type { FieldGrid } from "../demo/explore";
import type { ObservatoryState, Section } from "./observatoryState";
import { amazoniaFrame, type GeoExtent } from "../globe/geography";
import { Icon, SymbolMark } from "./icons";
import type { PlanetaryForecast, ProductTrack,ProductRegion } from '../domain/generated';
import { SentryNotes, type SentryBoard } from "../forecasts/SentryForecast";

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
  planetaryKp?: { forecast: PlanetaryForecast | null; error: string | null } | null;
  mapNotice?: string | null;
  sentryBoard?: SentryBoard | null;
}

const month = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];

function utcStamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return `${date.getUTCDate()} ${month[date.getUTCMonth()]} ${String(date.getUTCHours()).padStart(2, "0")}:${String(date.getUTCMinutes()).padStart(2, "0")}`;
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
  planetaryKp,
  mapNotice,
  sentryBoard,
}: GlobeColumnProps) {
  const [controls, setControls] = useState<GlobeHandle | null>(null);
  const cameraReady = Boolean(controls?.zoomIn && controls.zoomOut);
  const note = planetaryKp
    ? "El Kp previsto es planetario. El aviso está en el panel del mapa, no en una región."
    : mapNotice?.startsWith("Región Niño")
      ? "El recuadro marca la región del índice. Las probabilidades están en el inspector, no en cada punto."
      : mapNotice?.startsWith("Sentry")
        ? "Sentry no publica un lugar de impacto. El mapa no muestra puntos ni trayectorias."
        : mapNotice
          ? "El punto marca el terremoto principal. Las probabilidades están en el inspector, no en el mapa."
        : state.section === "explorar" ? null : trendNote ?? sectionNote[state.section];
  const planetaryWindows = (planetaryKp?.forecast?.windows ?? []).filter((window) => window.temporal_state !== "expired");

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

  const sentry = sentryBoard?.assessments?.status === "available" ? sentryBoard : null;
  return (
    <section className={sentry ? "stage sentry-stage" : "stage"} aria-label={sentry ? "Escena ilustrativa de Sentry" : "Globo"}>
      {sentry ? <SentryNotes board={sentry} part="top" /> : note ? <p className="section-note" role="status">{note}</p> : null}
      <div className="globe-wrap">
        <GlobeStage createGlobe={createGlobe} onControls={setControls} onSelect={onSelect} />
        {signalCount === 0 && !planetaryKp && !mapNotice && !sentry ? (
          <p className="empty-map" role="status">
            {emptyText ?? "No hay señales en este instante y con estos filtros. Activá una categoría o volvé a Ahora."}
          </p>
        ) : null}
        {sentry && sentry.selected ? <aside className="asteroid-badge" aria-label="Asteroide ilustrativo"><svg viewBox="0 0 80 64" aria-hidden="true"><path fill="#d5dee6" d="M18 34 28 14l18-4 16 12 6 16-8 14-20 6-16-4z"/><path fill="#8ea0b0" d="M30 22l8 10-6 8 12 4 8-12-6-12z"/></svg><strong>Asteroide seleccionado: {sentry.selected.fullname}</strong><p>Representación ilustrativa, no a escala. La forma no es un modelo verificado de este objeto y no indica su posición real.</p></aside> : null}
        {!sentry && mapNotice ? <p className="kp-float map-notice" role="status">{mapNotice}</p> : null}
        {planetaryKp ? (
          <aside className="kp-float" aria-label="Kp previsto planetario">
            <h2>Kp previsto</h2>
            <p>Índice planetario de NOAA SWPC. No se dibuja en el mapa.</p>
            {planetaryKp.error ? <p role="status">{planetaryKp.error}</p> : null}
            {planetaryWindows.length ? (
              <ol>
                {planetaryWindows.map((window) => (
                  <li key={window.valid_from}>
                    <strong>{window.value.toFixed(2)}</strong>
                    <span>{utcStamp(window.valid_from)}–{utcStamp(window.valid_to)} UTC</span>
                  </li>
                ))}
              </ol>
            ) : (
              <p>{planetaryKp.forecast?.reason ?? planetaryKp.forecast?.note ?? "No hay ventanas previstas en esta copia."}</p>
            )}
          </aside>
        ) : null}
        {!sentry && <div className="synthesis" aria-live="polite">
          <strong>{countLabel ?? `${formatCount(signalCount)} señales`}</strong>
          {groupCount > 0 ? <span>{formatCount(groupCount)} grupos</span> : null}
          <span>·</span>
          {catalogState === "ready" && catalogTotal !== null ? (
            <span>{formatCount(catalogTotal)} fenómenos</span>
          ) : (
            <span>{catalogState === "loading" ? "fenómenos…" : "fenómenos no disponibles"}</span>
          )}
          <small>del catálogo</small>
        </div>}
        <ul className="symbol-legend">
          {planetaryKp ? <li><SymbolMark kind="forecast" /> Kp planetario · sin lugar</li> : sentry ? <li>Sin lugar de impacto</li> : mapNotice?.startsWith("Región Niño") ? <li><span style={{color:'#e7bf74'}}>▱</span> Niño 3.4 · referencia</li> : mapNotice ? <li><SymbolMark kind="observation" /> Terremoto principal</li> : state.section==='pronosticos' && state.dataMode==='real' ? <>
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
      {sentry ? <SentryNotes board={sentry} part="bottom" /> : null}
    </section>
  );
}
