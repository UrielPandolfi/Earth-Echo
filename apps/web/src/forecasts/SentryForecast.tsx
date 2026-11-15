import { useEffect, useMemo, useState } from "react";
import type { SentryAssessments, SentryObject, SentryObjectDetail, SentryScenario } from "../domain/generated";

const api = import.meta.env.VITE_API_BASE ?? "/api";
type SortKey = "probability" | "palermo" | "torino" | "diameter" | "designation" | "impacts";
const months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
const references = [
  { name: "Persona", meters: 1.7, note: "estatura adulta habitual" },
  { name: "Automóvil", meters: 4.5, note: "largo habitual" },
  { name: "Colectivo", meters: 12, note: "largo habitual" },
];

function odds(value: number): string {
  const count = Number((1 / value).toPrecision(2));
  return `cerca de 1 de cada ${count.toLocaleString("es-AR")}`;
}

export function reading(value: number, text: string): string {
  if (!(value > 0)) return text;
  if (value >= 0.0001) return `${(value * 100).toLocaleString("es-AR", { maximumFractionDigits: 2 })} % · ${odds(value)}`;
  return `${text} · ${odds(value)}`;
}

export function diameterText(km: number | null | undefined): string | null {
  if (km == null || !(km > 0)) return null;
  const meters = km * 1000;
  if (meters < 1000) return `${meters.toLocaleString("es-AR", { maximumSignificantDigits: 3 })} m`;
  return `${km.toLocaleString("es-AR", { maximumSignificantDigits: 3 })} km`;
}

export function scenarioDate(text: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})\.(\d+)$/.exec(text);
  if (!match) return text;
  const month = months[Number(match[2]) - 1];
  if (!month) return text;
  return `${Number(match[3])} de ${month} de ${match[1]} · fracción .${match[4]} del día UTC`;
}

export function sentrySentence(object: SentryObject): string {
  if (object.status === "removed") {
    const when = object.removed_at ? ` (${object.removed_at} UTC)` : "";
    return `${object.fullname} figura como retirado de la tabla vigente de Sentry${when}. Ese retiro no confirma un impacto.`;
  }
  if (object.status === "not_listed" || object.cumulative_probability == null || !object.cumulative_probability_text) return "Sentry no publicó una probabilidad acumulada para esta designación.";
  const years = object.year_range ?? "evaluados";
  if (object.cumulative_probability >= 0.0001) return `NASA estima una probabilidad del ${(object.cumulative_probability * 100).toLocaleString("es-AR", { maximumFractionDigits: 2 })} % de impacto de este objeto durante los años ${years}.`;
  return `NASA publica una probabilidad de ${object.cumulative_probability_text} para este objeto durante los años ${years}. No es una alerta de emergencia.`;
}

export function scenarioSentence(object: SentryObject, scenario: SentryScenario): string {
  return `El escenario virtual de ${object.fullname} con fecha publicada ${scenario.date_text} tiene una probabilidad de ${scenario.probability_text}. Es un impacto posible de la evaluación, no un impacto anunciado.`;
}

