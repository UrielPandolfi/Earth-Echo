import { useEffect, useRef } from "react";
import type { DemoRecord } from "../demo/catalog";
import { infoKindLabel } from "../demo/explore";
import { timelineLabel } from "../demo/queries";
import type { InspectorTab, ObservatoryState } from "./observatoryState";
import { AnomalyChart } from "./AnomalyChart";
import { Icon } from "./icons";

interface InspectorProps {
  state: ObservatoryState;
  signal: DemoRecord | null;
  outsideFilter: boolean;
  related: DemoRecord[];
  onTab: (tab: InspectorTab) => void;
  onAnalysis: (open: boolean) => void;
  onSelect: (id: string) => void;
}

const tabs: Array<{ id: InspectorTab; label: string }> = [
  { id: "resumen", label: "Resumen" },
  { id: "datos", label: "Datos" },
  { id: "antecedentes", label: "Antecedentes" },
];

function formatInstant(value: string): string {
  return value.replace("T", " ").replace("Z", " UTC");
}

export function Inspector({ state, signal, outsideFilter, related, onTab, onAnalysis, onSelect }: InspectorProps) {
  const closeRef = useRef<HTMLButtonElement>(null);
  const onAnalysisRef = useRef(onAnalysis);
  onAnalysisRef.current = onAnalysis;

  useEffect(() => {
    if (!state.analysisOpen) {
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
  }, [state.analysisOpen]);

  if (!signal) {
    return (
      <aside className="inspector" aria-label="Señal seleccionada">
        <header className="inspector-head">
          <p className="kicker">Señal seleccionada · DEMO</p>
          <h2>Sin selección</h2>
        </header>
        <p className="fine">Elegí un resultado de la búsqueda o un símbolo del globo.</p>
      </aside>
    );
  }

  const valueText = signal.value === null ? "Sin valor en este registro" : `${signal.value} ${signal.unit}`;

  return (
    <aside className="inspector" aria-label="Señal seleccionada">
      <header className="inspector-head">
        <p className="kicker">Señal seleccionada · DEMO</p>
        <h2>{signal.title}</h2>
        <p className="region">{signal.regionName}</p>
        <p className="status-pill">
          <Icon name="heat" />
          {infoKindLabel(signal.infoType)}
        </p>
      </header>
      {outsideFilter ? (
        <p className="outside" role="status">
          Esta señal no cumple el filtro o el instante actual. Sigue en la ficha y no se dibuja en el mapa.
        </p>
      ) : null}
      <div className="tabs" role="tablist" aria-label="Ficha de la señal">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={state.tab === tab.id}
            className={state.tab === tab.id ? "is-current" : undefined}
            onClick={() => onTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="inspector-body" role="tabpanel">
        {state.tab === "resumen" ? (
          <>
            <p>{signal.summary}</p>
            <p className="fine">{signal.unitMeaning}</p>
            <h3>
              {signal.variableId} · {signal.unit}
            </h3>
            <p className="fine">Valor ilustrativo: {valueText}</p>
            <AnomalyChart
              points={signal.series}
              caption={`Serie del registro ${signal.id}. Los huecos son valores ausentes. El tramo punteado es pronóstico del escenario.`}
            />
          </>
        ) : null}
        {state.tab === "datos" ? (
          <dl className="facts">
            <div>
              <dt>Instante de la vista</dt>
              <dd>{timelineLabel(state.timelineDays)}</dd>
            </div>
            <div>
              <dt>Validez</dt>
              <dd>
                {formatInstant(signal.validFrom)} → {formatInstant(signal.validTo)}
              </dd>
            </div>
            <div>
              <dt>Disponible desde</dt>
              <dd>{formatInstant(signal.availableAt)}</dd>
            </div>
            <div>
              <dt>Inicialización</dt>
              <dd>{signal.initializationTime ? formatInstant(signal.initializationTime) : "No aplica"}</dd>
            </div>
            <div>
              <dt>Valor</dt>
              <dd>{valueText}</dd>
            </div>
            <div>
              <dt>Probabilidad</dt>
              <dd>No disponible</dd>
            </div>
            <div>
              <dt>Fuentes previstas</dt>
              <dd>{signal.intendedSourceIds.join(" · ")} · no conectadas</dd>
            </div>
          </dl>
        ) : null}
        {state.tab === "antecedentes" ? (
          <div className="prose">
            <p>
              {signal.phenomenonId} está especificado en el catálogo y no evaluado en este escenario. {signal.unitMeaning}
            </p>
            <p>
              La serie pertenece solo a {signal.id}. Un hueco no se rellena con cero ni con el valor vecino.
            </p>
          </div>
        ) : null}
        <dl className="facts compact">
          <div>
            <dt>Cobertura</dt>
            <dd>
              {signal.regionName} · {signal.longitude.toFixed(1)}°, {signal.latitude.toFixed(1)}°
            </dd>
          </div>
          <div>
            <dt>Fuentes previstas</dt>
            <dd>{signal.intendedSourceIds.join(" · ")}</dd>
          </div>
        </dl>
        <h3>Señales relacionadas</h3>
        <p className="fine">Otras fichas de la misma región del escenario. No hay una relación causal evaluada.</p>
        <ul className="related">
          {related.map((item) => (
            <li key={item.id}>
              <Icon name="heat" />
              <button type="button" onClick={() => onSelect(item.id)}>
                <strong>{item.title}</strong>
                <small>{item.regionName}</small>
              </button>
            </li>
          ))}
        </ul>
      </div>
      <footer className="inspector-foot">
        <button type="button" className="analysis" onClick={() => onAnalysis(true)}>
          Ver análisis completo
        </button>
      </footer>
      {state.analysisOpen ? (
        <div className="dialog-backdrop">
          <div role="dialog" aria-modal="true" aria-labelledby="analysis-title" className="dialog">
            <h2 id="analysis-title">Análisis de {signal.title}</h2>
            <p>{signal.summary}</p>
            <p>
              Valor ilustrativo: {valueText}. Unidad: {signal.unitMeaning} Validez {formatInstant(signal.validFrom)} a{" "}
              {formatInstant(signal.validTo)}.
            </p>
            <p>Fuentes previstas {signal.intendedSourceIds.join(", ")}, todavía no conectadas. No hay probabilidad ni causalidad.</p>
            <button ref={closeRef} type="button" onClick={() => onAnalysis(false)}>
              Cerrar
            </button>
          </div>
        </div>
      ) : null}
    </aside>
  );
}
