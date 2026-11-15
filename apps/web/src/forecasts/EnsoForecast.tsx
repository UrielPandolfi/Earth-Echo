import type { EnsoOutlook, EnsoPhase } from "../domain/generated";

const api = import.meta.env.VITE_API_BASE ?? "/api";

export function ensoSentence(phase: EnsoPhase): string {
  return `Para ${phase.season}, NOAA estima ${phase.el_nino_percent}% de probabilidad de El Niño, ${phase.neutral_percent}% de fase neutral y ${phase.la_nina_percent}% de La Niña.`;
}

export function EnsoStack({ phase }: { phase: EnsoPhase }) {
  return (
    <span className="enso-stack" aria-hidden="true">
      <i className="nina" style={{ width: `${phase.la_nina_percent}%` }} />
      <i className="neutral" style={{ width: `${phase.neutral_percent}%` }} />
      <i className="nino" style={{ width: `${phase.el_nino_percent}%` }} />
    </span>
  );
}

export function EnsoForecastView({ outlook, selected, onSelect, onFocus }: {
  outlook: EnsoOutlook;
  selected: string | null;
  onSelect: (season: string) => void;
  onFocus?: () => void;
}) {
  const phase = outlook.phases.find((item) => item.season === selected) ?? outlook.phases[0] ?? null;
  return (
    <section className="enso-view" aria-label="Pronóstico ENSO">
      <h3>El Niño / La Niña</h3>
      <p className="fine">Edición {outlook.edition ?? "no informada"}. {outlook.issue_time_basis}</p>
      {outlook.observation ? (
        <p>Índice observado más reciente: {outlook.observation.season_id}, RONI {outlook.observation.roni_c} °C, fase de ese trimestre {outlook.observation.season_phase}. {outlook.observation.note}</p>
      ) : (
        <p>No hay una observación RONI compatible para mostrar un estado actual. El pronóstico de abajo no la reemplaza.</p>
      )}
      {outlook.status !== "available" || !phase ? <p role="status">{outlook.reason ?? "Sin probabilidades oficiales."}</p> : <>
        <label className="forecast-control">Trimestre
          <select aria-label="Trimestre ENSO" value={phase.season} onChange={(event) => onSelect(event.target.value)}>
            {outlook.phases.map((item) => <option key={item.season} value={item.season}>{item.season}</option>)}
          </select>
        </label>
        <p>{ensoSentence(phase)}</p>
        <EnsoStack phase={phase} />
        <p className="fine enso-key"><span className="nina" /> La Niña <span className="neutral" /> Neutral <span className="nino" /> El Niño{phase.roni_p50_c != null ? ` · mediana RONI ${phase.roni_p50_c} °C` : ""}</p>
        <div className="enso-seasons" role="list" aria-label="Probabilidades por trimestre">
          {outlook.phases.map((item) => (
            <button key={item.season} type="button" role="listitem" aria-current={item.season === phase.season} onClick={() => onSelect(item.season)}>
              <span>{item.season}</span>
              <EnsoStack phase={item} />
            </button>
          ))}
        </div>
      </>}
      <h3>¿Qué significa para el planeta?</h3>
      <p>{outlook.meaning}</p>
      {onFocus ? <button type="button" onClick={onFocus}>Encuadrar Niño 3.4</button> : null}
      <p className="fine">{outlook.limitation}</p>
      <p><a href={`${api}/v1/forecasts/enso/d48.csv`}>Descargar probabilidades CSV</a> · <a href={outlook.source_url} target="_blank" rel="noreferrer">Tabla oficial CPC</a> · <a href={outlook.discussion_url} target="_blank" rel="noreferrer">Discusión ENSO</a></p>
    </section>
  );
}