export function useSentryBoard(assessments: SentryAssessments | null, live = true) {
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<SortKey>("probability");
  const [removedView, setRemovedView] = useState(false);
  const [designation, setDesignation] = useState<string | null>(null);
  const [visible, setVisible] = useState(8);
  const [loaded, setLoaded] = useState<SentryObjectDetail | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);
  const source = assessments?.status === "available" ? (removedView ? assessments.removed : assessments.objects) : [];
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const rows = source.filter((item) => !needle || item.designation.toLowerCase().includes(needle) || item.fullname.toLowerCase().includes(needle));
    const number = (value: number | null | undefined) => value ?? Number.NEGATIVE_INFINITY;
    return [...rows].sort((a, b) => {
      if (sort === "designation") return a.designation.localeCompare(b.designation);
      if (sort === "palermo") return number(b.palermo_max) - number(a.palermo_max);
      if (sort === "torino") return number(b.torino_max) - number(a.torino_max);
      if (sort === "diameter") return number(b.diameter_km) - number(a.diameter_km);
      if (sort === "impacts") return number(b.potential_impacts) - number(a.potential_impacts);
      return number(b.cumulative_probability) - number(a.cumulative_probability);
    });
  }, [source, query, sort]);
  const selected = filtered.find((item) => item.designation === designation) ?? filtered[0] ?? null;
  useEffect(() => {
    if (!live || !selected || selected.status !== "current") {
      setLoaded(null);
      return;
    }
    const controller = new AbortController();
    setDetailError(null);
    setShowAll(false);
    void fetch(`${api}/v1/forecasts/impacts/d29/object?des=${encodeURIComponent(selected.designation)}`, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error("El detalle de Sentry no está disponible.");
        return await response.json() as SentryObjectDetail;
      })
      .then((body) => { if (!controller.signal.aborted) setLoaded(body); })
      .catch((error: unknown) => { if (!controller.signal.aborted && !(error instanceof DOMException && error.name === "AbortError")) setDetailError(error instanceof Error ? error.message : "El detalle de Sentry no está disponible."); });
    return () => controller.abort();
  }, [selected?.designation, selected?.status, live]);
  const detail = loaded && selected && loaded.designation === selected.designation ? loaded : null;
  return { assessments, query, setQuery, sort, setSort, removedView, setRemovedView, setDesignation, visible, setVisible, filtered, selected, detail, detailError, showAll, setShowAll };
}

export type SentryBoard = ReturnType<typeof useSentryBoard>;

export function SentryNotes({ board, part }: { board: SentryBoard; part: "top" | "bottom" }) {
  const selected = board.selected;
  const count = board.assessments?.objects.length;
  const size = diameterText(selected?.diameter_km);
  const meters = selected?.diameter_km != null ? selected.diameter_km * 1000 : null;
  const scaleMax = Math.max(meters ?? 0, ...references.map((item) => item.meters), 1);
  if (part === "top") return (
    <div className="stat-grid" aria-label="Resumen del objeto seleccionado">
      <article className="stat-card"><span>Objetos evaluados</span><strong>{count ?? "—"}</strong><small>Tabla vigente de Sentry</small></article>
      <article className="stat-card"><span>Probabilidad publicada</span><strong>{selected?.cumulative_probability != null && selected.cumulative_probability >= 0.0001 ? `${(selected.cumulative_probability * 100).toLocaleString("es-AR", { maximumFractionDigits: 2 })} %` : selected?.cumulative_probability_text ?? "—"}</strong><small>{selected ? selected.fullname : "Sin objeto seleccionado"}</small></article>
      <article className="stat-card"><span>Años evaluados</span><strong>{selected?.year_range ?? "—"}</strong><small>Intervalo publicado, no una fecha</small></article>
      <article className="stat-card"><span>Tamaño estimado</span><strong>{size ?? "Sin dato"}</strong><small>{selected?.potential_impacts ?? "—"} escenarios publicados</small></article>
    </div>
  );
  return <>
    <article className="plain-card">
      <h2>Sentry no publica un lugar exacto de impacto</h2>
      <p>Por eso el mapa no muestra puntos sobre la Tierra. La roca que acompaña al globo es una forma genérica, no la órbita ni la posición real de {selected?.fullname ?? "el objeto"}.</p>
      <div className="chip-row"><span>La Tierra es el globo real</span><span>Sin ubicación de impacto</span></div>
    </article>
    <section className="plain-card" aria-label="Comparación de tamaño a escala">
      <h2>¿Qué tan grande es este asteroide?</h2>
      {meters == null ? <p>Sentry no publicó un diámetro estimado para este objeto. No se inventó un tamaño.</p> : <>
        <p>{selected?.fullname} · diámetro estimado {size}. La comparación usa la misma escala. Las referencias son tamaños habituales, no mediciones de un objeto concreto.</p>
        <div className="size-scale">
          <div><span>{selected?.designation}</span><i style={{ width: `${(meters / scaleMax) * 100}%` }} /><b>{size}</b></div>
          {references.map((item) => <div className="ref" key={item.name}><span>{item.name}</span><i style={{ width: `${(item.meters / scaleMax) * 100}%` }} /><b>{item.meters.toLocaleString("es-AR")} m · {item.note}</b></div>)}
        </div>
      </>}
    </section>
  </>;
}

