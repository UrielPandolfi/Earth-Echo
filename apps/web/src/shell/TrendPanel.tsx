import { useEffect, useState } from "react";
import type { DataMode } from "./observatoryState";
import { ForecastReplay } from "./ForecastReplay";
import { TrendChart } from "./TrendChart";

const apiBase = import.meta.env.VITE_API_BASE ?? "/api";

interface TrendPoint {
  year: number;
  month: number;
  anomaly_c: number | null;
}

interface TrendResponse {
  status: "evaluated" | "not_evaluable" | "unavailable";
  reason: string | null;
  narrative: string;
  method_id: string;
  reference_start: string;
  reference_end: string;
  analysis_start: string;
  analysis_end: string;
  present_months: number;
  missing_months: number;
  expected_months: number;
  slope_c_per_year: number | null;
  interval_low_c_per_year: number | null;
  interval_high_c_per_year: number | null;
  includes_zero: boolean | null;
  practical_threshold_exceeded: boolean | null;
  execution_id: string;
  series: TrendPoint[];
  trend_line: Array<{ year: number; month: number; anomaly_c: number }>;
  interval_low_line: Array<{ year: number; month: number; anomaly_c: number }>;
  interval_high_line: Array<{ year: number; month: number; anomaly_c: number }>;
  warnings: string[];
}

interface TrendPanelProps {
  mode: DataMode;
  analysisOpen: boolean;
  onAnalysis: (open: boolean) => void;
  onReplay?: (issue: string, revealed: boolean) => void;
}

export function TrendPanel({ mode, analysisOpen, onAnalysis, onReplay }: TrendPanelProps) {
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
        <p>El escenario simulado no se usa para estimar una tendencia. Elegí REAL para la SST del Caribe occidental.</p>
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
        <p>{error ?? "Cargando la serie mensual."}</p>
        <p className="fine">El escenario DEMO no se usó como reemplazo.</p>
      </aside>
    );
  }

  return (
    <aside className="inspector" aria-label="Tendencia">
      <header className="inspector-head">
        <p className="kicker">Tendencia · REAL · D15</p>
        <h2>SST del Caribe occidental</h2>
        <p className="region">{view.analysis_start} a {view.analysis_end}</p>
      </header>
      <div className="inspector-body">
        <p>{view.narrative}</p>
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
        <p className="fine">Método {view.method_id}. Ejecución {view.execution_id}.</p>
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
