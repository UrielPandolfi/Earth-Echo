import { useEffect, useMemo, useState } from "react";
import type { SentryAssessments, SentryObject, SentryObjectDetail, SentryScenario } from "../domain/generated";

const api = import.meta.env.VITE_API_BASE ?? "/api";
type SortKey = "probability" | "palermo" | "torino" | "diameter" | "designation" | "impacts";

function reading(value: number, text: string): string {
  if (!(value > 0)) return text;
  if (value >= 0.001) return `${text} · ${(value * 100).toLocaleString("es-AR", { maximumSignificantDigits: 4 })} %`;
  return `${text} · cerca de 1 en ${Number((1 / value).toPrecision(2)).toLocaleString("es-AR")}`;
}

export function sentrySentence(object: SentryObject): string {
  if (object.status === "removed") {
    const when = object.removed_at ? ` (${object.removed_at} UTC)` : "";
    return `${object.fullname} figura como retirado de la tabla vigente de Sentry${when}. Ese retiro no confirma un impacto.`;
  }
  if (object.status === "not_listed" || !object.cumulative_probability_text) return "Sentry no publicó una probabilidad acumulada para esta designación.";
  return `Para ${object.fullname}, Sentry publica una probabilidad acumulada de impacto de ${object.cumulative_probability_text} dentro de los años ${object.year_range ?? "no informados"}. No es una fecha, un lugar ni una alerta de emergencia.`;
}

export function scenarioSentence(object: SentryObject, scenario: SentryScenario): string {
  return `El escenario virtual de ${object.fullname} con fecha publicada ${scenario.date_text} tiene una probabilidad de ${scenario.probability_text}. Es un impacto posible de la evaluación, no un impacto anunciado.`;
}

