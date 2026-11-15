import { useEffect, useState } from "react";
import type { DataMode } from "./observatoryState";
import { ForecastReplay } from "./ForecastReplay";
import { TrendChart } from "./TrendChart";
import { SSTAnomalies } from './SSTAnomalies';
import { AssociationsPanel } from './AssociationsPanel';
import type { TrendView as TrendResponse } from '../domain/generated';

const apiBase = import.meta.env.VITE_API_BASE ?? "/api";

interface TrendPanelProps {
  mode: DataMode;
  analysisOpen: boolean;
  onAnalysis: (open: boolean) => void;
  onReplay?: (issue: string, revealed: boolean) => void;
  onShowProduct?: (key:string)=>void;
}

export function TrendPanel({ mode, analysisOpen, onAnalysis, onReplay,onShowProduct }: TrendPanelProps) {
  const [view, setView] = useState<TrendResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (mode !== "real") {
      return;
    }
    const controller = new AbortController();
    async function load() {
      try {
        const response = await fetch(`${apiBase}/v1/analyses/d15-sst`, { signal: controller.signal });
        if (!response.ok) {
          throw new Error("La tendencia no respondió.");
        }
        setView((await response.json()) as TrendResponse);
        setError(null);
      } catch (caught) {
        if (caught instanceof DOMException && caught.name === "AbortError") {
          return;
        }
        setView(null);
        setError(caught instanceof Error ? caught.message : "No se pudo leer la tendencia.");
      }
    }
    void load();
    return () => controller.abort();
  }, [mode]);

  if (mode !== "real") {
    return (
      <aside className="inspector" aria-label="Tendencia">
        <header className="inspector-head">
          <p className="kicker">Tendencia</p>
          <h2>Sin análisis en DEMO</h2>
        </header>
        <p>El escenario simulado no se usa para estimar una tendencia. Elegí REAL para la historia SST del recorte del Caribe.</p>
      </aside>
    );
  }

  if (error || !view) {
    return (
      <aside className="inspector" aria-label="Tendencia">
        <header className="inspector-head">
          <p className="kicker">Tendencia · REAL</p>
          <h2>No disponible</h2>
        </header>
        <div className="inspector-body">
          <p role="status">{error ?? "Cargando la serie mensual."}</p>
          <SSTAnomalies key="sst-anomalies" onShowProduct={onShowProduct}/>
          <AssociationsPanel key="associations" />
        </div>
        <p className="fine">El escenario DEMO no se usó como reemplazo.</p>
      </aside>
    );
  }

  return (
    <aside className="inspector" aria-label="Tendencia">
      <header className="inspector-head">
        <p className="kicker">Tendencia · REAL · D15</p>
        <h2>SST del Caribe · recorte histórico</h2>
        <p className="region">{view.analysis_start} a {view.analysis_end}</p>
      </header>
      <div className="inspector-body">
        <p>{view.narrative}</p>
        {view.region_extent && <p className="fine">Huella WGS84: {view.region_extent.south.toFixed(2)} a {view.region_extent.north.toFixed(2)}° N, {Math.abs(view.region_extent.west).toFixed(2)} a {Math.abs(view.region_extent.east).toFixed(2)}° O · sur de Puerto Rico.</p>}
        <p className="fine">
          Referencia {view.reference_start} a {view.reference_end}. Meses presentes {view.present_months} de {view.expected_months}. Huecos {view.missing_months}.
        </p>
        <dl className="facts">
          <div>
            <dt>Pendiente</dt>
            <dd>{view.slope_c_per_year === null ? "No evaluable" : `${view.slope_c_per_year.toFixed(3)} °C/año`}</dd>
          </div>
          <div>
            <dt>Intervalo</dt>
            <dd>
              {view.interval_low_c_per_year === null || view.interval_high_c_per_year === null
                ? "No disponible"
                : `${view.interval_low_c_per_year.toFixed(3)} a ${view.interval_high_c_per_year.toFixed(3)}`}
            </dd>
          </div>
          <div>
            <dt>Cero</dt>
            <dd>{view.includes_zero === null ? "No evaluado" : view.includes_zero ? "El intervalo lo incluye" : "El intervalo no lo incluye"}</dd>
          </div>
          <div>
            <dt>Pronóstico</dt>
            <dd>No es un pronóstico</dd>
          </div>
        </dl>
        <p className="fine">Intervalo condicional con bloques de {view.bootstrap_block_months ?? 12} meses. Sensibilidad con {view.sensitivity_block_months ?? 24} meses: {view.sensitivity_low_c_per_year==null || view.sensitivity_high_c_per_year==null ? 'No evaluable' : `${view.sensitivity_low_c_per_year.toFixed(3)} a ${view.sensitivity_high_c_per_year.toFixed(3)} °C/año`}. Correlación residual mensual adyacente: {view.residual_lag1_r==null ? 'No definida' : view.residual_lag1_r.toFixed(3)}.</p>
        <p className="fine">Los intervalos dependen del período y de los supuestos del remuestreo; no incluyen toda la incertidumbre observacional.</p>
        <p className="fine">Método {view.method_id}. Ejecución {view.execution_id}.</p>
        <SSTAnomalies key="sst-anomalies" onShowProduct={onShowProduct}/>
        <AssociationsPanel key="associations" />
        <ForecastReplay onReplay={onReplay} />
      </div>
      <footer className="inspector-foot">
        <button type="button" className="analysis" onClick={() => onAnalysis(true)}>
          Ver serie
        </button>
        <a className="analysis" href={`${apiBase}/v1/analyses/d15-sst.csv`}>Exportar CSV</a>
      </footer>
      {analysisOpen ? (
        <div className="dialog-backdrop trend-backdrop">
          <div role="dialog" aria-modal="true" aria-labelledby="trend-title" className="dialog trend-dialog">
            <h2 id="trend-title">Anomalía mensual de SST</h2>
            <p>{view.narrative}</p>
            {view.status === "evaluated" ? (
              <TrendChart
                series={view.series}
                trendLine={view.trend_line}
                lowLine={view.interval_low_line}
                highLine={view.interval_high_line}
              />
            ) : (
              <p>{view.reason}</p>
            )}
            <ul>
              {view.warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
            <button type="button" onClick={() => onAnalysis(false)}>Cerrar</button>
          </div>
        </div>
      ) : null}
    </aside>
  );
}
