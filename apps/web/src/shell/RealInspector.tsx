import { useEffect, useRef, type RefObject } from "react";
import type { RealObservation, RealSourceView } from "../real/view";
import { freshnessLabel } from "../real/view";
import { AnomalyChart } from "./AnomalyChart";

interface RealQuake {
  id: string;
  magnitude: number;
  place: string;
  time: string;
  depth_km?: number | null;
}

interface RealInspectorProps {
  view: RealSourceView | null;
  error: string | null;
  index: number;
  onAnalysis: (open: boolean) => void;
  analysisOpen: boolean;
  quake: RealQuake | null;
}

function utcLabel(value: string): string {
  return value.replace("T", " ").replace("Z", " UTC").replace("+00:00", " UTC");
}

export function RealInspector({ view, error, index, onAnalysis, analysisOpen, quake }: RealInspectorProps) {
  if (quake) {
    return (
      <aside className="inspector" aria-label="Sismo observado">
        <header className="inspector-head">
          <p className="kicker">Sismo · D21 · REAL</p>
          <h2>M{quake.magnitude.toFixed(1)}</h2>
          <p className="region">{quake.place}</p>
        </header>
        <div className="inspector-body">
          <p>Evento del catálogo USGS. No es una probabilidad de réplica ni un pronóstico del próximo sismo.</p>
          <dl className="facts">
            <div>
              <dt>Hora</dt>
              <dd>{quake.time}</dd>
            </div>
            <div>
              <dt>Profundidad</dt>
              <dd>{quake.depth_km === null || quake.depth_km === undefined ? "No disponible" : `${quake.depth_km} km`}</dd>
            </div>
            <div>
              <dt>Identificador</dt>
              <dd>{quake.id}</dd>
            </div>
          </dl>
        </div>
      </aside>
    );
  }
  const closeRef = useRef<HTMLButtonElement>(null);
  const onAnalysisRef = useRef(onAnalysis);
  onAnalysisRef.current = onAnalysis;

  useEffect(() => {
    if (!analysisOpen) {
      return;
    }
    closeRef.current?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onAnalysisRef.current(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [analysisOpen]);

  if (error || !view || view.status !== "available") {
    return (
      <aside className="inspector" aria-label="Dato real">
        <header className="inspector-head">
          <p className="kicker">Dato real</p>
          <h2>No disponible</h2>
        </header>
        <p>{error ?? view?.reason ?? "Cargando el subconjunto real."}</p>
        <p className="fine">El escenario DEMO no se usó como reemplazo.</p>
      </aside>
    );
  }

  const selected = view.observations[index] ?? view.observations[0];
  if (!selected) {
    return (
      <aside className="inspector" aria-label="Dato real">
        <h2>Sin observaciones</h2>
      </aside>
    );
  }
  const series = view.observations.map((item) => ({
    label: `${item.observed.start.slice(8, 10)} nov`,
    kind: "observed" as const,
    value: item.measurement.status === "present" ? item.measurement.value : null,
  }));
  const numbers = series.flatMap((item) => (item.value === null ? [] : [item.value]));
  const low = numbers.length > 0 ? Math.min(...numbers) - 0.05 : 0;
  const high = numbers.length > 0 ? Math.max(...numbers) + 0.05 : 1;

  return (
    <aside className="inspector" aria-label="Dato real">
      <header className="inspector-head">
        <p className="kicker">SST real · D15</p>
        <h2>SST del Caribe occidental</h2>
        <p className="region">{utcLabel(selected.observed.start)}</p>
        <p className="status-pill">Observación</p>
      </header>
      <div className="inspector-body">
        <p>{selected.quality.summary}</p>
        <p className="fine">{freshnessLabel(view.freshness)}</p>
        <h3>V15 · °C</h3>
        <p className="fine">
          {selected.measurement.status === "present"
            ? `Promedio del recorte: ${selected.measurement.value} ${selected.measurement.unit}`
            : "Sin valor. Las celdas de relleno no se convirtieron en cero."}
        </p>
        <AnomalyChart
          points={series}
          domain={{ min: low, max: high, ticks: [Number(high.toFixed(2)), Number(((low + high) / 2).toFixed(2)), Number(low.toFixed(2))] }}
          caption="Promedios diarios de SST del recorte, en grados Celsius. No hay tramo de pronóstico."
        />
        <dl className="facts">
          <div>
            <dt>Activo</dt>
            <dd>{selected.asset_id}</dd>
          </div>
          <div>
            <dt>Observación</dt>
            <dd>{selected.id}</dd>
          </div>
          <div>
            <dt>Checksum</dt>
            <dd>{view.checksum_sha256}</dd>
          </div>
          <div>
            <dt>Probabilidad</dt>
            <dd>No disponible</dd>
          </div>
        </dl>
        <p className="fine">{selected.spatial.resolution_note}</p>
      </div>
      <footer className="inspector-foot">
        <button type="button" className="analysis" onClick={() => onAnalysis(true)}>
          Ver trazabilidad
        </button>
      </footer>
      {analysisOpen ? (
        <TraceDialog observation={selected} view={view} closeRef={closeRef} onClose={() => onAnalysis(false)} />
      ) : null}
    </aside>
  );
}

function TraceDialog({
  observation,
  view,
  closeRef,
  onClose,
}: {
  observation: RealObservation;
  view: RealSourceView;
  closeRef: RefObject<HTMLButtonElement | null>;
  onClose: () => void;
}) {
  return (
    <div className="dialog-backdrop">
      <div role="dialog" aria-modal="true" aria-labelledby="trace-title" className="dialog">
        <h2 id="trace-title">Trazabilidad de {observation.id}</h2>
        <p>
          Activo {observation.asset_id}. Checksum {view.checksum_sha256}. {view.byte_size} bytes. Producto CoralTemp {view.product_version}, colección noaacrwsstDaily.
        </p>
        <p>{observation.provenance.note}</p>
        <p>La misma observación es el promedio que muestra el mapa y esta ficha. No es el escenario DEMO.</p>
        <button ref={closeRef} type="button" onClick={onClose}>
          Cerrar
        </button>
      </div>
    </div>
  );
}
