import type { AftershockEvent, AftershockForecasts } from "../domain/generated";

const api = import.meta.env.VITE_API_BASE ?? "/api";
const stateLabel = { future: "Futuro", in_progress: "En curso", expired: "Vencido", unknown: "Validez desconocida" };
const horizonName: Record<string, string> = { "1 Day": "1 día", "1 Week": "1 semana", "1 Month": "1 mes", "1 Year": "1 año" };

function percent(value: number): string {
  const pct = value * 100;
  const text = pct >= 1
    ? pct.toLocaleString("es-AR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    : pct.toLocaleString("es-AR", { maximumSignificantDigits: 4 });
  return `${text} %`;
}

export function aftershockSentence(event: AftershockEvent, label: string, magnitude: number, probability: number): string {
  const shock = event.magnitude == null ? `el evento ${event.event_id}` : `el terremoto de magnitud ${event.magnitude}`;
  return `Tras ${shock}, el USGS estima una probabilidad de ${percent(probability)} de que ocurra al menos una réplica de magnitud ${magnitude} o superior durante ${label}.`;
}

export function AftershockForecastView({ forecasts, eventId, windowLabel, magnitude, onEvent, onWindow, onMagnitude, onFocus }: {
  forecasts: AftershockForecasts;
  eventId: string | null;
  windowLabel: string | null;
  magnitude: number | null;
  onEvent: (id: string) => void;
  onWindow: (label: string) => void;
  onMagnitude: (value: number) => void;
  onFocus?: () => void;
}) {
  const event = forecasts.events.find((item) => item.event_id === eventId) ?? forecasts.events[0] ?? null;
  const horizon = event?.windows.find((item) => item.label === windowLabel) ?? event?.windows.find((item) => item.temporal_state !== "expired") ?? event?.windows[0] ?? null;
  const bin = horizon?.bins.find((item) => item.magnitude === magnitude) ?? horizon?.bins[0] ?? null;
  if (forecasts.status !== "available" || !event || !horizon || !bin) {
    return <p role="status">{forecasts.reason ?? "No hay un pronóstico oficial de réplicas."}</p>;
  }
  return (
    <section className="oaf-view" aria-label="Pronóstico de réplicas">
      <p className="metric-label">Después del terremoto principal</p>
      <h3>{event.magnitude == null ? event.event_id : `Magnitud ${event.magnitude}`}</h3>
      <p className="fine">{event.event_id} · el punto del mapa es ese sismo, no el lugar de las réplicas.</p>
      {forecasts.events.length > 1 ? (
        <label className="forecast-control">Evento
          <select aria-label="Evento con pronóstico OAF" value={event.event_id} onChange={(input) => onEvent(input.target.value)}>
            {forecasts.events.map((item) => <option key={item.event_id} value={item.event_id}>{item.event_id} · M{item.magnitude ?? "—"}</option>)}
          </select>
        </label>
      ) : null}
      <label className="forecast-control">Durante cuánto tiempo
        <select aria-label="Horizonte de réplicas" value={horizon.label} onChange={(input) => onWindow(input.target.value)}>
          {event.windows.map((item) => <option key={item.label} value={item.label}>{horizonName[item.label] ?? item.label} · {stateLabel[item.temporal_state]}</option>)}
        </select>
      </label>
      <label className="forecast-control">Réplicas de magnitud
        <select aria-label="Umbral de magnitud" value={String(bin.magnitude)} onChange={(input) => onMagnitude(Number(input.target.value))}>
          {horizon.bins.map((item) => <option key={item.magnitude} value={item.magnitude}>M{item.magnitude} o mayor</option>)}
        </select>
      </label>
      {horizon.temporal_state === "expired" ? <p className="forecast-warning" role="status">Este plazo ya terminó. No describe lo que puede pasar ahora.</p> : null}
      <div className="metric-block">
        <p className="metric-label">Probabilidad de al menos una réplica</p>
        <p className="forecast-result">{percent(bin.probability)}</p>
        <p>{aftershockSentence(event, horizon.label, bin.magnitude, bin.probability)}</p>
        <p className="fine">Desde {new Date(horizon.valid_from).toISOString()} hasta {new Date(horizon.valid_to).toISOString()}.</p>
      </div>
      <p className="fine">Cantidad más probable: {bin.median_count ?? "no publicada"}. En 95 de cada 100 simulaciones del modelo, el conteo queda entre {bin.p95_minimum ?? "—"} y {bin.p95_maximum ?? "—"}.</p>
      <div className="enso-seasons" role="list" aria-label="Probabilidades por magnitud">
        {horizon.bins.map((item) => (
          <button key={item.magnitude} type="button" role="listitem" aria-current={item.magnitude === bin.magnitude} onClick={() => onMagnitude(item.magnitude)}>
            <span>M{item.magnitude}+</span>
            <span className="enso-stack" aria-hidden="true"><i className="nino" style={{ width: `${Math.max(item.probability * 100, item.probability > 0 ? 2 : 0)}%` }} /></span>
          </button>
        ))}
      </div>
      <details>
        <summary>De dónde sale este número</summary>
        <p className="fine">{event.geometry_note}</p>
        <p className="fine">Emitido {event.issued_at}. Versión {event.product_version}. Recuperado {event.retrieved_at}. Modelo: {event.model_name}.</p>
        <p>{forecasts.limitation}</p>
        <p><a href={`${api}/v1/forecasts/aftershocks/d22.csv`}>Descargar CSV</a> · <a href={event.original_url} target="_blank" rel="noreferrer">forecast.json del USGS</a></p>
      </details>
      {onFocus && event.latitude != null ? <button type="button" onClick={onFocus}>Encuadrar el terremoto principal</button> : null}
    </section>
  );
}