export function SentryForecastView({ assessments, detail: provided, board }: { assessments: SentryAssessments; detail?: SentryObjectDetail | null; board?: SentryBoard }) {
  const local = useSentryBoard(board ? null : assessments, !board && provided === undefined);
  const state = board ?? local;
  const [science, setScience] = useState(false);
  if (assessments.status !== "available") return <p role="status">{assessments.reason ?? "No hay una evaluación Sentry retenida."}</p>;
  const selected = state.selected;
  const detail = provided !== undefined ? (provided && selected && provided.designation === selected.designation ? provided : null) : state.detail;
  const shown = detail ? (state.showAll ? detail.scenarios : detail.scenarios.slice(0, 6)) : [];
  return (
    <section className="sentry-view" aria-label="Evaluaciones de impacto de Sentry">
      <h3>Impactos de asteroides conocidos</h3>
      <p>Mostramos evaluaciones oficiales de NASA/JPL Sentry para asteroides ya descubiertos.</p>
      <details><summary>¿Qué significa?</summary><p>Sentry calcula la probabilidad de que un asteroide pueda impactar en la Tierra en ciertos años. Son posibilidades, no impactos confirmados.</p></details>
      <label className="forecast-control">Buscar asteroide
        <input aria-label="Buscar asteroide" placeholder="Ej. 2010 RF12" value={state.query} onChange={(input) => { state.setQuery(input.target.value); state.setVisible(8); }} />
      </label>
      <label className="forecast-control">Ordenar por
        <select aria-label="Orden de la tabla Sentry" value={state.sort} onChange={(input) => state.setSort(input.target.value as SortKey)}>
          <option value="probability">Probabilidad acumulada</option>
          <option value="palermo">Palermo máximo</option>
          <option value="torino">Torino máximo</option>
          <option value="diameter">Diámetro estimado</option>
          <option value="impacts">Escenarios publicados</option>
          <option value="designation">Designación</option>
        </select>
      </label>
      <div className="chip-row">
        <button type="button" aria-pressed={!state.removedView} onClick={() => { state.setRemovedView(false); state.setDesignation(null); }}>Vigentes · {assessments.objects.length}</button>
        <button type="button" aria-pressed={state.removedView} onClick={() => { state.setRemovedView(true); state.setDesignation(null); }}>Retirados · {assessments.removed.length}</button>
      </div>
      <p className="fine">{state.filtered.length} coincidencias. Esta tabla no es el catálogo de todos los objetos del sistema solar.</p>
      <div className="product-table"><table className="sentry-table"><thead><tr><th>Asteroide</th><th>Probabilidad</th><th>Interpretación</th><th>Período</th></tr></thead><tbody>
        {state.filtered.slice(0, state.visible).map((item) => (
          <tr key={item.designation} aria-selected={item.designation === selected?.designation}>
            <td><button type="button" onClick={() => state.setDesignation(item.designation)}>{item.fullname}</button></td>
            <td>{item.cumulative_probability == null ? "Retirado" : item.cumulative_probability >= 0.0001 ? `${(item.cumulative_probability * 100).toLocaleString("es-AR", { maximumFractionDigits: 2 })} %` : item.cumulative_probability_text}</td>
            <td>{item.cumulative_probability != null && item.cumulative_probability > 0 ? odds(item.cumulative_probability) : "Sin probabilidad publicada"}</td>
            <td>{item.year_range ?? item.removed_at ?? "—"}</td>
          </tr>
        ))}
      </tbody></table></div>
      {state.visible < state.filtered.length ? <button type="button" onClick={() => state.setVisible((count) => count + 12)}>Mostrar más</button> : null}
      {!selected ? <p role="status">Ningún objeto coincide con la búsqueda.</p> : <>
        <article className="plain-card">
          <p className="fine">{selected.fullname} {selected.status === "current" ? "No es una alerta" : "Retirado de la tabla vigente"}</p>
          <h2>{selected.designation}</h2>
          <p>{sentrySentence(selected)}</p>
          {selected.cumulative_probability != null && selected.cumulative_probability_text ? <p className="forecast-result">{reading(selected.cumulative_probability, selected.cumulative_probability_text)}</p> : null}
          <dl className="facts">
            <div><dt>Años evaluados</dt><dd>{selected.year_range ?? "No informados"}</dd></div>
            <div><dt>Diámetro estimado</dt><dd>{diameterText(selected.diameter_km) ?? "No publicado"}</dd></div>
            <div><dt title="La escala de Torino va de 0 a 10. Un 0 publicado no significa que el impacto sea imposible.">Torino</dt><dd>{selected.torino_max ?? "No publicado"}</dd></div>
            <div><dt title="Palermo es una escala técnica logarítmica. Un valor negativo no es un porcentaje.">Palermo máx.</dt><dd>{selected.palermo_max ?? "No publicado"}</dd></div>
            <div><dt>Última observación usada</dt><dd>{selected.last_observation ?? "No informada"}</dd></div>
          </dl>
        </article>
        {state.detailError ? <p role="status">{state.detailError}</p> : null}
        {selected.status === "removed" ? <p>La tabla de retirados publica la designación y la hora del retiro. No conserva la probabilidad anterior y Earth Echo no la reconstruye.</p> : null}
        {detail?.scenarios_status === "missing_input" ? <p role="status">{detail.scenarios_reason}</p> : null}
        {shown.length ? <section aria-label="Escenarios virtuales"><h3>Escenarios más probables</h3>
          {shown.map((item) => <article key={`${item.date_text}-${item.probability_text}`} className="info-card"><span>{scenarioDate(item.date_text)}</span><strong>{item.probability >= 0.0001 ? `${(item.probability * 100).toLocaleString("es-AR", { maximumFractionDigits: 2 })} %` : item.probability_text}</strong><p>{scenarioSentence(selected, item)}</p><p className="fine">{odds(item.probability)}. Energía {item.energy_mt ?? "no publicada"} Mt. Método {item.method ?? "no publicado"}.</p></article>)}
          {detail && detail.scenarios.length > 6 && !state.showAll ? <button type="button" onClick={() => state.setShowAll(true)}>Ver los {detail.scenarios.length} escenarios</button> : null}
        </section> : null}
        <button type="button" aria-expanded={science} onClick={() => setScience((open) => !open)}>{science ? "Ocultar detalle científico" : "Detalle científico"}</button>
        {science ? <div className="info-card"><p>Magnitud absoluta H: {selected.absolute_magnitude_h ?? "no publicada"}. Velocidad de exceso: {selected.v_inf_km_s == null ? "no publicada" : `${selected.v_inf_km_s} km/s`}. Palermo acumulado: {selected.palermo_cumulative ?? "no publicado"}.</p><p>{assessments.limitation}</p><p className="fine">Tabla recuperada {assessments.retrieved_at}. Versión de la API {assessments.signature_version}. SHA-256 {assessments.checksum_sha256}.</p><p><a href={`${api}/v1/forecasts/impacts/d29.csv`}>Descargar tabla CSV</a>{selected.status === "current" ? <> · <a href={`${api}/v1/forecasts/impacts/d29.csv?des=${encodeURIComponent(selected.designation)}`}>CSV de escenarios</a></> : null} · <a href={assessments.source_url} target="_blank" rel="noreferrer">API Sentry</a></p></div> : null}
      </>}
    </section>
  );
}
