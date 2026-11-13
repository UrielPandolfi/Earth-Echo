import { useEffect, useRef } from "react";
import { demoScenario } from "../demo/scenario";
import { timelineKind, timelineLabel } from "../demo/queries";
import type { InspectorTab, ObservatoryState } from "./observatoryState";
import { AnomalyChart } from "./AnomalyChart";
import { Icon } from "./icons";

interface InspectorProps {
  state: ObservatoryState;
  onTab: (tab: InspectorTab) => void;
  onAnalysis: (open: boolean) => void;
}

const tabs: Array<{ id: InspectorTab; label: string }> = [
  { id: "resumen", label: "Resumen" },
  { id: "datos", label: "Datos" },
  { id: "antecedentes", label: "Antecedentes" },
];

export function Inspector({ state, onTab, onAnalysis }: InspectorProps) {
  const signal = demoScenario.signal;
  const closeRef = useRef<HTMLButtonElement>(null);
  const onAnalysisRef = useRef(onAnalysis);
  const kind = timelineKind(state.timelineDays);
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

  return (
    <aside className="inspector" aria-label="Señal seleccionada">
      <header className="inspector-head">
        <p className="kicker">Señal seleccionada · DEMO</p>
        <h2>{signal.title}</h2>
        <p className="region">{signal.regionName}</p>
        <p className="status-pill">
          <Icon name="heat" />
          {signal.statusLabel}
        </p>
      </header>
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
            <p className="fine">Texto del escenario demo. No es una medición de SMAP ni de GLDAS.</p>
            <h3>{signal.variableLabel}</h3>
            <p className="fine">{signal.anomalyLabel}</p>
            <AnomalyChart
              points={signal.series}
              caption="Serie sintética de anomalía. La parte punteada es un tramo de pronóstico no evaluado."
            />
          </>
        ) : null}
        {state.tab === "datos" ? (
          <dl className="facts">
            <div>
              <dt>Momento</dt>
              <dd>{timelineLabel(state.timelineDays)} · {kind === "pronostico" ? "tramo estimado" : "tramo observado"}</dd>
            </div>
            <div>
              <dt>Variable</dt>
              <dd>{signal.variableId} · {signal.variableLabel}</dd>
            </div>
            <div>
              <dt>Región</dt>
              <dd>{signal.regionName} · {signal.regionId}</dd>
            </div>
            <div>
              <dt>Probabilidad</dt>
              <dd>No disponible</dd>
            </div>
            <div>
              <dt>Valor medido</dt>
              <dd>No disponible. La curva es sintética.</dd>
            </div>
            <div>
              <dt>Fuentes citadas</dt>
              <dd>
                {signal.sources.map((source) => (
                  <span key={source.id}>{source.id} {source.name} · {source.integration}</span>
                ))}
              </dd>
            </div>
          </dl>
        ) : null}
        {state.tab === "antecedentes" ? (
          <div className="prose">
            <p>SMAP observa humedad superficial y no toda la zona radicular. GLDAS es salida de un modelo, no una medición directa.</p>
            <p>Esta ficha no tiene una serie observada cargada. El gráfico del resumen es una curva de demostración, con un tramo futuro sin evaluación.</p>
            <p>El estado del fenómeno F11 sigue especificado. No hay un modelo validado para este alcance.</p>
          </div>
        ) : null}
        <dl className="facts compact">
          <div>
            <dt>Horizonte</dt>
            <dd>{signal.horizonLabel}</dd>
          </div>
          <div>
            <dt>Cobertura</dt>
            <dd>{signal.coverageLabel}</dd>
          </div>
          <div>
            <dt>Fuentes</dt>
            <dd>NASA SMAP · GLDAS</dd>
          </div>
        </dl>
        <h3>Señales relacionadas</h3>
        <p className="fine">Otras fichas del mismo escenario. No hay una relación causal evaluada.</p>
        <ul className="related">
          {signal.related.map((item) => (
            <li key={item.id}>
              <Icon name={item.icon} />
              <span>
                <strong>{item.title}</strong>
                <small>{item.detail}</small>
              </span>
              <em>{item.level}</em>
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
            <h2 id="analysis-title">Análisis completo</h2>
            <p>
              No hay un análisis calculado para {signal.title}. El botón abre este estado y no simula un resultado.
              Las series y la evaluación llegan en fases posteriores.
            </p>
            <button ref={closeRef} type="button" onClick={() => onAnalysis(false)}>
              Cerrar
            </button>
          </div>
        </div>
      ) : null}
    </aside>
  );
}
