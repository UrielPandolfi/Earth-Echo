import { useEffect, useState } from "react";

const apiBase = import.meta.env.VITE_API_BASE ?? "/api";

interface KpStep {
  valid_start: string;
  valid_end: string;
  lead_time_hours: number;
  kp: number;
}

interface KpForecast {
  issued_at: string;
  initialization_note: string;
  note: string;
  steps: KpStep[];
  validated_for_use: boolean;
}

interface ExperimentReport {
  reason: string;
  additional_skill: boolean;
  validated_for_use: boolean;
  cases_scored: number;
  cases_excluded: number;
  event_base_rate: number | null;
  availability_note: string;
  metrics: Record<string, { mae_c: number; bias_c: number; events: { hits: number; false_alarms: number; misses: number } } | null>;
}

interface ReplayResult {
  status?: string;
  reason?: string;
  analog_c: number | null;
  persistence_c: number;
  climatology_c: number;
  outcome_c: number | null;
  analog_error_c?: number;
  excluded_reason: string | null;
  neighbors: number[][];
}

const issues = Array.from({ length: 47 }, (_, index) => {
  const monthIndex = (2022 * 12) + index;
  const year = Math.floor(monthIndex / 12);
  const month = (monthIndex % 12) + 1;
  return { year, month };
});

function mae(report: ExperimentReport, name: string): string {
  const metric = report.metrics[name];
  return metric ? `${metric.mae_c.toFixed(3)} °C` : "no disponible";
}

interface ForecastReplayProps {
  onReplay?: (issue: string, revealed: boolean) => void;
}

export function ForecastReplay({ onReplay }: ForecastReplayProps) {
  const [forecast, setForecast] = useState<KpForecast | null>(null);
  const [report, setReport] = useState<ExperimentReport | null>(null);
  const [issue, setIssue] = useState("2024-6");
  const [replayResult, setReplayResult] = useState<ReplayResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      try {
        const [forecastResponse, reportResponse] = await Promise.all([
          fetch(`${apiBase}/v1/forecasts/d28-kp`, { signal: controller.signal }),
          fetch(`${apiBase}/v1/experiments/sst-anomaly`, { signal: controller.signal }),
        ]);
        if (!forecastResponse.ok || !reportResponse.ok) {
          throw new Error("El pronóstico o el experimento no respondieron.");
        }
        setForecast((await forecastResponse.json()) as KpForecast);
        setReport((await reportResponse.json()) as ExperimentReport);
      } catch (caught) {
        if (caught instanceof DOMException && caught.name === "AbortError") {
          return;
        }
        setError(caught instanceof Error ? caught.message : "No se pudo leer el experimento.");
      }
    }
    void load();
    return () => controller.abort();
  }, []);

  async function post(path: string) {
    const [year, month] = issue.split("-").map(Number);
    const response = await fetch(`${apiBase}${path}?year=${year}&month=${month}`, { method: "POST" });
    const body = (await response.json()) as ReplayResult;
    setReplayResult(body);
    const revealed = body.outcome_c !== null && body.outcome_c !== undefined;
    onReplay?.(`${year}-${String(month).padStart(2, "0")}`, revealed);
  }

  return (
    <section className="forecast-block" aria-label="Pronósticos">
      <h3>Pronóstico importado</h3>
      {forecast ? (
        <>
          <p>Kp previsto por SWPC. Emitido {forecast.issued_at}. {forecast.initialization_note}</p>
          <p className="fine">{forecast.note} No está validado para uso operativo.</p>
          <p>
            {forecast.steps[0]?.valid_start} → {forecast.steps[forecast.steps.length - 1]?.valid_end}:{" "}
            {forecast.steps.map((step) => step.kp.toFixed(2)).join(" · ")} Kp
          </p>
        </>
      ) : (
        <p>{error ?? "Cargando el pronóstico importado."}</p>
      )}
      <h3>Experimento retrospectivo</h3>
      {report ? (
        <>
          <p>{report.reason}</p>
          <p className="fine">{report.availability_note}</p>
          <dl className="facts">
            <div>
              <dt>Error análogo</dt>
              <dd>{mae(report, "analog")}</dd>
            </div>
            <div>
              <dt>Error persistencia</dt>
              <dd>{mae(report, "persistence")}</dd>
            </div>
            <div>
              <dt>Error climatología</dt>
              <dd>{mae(report, "climatology")}</dd>
            </div>
            <div>
              <dt>Casos</dt>
              <dd>{report.cases_scored} puntuados, {report.cases_excluded} excluidos</dd>
            </div>
          </dl>
          <p className="fine">
            Falsas alarmas del análogo: {report.metrics.analog?.events.false_alarms ?? "—"}. Omisiones:{" "}
            {report.metrics.analog?.events.misses ?? "—"}. Frecuencia del evento:{" "}
            {report.event_base_rate === null ? "no disponible" : report.event_base_rate.toFixed(2)}. Los meses seguidos no son casos independientes.
          </p>
          <label>
            Mes de emisión
            <select value={issue} onChange={(event) => {
              setIssue(event.target.value);
              setReplayResult(null);
              const [year, month] = event.target.value.split("-");
              onReplay?.(`${year}-${month.padStart(2, "0")}`, false);
            }}>
              {issues.map((item) => (
                <option key={`${item.year}-${item.month}`} value={`${item.year}-${item.month}`}>
                  {item.year}-{String(item.month).padStart(2, "0")}
                </option>
              ))}
            </select>
          </label>
          <div className="inspector-foot">
            <button type="button" onClick={() => void post("/v1/experiments/sst-anomaly/replay")}>Guardar predicción</button>
            <button type="button" onClick={() => void post("/v1/experiments/sst-anomaly/reveal")} disabled={!replayResult || replayResult.status === "prediction_not_saved"}>
              Revelar desenlace
            </button>
          </div>
          {replayResult ? (
            <p>
              {replayResult.status === "prediction_not_saved"
                ? replayResult.reason
                : replayResult.excluded_reason
                  ? replayResult.excluded_reason
                  : `Análogo ${replayResult.analog_c?.toFixed(3) ?? "no disponible"} °C. Persistencia ${replayResult.persistence_c.toFixed(3)} °C. Climatología ${replayResult.climatology_c.toFixed(3)} °C.`}
              {replayResult.outcome_c !== null && replayResult.outcome_c !== undefined
                ? ` Desenlace ${replayResult.outcome_c.toFixed(3)} °C. Error del análogo ${replayResult.analog_error_c?.toFixed(3) ?? "no disponible"} °C.`
                : " El desenlace todavía no se mostró."}
            </p>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