export function SentryForecastView({ assessments, detail: provided }: { assessments: SentryAssessments; detail?: SentryObjectDetail | null }) {
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<SortKey>("probability");
  const [removedView, setRemovedView] = useState(false);
  const [designation, setDesignation] = useState<string | null>(null);
  const [visible, setVisible] = useState(30);
  const [loaded, setLoaded] = useState<SentryObjectDetail | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const source = removedView ? assessments.removed : assessments.objects;
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const rows = source.filter((item) => !needle || item.designation.toLowerCase().includes(needle) || item.fullname.toLowerCase().includes(needle));
    const number = (value: number | null | undefined) => value ?? Number.NEGATIVE_INFINITY;
    const ordered = [...rows].sort((a, b) => {
      if (sort === "designation") return a.designation.localeCompare(b.designation);
      if (sort === "palermo") return number(b.palermo_max) - number(a.palermo_max);
      if (sort === "torino") return number(b.torino_max) - number(a.torino_max);
      if (sort === "diameter") return number(b.diameter_km) - number(a.diameter_km);
      if (sort === "impacts") return number(b.potential_impacts) - number(a.potential_impacts);
      return number(b.cumulative_probability) - number(a.cumulative_probability);
    });
    return ordered;
  }, [source, query, sort]);
  const selected = filtered.find((item) => item.designation === designation) ?? filtered[0] ?? null;
  useEffect(() => {
    if (provided !== undefined || !selected || selected.status !== "current") {
      setLoaded(null);
      return;
    }
    const controller = new AbortController();
    setDetailError(null);
    void fetch(`${api}/v1/forecasts/impacts/d29/object?des=${encodeURIComponent(selected.designation)}`, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error("El detalle de Sentry no está disponible.");
        return await response.json() as SentryObjectDetail;
      })
      .then((body) => { if (!controller.signal.aborted) setLoaded(body); })
      .catch((error: unknown) => { if (!controller.signal.aborted) setDetailError(error instanceof Error ? error.message : "El detalle de Sentry no está disponible."); });
    return () => controller.abort();
  }, [provided, selected]);
  if (assessments.status !== "available") return <p role="status">{assessments.reason ?? "No hay una evaluación Sentry retenida."}</p>;
  const candidate = provided !== undefined ? provided : loaded;
  const detail = candidate && selected && candidate.designation === selected.designation ? candidate : null;
  const scenario = detail?.scenarios[0] ?? null;
  const widest = detail?.scenarios.reduce((max, item) => Math.max(max, item.probability), 0) ?? 0;
  return (
    <section className="sentry-view" aria-label="Evaluaciones de impacto de Sentry">
      <h3>Asteroides conocidos · Sentry</h3>
      <p>{assessments.meaning}</p>
      <label className="forecast-control">Buscar designación o nombre
        <input aria-label="Buscar asteroide" value={query} onChange={(input) => { setQuery(input.target.value); setVisible(30); }} />
      </label>
      <label className="forecast-control">Ordenar por
        <select aria-label="Orden de la tabla Sentry" value={sort} onChange={(input) => setSort(input.target.value as SortKey)}>
          <option value="probability">Probabilidad acumulada</option>
          <option value="palermo">Palermo máximo</option>
          <option value="torino">Torino máximo</option>
          <option value="diameter">Diámetro estimado</option>
          <option value="impacts">Escenarios publicados</option>
          <option value="designation">Designación</option>
        </select>
      </label>
      <div className="forecast-control">
        <button type="button" aria-pressed={!removedView} onClick={() => { setRemovedView(false); setDesignation(null); }}>Vigentes · {assessments.objects.length}</button>
        <button type="button" aria-pressed={removedView} onClick={() => { setRemovedView(true); setDesignation(null); }}>Retirados · {assessments.removed.length}</button>
      </div>
      <p className="fine">{filtered.length} coincidencias. La tabla vigente no es el catálogo de todos los objetos del sistema solar.</p>
      <div className="sentry-list" role="list">
        {filtered.slice(0, visible).map((item) => (
          <button key={item.designation} type="button" role="listitem" aria-current={item.designation === selected?.designation} onClick={() => setDesignation(item.designation)}>
            <strong>{item.fullname}</strong>
            <span>{item.status === "removed" ? `Retirado ${item.removed_at ?? ""}` : item.cumulative_probability_text}</span>
          </button>
        ))}
      </div>
      {visible < filtered.length ? <button type="button" onClick={() => setVisible((count) => count + 30)}>Mostrar más</button> : null}
      {!selected ? <p role="status">Ningún objeto coincide con la búsqueda.</p> : <>
        <p>{sentrySentence(selected)}</p>
        {selected.cumulative_probability != null && selected.cumulative_probability_text ? <p className="forecast-result">{reading(selected.cumulative_probability, selected.cumulative_probability_text)}</p> : null}
        <p className="fine">Probabilidad acumulada del objeto. Años evaluados: {selected.year_range ?? "no informados"}. Última observación usada: {selected.last_observation ?? "no informada"}.</p>
        <dl className="facts">
          <div><dt>Torino máximo</dt><dd>{selected.torino_max ?? "No publicado"}</dd></div>
          <div><dt>Palermo máximo</dt><dd>{selected.palermo_max ?? "No publicado"}</dd></div>
          <div><dt>Palermo acumulado</dt><dd>{selected.palermo_cumulative ?? "No publicado"}</dd></div>
          <div><dt>Diámetro estimado</dt><dd>{selected.diameter_km == null ? "No publicado" : `${selected.diameter_km} km`}</dd></div>
          <div><dt>Magnitud absoluta H</dt><dd>{selected.absolute_magnitude_h ?? "No publicada"}</dd></div>
          <div><dt>Velocidad de exceso v∞</dt><dd>{selected.v_inf_km_s == null ? "No publicada" : `${selected.v_inf_km_s} km/s`}</dd></div>
          <div><dt>Escenarios en la tabla</dt><dd>{selected.potential_impacts ?? "No publicado"}</dd></div>
        </dl>
        <p className="fine">El diámetro es una estimación, normalmente a partir del brillo y un albedo supuesto. La masa y la velocidad de entrada no vienen en esta tabla resumida y no se completan.</p>
        <figure className="sentry-sketch"><span className="earth">Tierra</span><span className="rock" /><figcaption>Esquema ilustrativo. No es una órbita, una trayectoria ni un punto de impacto.</figcaption></figure>
        {detailError ? <p role="status">{detailError}</p> : null}
        {selected.status === "current" && detail?.scenarios_status === "missing_input" ? <p role="status">{detail.scenarios_reason}</p> : null}
        {selected.status === "removed" ? <p>{SENTRY_REMOVED}</p> : null}
        {scenario ? <>
          <p>{scenarioSentence(selected, scenario)}</p>
          <p className="fine">Fecha publicada {scenario.date_text}{scenario.date_utc ? ` · instante UTC interpretado ${scenario.date_utc}` : ""}. Energía {scenario.energy_mt ?? "no publicada"} Mt. Método {scenario.method ?? "no publicado"}.</p>
          <div className="sentry-list" role="list" aria-label="Escenarios virtuales">
            {detail?.scenarios.slice(0, 12).map((item) => (
              <div key={`${item.date_text}-${item.probability_text}`} role="listitem">
                <span>{item.date_text}</span>
                <span className="enso-stack" aria-hidden="true"><i className="nino" style={{ width: `${widest > 0 ? (item.probability / widest) * 100 : 0}%` }} /></span>
                <span>{reading(item.probability, item.probability_text)}</span>
              </div>
            ))}
          </div>
          <p className="fine">El ancho compara los escenarios de este objeto entre sí. No es un mapa de riesgo ni una probabilidad nueva. {detail && detail.scenarios.length > 12 ? `Hay ${detail.scenarios.length} escenarios; se muestran los 12 de mayor probabilidad publicada.` : null}</p>
        </> : null}
        <h3>Cómo leer estas cifras</h3>
        <p>Una probabilidad de impacto es la estimación publicada de que ese objeto, con la órbita y las observaciones usadas, alcance la Tierra en el período indicado. Puede bajar o desaparecer cuando un observatorio agrega posiciones. Una cifra muy pequeña sigue siendo una probabilidad, no un impacto confirmado, y no se redondea hasta hacerla desaparecer.</p>
        <p>Un acercamiento cercano es un paso a cierta distancia. Un impacto virtual es un escenario en el que alguna de las órbitas posibles toca la Tierra. Sentry evalúa objetos ya descubiertos; no dice nada de un objeto que todavía nadie observó.</p>
        <p>{assessments.limitation}</p>
        <p className="fine">Tabla recuperada {assessments.retrieved_at}. Versión de la API {assessments.signature_version}. SHA-256 {assessments.checksum_sha256}.</p>
        <p><a href={`${api}/v1/forecasts/impacts/d29.csv`}>Descargar tabla CSV</a>{selected.status === "current" ? <> · <a href={`${api}/v1/forecasts/impacts/d29.csv?des=${encodeURIComponent(selected.designation)}`}>CSV de escenarios</a></> : null} · <a href={assessments.source_url} target="_blank" rel="noreferrer">API Sentry</a></p>
      </>}
    </section>
  );
}

const SENTRY_REMOVED = "La tabla de retirados publica la designación y la hora del retiro. No conserva la probabilidad anterior y Earth Echo no la reconstruye.";
