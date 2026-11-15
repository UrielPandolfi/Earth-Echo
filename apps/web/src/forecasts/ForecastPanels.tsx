import {useState} from 'react';
import type {ForecastDescriptor,ProductList} from '../domain/generated';
import type {ForecastExplorer} from './useForecastExplorer';
import {AnomalyChart} from '../shell/AnomalyChart';
import {EnsoForecastView} from './EnsoForecast';
import {AftershockForecastView} from './AftershockForecast';
import {SentryForecastView, type SentryBoard} from './SentryForecast';

const api=import.meta.env.VITE_API_BASE ?? '/api';
export const temporalLabel={future:'Futuro',in_progress:'En curso',expired:'Archivado · vencido',unknown:'Validez desconocida'};
export function utc(value:string|null|undefined):string {
  return value ? new Date(value).toLocaleString('es-AR',{timeZone:'UTC',year:'numeric',month:'short',day:'2-digit',hour:'2-digit',minute:'2-digit'})+' UTC' : 'No informada';
}
export function period(f:ForecastDescriptor):string {
  if(f.temporal_semantics==='monthly_interval')return new Date(f.valid_from!).toLocaleDateString('es-AR',{timeZone:'UTC',month:'long',year:'numeric'});
  return f.valid_to ? `${utc(f.valid_from)} → ${utc(f.valid_to)}` : utc(f.valid_from);
}
export function percent(p:number):string{return (p*100).toLocaleString('es-AR',{maximumFractionDigits:1})+' %';}

export function ForecastPanel({explorer:x,products,onTechnical,onSelectPosition}:{explorer:ForecastExplorer;products:ProductList|null;onTechnical:()=>void;onSelectPosition:(p:{longitude:number;latitude:number})=>void}) {
  const entries=x.catalog?.forecasts ?? [];
  const choices=entries.filter(f=>x.selection.mode==='d16' ? f.source_id==='D16' : f.source_id==='D07' && ['2t','wind_speed_10m','tp'].includes(f.variable));
  const f=x.field?.forecast;
  const h=x.highlights;
  const future=entries.some(e=>e.source_id==='D16' && e.temporal_state==='future' && e.availability==='available');
  return <aside className="sidebar forecast-sidebar" aria-label="Pronósticos reales"><div className="sidebar-head"><h2>Pronósticos · REAL</h2></div><div className="sidebar-body">
    <p className="hint">Earth Echo muestra el resultado del organismo que lo calcula. No inventa otro número.</p>
    <label className="forecast-control">Producto<select aria-label="Producto predictivo" value={x.selection.mode} onChange={e=>x.setMode(e.target.value as 'd16'|'ifs'|'kp'|'enso'|'oaf'|'sentry')}>
      <option value="d16">◇ Calor marino · mensual</option><option value="ifs">◇ Meteorología · IFS +24 h</option><option value="enso">◇ El Niño / La Niña · estacional</option><option value="oaf">◇ Réplicas sísmicas · USGS</option><option value="sentry">◇ Asteroides · Sentry</option><option value="kp">◇ Kp · planetario</option>
    </select></label>
    {x.selection.mode!=='kp' && x.selection.mode!=='enso' && x.selection.mode!=='oaf' && x.selection.mode!=='sentry' && <label className="forecast-control">{x.selection.mode==='d16' ? 'Mes y corrida disponibles' : 'Variable y plazo disponible'}<select aria-label="Período del pronóstico" value={x.key ?? ''} onChange={e=>x.setPeriod(e.target.value)}>
      {!x.key && <option value="">Sin período disponible</option>}
      {x.key && !choices.some(c=>c.id===x.key) && <option value={x.key}>Selección ya no retenida</option>}
      {choices.map(c=><option value={c.id} key={c.id}>{x.selection.mode==='ifs' ? `${c.title} · ` : ''}{period(c)} · {temporalLabel[c.temporal_state]} · inicio {c.initialized_at?.slice(0,10) ?? 'desconocido'} · {c.id.slice(0,6)}</option>)}
    </select></label>}
    {x.error && <p role="status">{x.error} Se conserva el producto válido cargado, si existe.</p>}
    {x.selection.mode==='d16' && <>
      {x.catalog && !future && <p className="forecast-warning" role="status">No hay un mes completo futuro retenido. Podés consultar los períodos en curso o archivados.</p>}
      <p>Calor marino previsto · mensual</p><p className="fine">Probabilidad de superar el umbral mensual p90 de NOAA, referencia 1991–2020. Tendencia retenida.</p>
      <div className="legend-bar legend-real"/><div className="legend-scale"><span>0 %</span><span>50 %</span><span>100 %</span></div>
      <p className="hint">Probabilidad del evento · máscara transparente · malla 1°. Sin interpolación científica.</p>
      <label className="forecast-control">Filtro de exploración: ≥ {percent(x.selection.threshold)}<input aria-label="Filtro de probabilidad" type="range" min="0" max="100" step="5" value={x.selection.threshold*100} onChange={e=>x.setThreshold(Number(e.target.value)/100)}/></label>
      <p className="hint">Este filtro selecciona celdas; no cambia el p90 científico ni crea niveles de peligro.</p>
      <section aria-label="Áreas destacadas"><h3>Áreas destacadas del pronóstico</h3>
        {x.highlightError ? <p role="status">{x.highlightError}</p> : h ? <>
          {h.total_areas!=null && <p className="fine">{h.total_areas} áreas con este filtro · {h.returned_areas} mostradas · {h.matching_cells?.toLocaleString('es')} celdas. Son zonas para explorar, no alertas.</p>}
          {h.reason && <p role="status">{h.reason}</p>}
          <ol className="forecast-areas">{h.areas.map((a,index)=><li key={a.id}><button type="button" onClick={()=>onSelectPosition({longitude:a.representative.cell!.longitude,latitude:a.representative.cell!.latitude})}>
            <strong>Zona {index+1} · {a.cell_count.toLocaleString('es')} celdas</strong><span>{percent(a.probability_min)}–{percent(a.probability_max)} por celda</span><small>Representante {a.representative.cell!.latitude}°, {a.representative.cell!.longitude}°</small>
          </button></li>)}</ol>
          <details><summary>Regla de agrupación</summary><p className="fine">{h.rule}</p><p className="fine">El rango pertenece a las celdas. No es una probabilidad de toda la región. El mapa conserva el ráster, sin polígonos aproximados.</p></details>
        </> : <p role="status">{x.key ? 'Consultando el campo y sus destacados…' : 'Sin datos disponibles.'}</p>}
      </section>
    </>}
    {x.selection.mode==='ifs' && <><p>Un único plazo +24 h por corrida retenida.</p><p className="fine">Temperatura del aire a 2 m, rapidez del viento medio a 10 m y precipitación acumulada. No son probabilidades de desastre. Tocá el campo para consultar un valor.</p>
      {f && <><div className="legend-bar legend-real"/><div className="legend-scale"><span>{x.field?.grid?.minimum?.toLocaleString('es',{maximumFractionDigits:2}) ?? '—'}</span><span>{x.field?.grid?.maximum?.toLocaleString('es',{maximumFractionDigits:2}) ?? '—'} {f.unit}</span></div><p className="hint">{f.resolution}</p></>}
      <p className="fine">Variables con entrada retenida: {['2t','wind_speed_10m','tp'].map(v=>`${{ '2t':'temperatura',wind_speed_10m:'viento',tp:'precipitación'}[v]}: ${entries.some(e=>e.source_id==='D07' && e.variable===v && e.availability==='available') ? 'disponible' : 'ausente'}`).join(' · ')}.</p>
    </>}
    {x.selection.mode==='kp' && <><p>Kp previsto · índice planetario</p><p className="fine">La serie y las ventanas UTC están en el inspector. No hay coordenadas o intensidades locales.</p>{x.kpError && <p role="status">{x.kpError}</p>}</>}
    {x.selection.mode==='enso' && <><p>El Niño / La Niña · estacional</p><p className="fine">Probabilidades oficiales por trimestre. El recuadro del mapa es Niño 3.4, no un pronóstico para cada lugar.</p>{x.ensoError && <p role="status">{x.ensoError}</p>}</>}
    {x.selection.mode==='oaf' && <><p>Réplicas sísmicas · USGS</p><p className="fine">Solo los eventos para los que el USGS publicó un pronóstico. El punto es el terremoto principal.</p>{x.oafError && <p role="status">{x.oafError}</p>}</>}
    {x.selection.mode==='sentry' && <article className="info-card"><span>En pocas palabras</span><p>Sentry estudia asteroides conocidos y calcula posibilidades de impacto futuro. No significa que esos impactos vayan a suceder.</p>{x.sentryError && <p role="status">{x.sentryError}</p>}</article>}
    <hr/><p className="hint">{products?.observation_records?.toLocaleString('es') ?? '—'} observaciones · {products?.calculated_indicator_products ?? '—'} productos de indicadores calculados · {x.catalog?.own_experiments ?? '—'} experimento retrospectivo.</p>
    <button className="wide-toggle" type="button" onClick={onTechnical}>Todas las fuentes y productos técnicos</button>
    <details><summary>Otras capacidades y archivos</summary><p className="fine">Metadatos existentes; consulta geográfica aún no adaptada en esta entrega.</p><ul className="forecast-capabilities">{entries.filter(e=>!e.queryable && e.spatial_support!=='planetary').map(e=><li key={e.id}>{e.source_id} · {e.title} · {temporalLabel[e.temporal_state]} · {e.coverage}</li>)}</ul></details>
  </div></aside>;
}

function Dates({f}:{f:ForecastDescriptor}) {
  return <><dl className="facts"><div><dt>Inicialización</dt><dd>{utc(f.initialized_at)}</dd></div><div><dt>Emisión</dt><dd>{utc(f.issued_at)}</dd></div><div><dt>Recuperación</dt><dd>{utc(f.retrieved_at)}</dd></div><div><dt>Procesamiento</dt><dd>{utc(f.processed_at)}</dd></div><div><dt>Primera captura retenida</dt><dd>{utc(f.first_seen_at)}</dd></div></dl><p className="fine">{f.first_seen_basis}</p></>;
}
function Update({f}:{f:ForecastDescriptor}) {
  return <>{f.update?.error && <p role="status" className="forecast-warning">Actualización fallida: {f.update.error}. Se conserva el último válido en REAL.</p>}{f.update_pending && <p className="fine">Comprobación de actualización pendiente según la cadencia; la recuperación no cambia la corrida ni su validez.</p>}{f.update && <details><summary>Estado de actualización</summary><p className="fine">Último intento {utc(f.update.last_attempt_at)} · {f.update.status}. Última consulta satisfactoria {utc(f.update.last_success_at)}. Próximo intento {utc(f.update.next_attempt_at)}.</p></details>}</>;
}
function Method({f}:{f:ForecastDescriptor}) {
  return <><h3>Definición y procedencia</h3><p>{f.event_definition}</p>{f.scientific_threshold && <p>{f.scientific_threshold}</p>}<p className="fine">Referencia: {f.reference_period ?? 'No aplica'} · tendencia: {f.trend_treatment==='retained' ? 'retenida' : f.trend_treatment ?? 'No aplica'}.</p><p>{f.coverage}</p><p className="fine">Unidad nativa: {f.native_unit} · mostrada: {f.unit}.</p><p className="fine">{f.sampling}</p><p className="fine">{f.quality_mask}</p><p className="fine">Método: {f.method} · adaptador {f.adapter_version}</p>{f.calculation && <><p className="fine">{f.calculation.applicability} Parámetros: {JSON.stringify(f.calculation.parameters)}. {f.calculation.reference_period}</p>{f.calculation.inputs.map(i=><p key={i.product_id} className="fine">Entrada {i.product_id} · {i.variable} · {i.unit} · SHA {i.checksum_sha256}</p>)}</>}<p className="fine">{f.provider_version}</p><p className="fine">{f.identity_basis}</p><p className="fine">ID local: {f.id}</p><p className="fine">SHA-256 original: {f.original_sha256}</p><p><a href={api+f.original_download}>Descargar original retenido</a></p><p><a href={f.original_url} target="_blank" rel="noreferrer">Producto del proveedor</a> · <a href={f.reference_url} target="_blank" rel="noreferrer">Método y fuente oficial</a></p><p className="fine">{f.skill_note} No se calcularon Brier ni calibración local.</p></>;
}

export function ForecastInspector({explorer:x,onFocus,sentryBoard}:{explorer:ForecastExplorer;onFocus:()=>void;sentryBoard?:SentryBoard}) {
  const [tab,setTab]=useState<'summary'|'data'|'method'>('summary');
  if(x.selection.mode==='sentry'){
    return <aside className="inspector forecast-inspector" aria-label="Pronóstico seleccionado"><header className="inspector-head"><p className="kicker">Evaluación orbital · REAL</p><h2>Impactos de asteroides conocidos</h2><p className="region">NASA/JPL CNEOS · Sentry</p></header><div className="inspector-body">{x.sentry ? <SentryForecastView assessments={x.sentry} board={sentryBoard}/> : <p role="status">{x.sentryError ?? 'Consultando la tabla Sentry…'}</p>}</div></aside>;
  }
  if(x.selection.mode==='oaf'){
    return <aside className="inspector forecast-inspector" aria-label="Pronóstico seleccionado"><header className="inspector-head"><p className="kicker">◇ PRONÓSTICO OFICIAL · REAL</p><h2>Réplicas sísmicas</h2><p className="region">Después de un terremoto con producto OAF</p></header><div className="inspector-body">{x.oaf ? <AftershockForecastView forecasts={x.oaf} eventId={x.selection.eventId} windowLabel={x.selection.oafWindow} magnitude={x.selection.oafMagnitude} onEvent={x.setEvent} onWindow={x.setOafWindow} onMagnitude={x.setOafMagnitude} onFocus={onFocus}/> : <p role="status">{x.oafError ?? 'Consultando el pronóstico USGS…'}</p>}</div></aside>;
  }
  if(x.selection.mode==='enso'){
    return <aside className="inspector forecast-inspector" aria-label="Pronóstico seleccionado"><header className="inspector-head"><p className="kicker">◇ PRONÓSTICO OFICIAL · REAL</p><h2>El Niño / La Niña</h2><p className="region">Trimestres de tres meses · Niño 3.4</p></header><div className="inspector-body">{x.enso ? <EnsoForecastView outlook={x.enso} selected={x.selection.season} onSelect={x.setSeason} onFocus={onFocus}/> : <p role="status">{x.ensoError ?? 'Consultando las tablas oficiales de NOAA CPC…'}</p>}</div></aside>;
  }
  const planetary=x.selection.mode==='kp';
  const f=planetary ? x.kp?.forecast : x.field?.forecast;
  const p=x.point;
  const windows=x.kp?.windows ?? [];
  const remaining=windows.filter(w=>w.temporal_state!=='expired');
  return <aside className="inspector forecast-inspector" aria-label="Pronóstico seleccionado"><header className="inspector-head"><p className="kicker">◇ PRONÓSTICO {planetary ? 'PLANETARIO' : 'EXTERNO'} · REAL</p><h2>{f?.title ?? (planetary ? 'Kp previsto' : 'Elegí un pronóstico')}</h2>{f && <><p className="region">{period(f)} · {temporalLabel[f.temporal_state]}</p>{f.experimental && <p className="forecast-warning">Experimental · investigación</p>}</>}</header>
    <div className="tabs" role="tablist" aria-label="Detalles del pronóstico">{([['summary','Resumen'],['data','Datos'],['method','Método y fuente']] as const).map(([id,label])=><button key={id} type="button" role="tab" aria-selected={tab===id} onClick={()=>setTab(id)}>{label}</button>)}</div>
    <div className="inspector-body" key={x.key ?? 'kp'}>
      {!f ? <p role="status">{x.error ?? x.kpError ?? (planetary && x.kp ? x.kp.reason ?? 'Kp sin entrada disponible.' : x.key || planetary ? 'Consultando el producto real…' : 'No hay entradas retenidas para este recorrido.')}</p> : <>
        {f.temporal_state==='expired' && <p role="status" className="forecast-warning">Pronóstico archivado: su validez terminó. No describe el futuro actual.</p>}
        <Update f={f}/>
        {tab==='summary' ? <>
          <p>{f.event_definition}</p>
          {planetary ? <><h3>Alcance planetario</h3><p>Sin pines ni probabilidades locales de auroras. {remaining.length} ventanas futuras o en curso.</p>{x.kpError && <p role="status">{x.kpError}</p>}
            {!!windows.length && <AnomalyChart observedLabel="Kp previsto" points={windows.map(w=>({label:utc(w.valid_from),kind:'forecast',value:w.value}))} domain={{min:0,max:9,ticks:[9,6,3,0]}} caption="NOAA SWPC · Kp · ventanas de tres horas · UTC. Filas predicted del proveedor; no observación."/>}
            <div className="product-table"><table><thead><tr><th>Ventana UTC [inicio, fin)</th><th>Kp</th><th>Estado</th></tr></thead><tbody>{windows.map(w=><tr key={w.valid_from}><td>{utc(w.valid_from)} → {utc(w.valid_to)}</td><td>{w.value}</td><td>{temporalLabel[w.temporal_state]}</td></tr>)}</tbody></table></div>
          </> : <>
            {x.pointError ? <p role="status">{x.pointError}</p> : !p ? <p className="forecast-instruction" role="status">{x.selection.position ? 'Consultando la posición seleccionada…' : 'Tocá una celda del globo o un área destacada para ver el resultado.'}</p> : <section aria-label="Resultado de la celda">
              {p.status==='no_coverage' || p.status==='missing_input' || p.status==='not_implemented' ? <><h3>{p.status==='no_coverage' ? 'Sin cobertura en esta posición' : p.status==='missing_input' ? 'Entrada científica ausente' : 'Consulta no implementada'}</h3><p>{p.reason}</p></> : <><h3>{f.source_id==='D16' ? 'Calor marino mensual previsto' : 'Valor meteorológico previsto'}</h3><p className="forecast-result">{p.probability!=null ? percent(p.probability) : p.value!=null ? `${p.value.toLocaleString('es-AR',{maximumFractionDigits:2})} ${p.unit}` : 'Valor ausente'}</p><p>{p.probability!=null ? 'Probabilidad del evento mensual · calculada por NOAA PSL/NMME' : `Valor calculado por el proveedor${f.result_type==='derived_indicator' ? '; transformación física de Earth Echo documentada' : ''}`}</p></>}
              <p>{p.cell ? `${f.source_id==='D16' ? 'Celda oceánica de la malla' : 'Soporte de visualización'}: centro ${p.cell.latitude}°, ${p.cell.longitude}° WGS84` : `Posición ${p.requested_latitude}°, ${p.requested_longitude}° WGS84`}</p>
              <p className="fine">{p.cell?.support_note ?? f.resolution}</p><p>Objetivo: {period(f)} · UTC</p>
              {p.cell && <button className="wide-toggle" type="button" onClick={onFocus}>Encuadrar celda explícitamente</button>}
            </section>}
          </>}
          <p className="forecast-warning">{f.source_id==='D16' ? 'Umbral mensual del proveedor; no predice daño coralino ni un evento diario de cinco días.' : planetary ? x.kp?.note : f.limitation}</p>
          <p className="fine">Quién lo calcula: {f.provider}. Earth Echo aporta integración y consulta.</p><p className="fine">{f.skill_note}</p>
        </> : tab==='data' ? <>
          <h3>Datos científicos · UTC</h3><p>Validez: {utc(f.valid_from)}{f.valid_to ? ` → ${utc(f.valid_to)} (fin excluido)` : ' (instante)'}</p><p className="fine">Semántica: {f.temporal_semantics}. {f.resolution}</p>
          {p && !planetary && <><p>Probabilidad exacta [0–1]: {p.probability ?? 'No aplica / ausente'}</p><p>Valor: {p.value ?? 'No aplica / ausente'} {p.unit}</p><p>Celda: {p.cell?.id ?? 'Sin celda'}</p>{p.cell && <p className="fine">Límites WGS84: O {p.cell.extent.west}°, E {p.cell.extent.east}°, S {p.cell.extent.south}°, N {p.cell.extent.north}°. {p.cell.extent.crosses_antimeridian ? 'Celda partida en el antimeridiano.' : ''}</p>}<p className="fine">{p.selection_rule}</p><p><a href={`${api}/v1/forecasts/fields/${f.id}/point.csv?longitude=${p.requested_longitude}&latitude=${p.requested_latitude}`}>Descargar celda CSV exacta</a></p></>}
          <p><a href={api+f.metadata_download}>Datos y metadatos JSON de la versión</a></p><Dates f={f}/>
        </> : <><Method f={f}/><Dates f={f}/></>}
      </>}
    </div></aside>;
}

export function ForecastTime({explorer:x}:{explorer:ForecastExplorer}) {
  if(x.selection.mode==='enso')return <div className="product-time forecast-time" aria-label="Tiempo del pronóstico"><strong>◇ Pronóstico estacional · {x.enso?.edition ?? 'sin edición'}</strong><span>Trimestres superpuestos de tres meses · UTC</span><span className="fine">Emisión horaria no publicada por CPC. Recuperado {x.enso?.retrieved_at ?? 'sin fecha'}.</span></div>;
  if(x.selection.mode==='oaf'){const event=x.oaf?.events?.find(item=>item.event_id===x.selection.eventId) ?? x.oaf?.events?.[0]; return <div className="product-time forecast-time" aria-label="Tiempo del pronóstico"><strong>◇ Réplicas · {event?.event_id ?? 'sin evento'}</strong><span>Emitido {event?.issued_at ?? 'sin fecha'} · UTC</span><span className="fine">La vigencia de cada horizonte está en el inspector. Un horizonte vencido no describe el futuro actual.</span></div>;}
  if(x.selection.mode==='sentry')return <div className="product-time forecast-time" aria-label="Tiempo del pronóstico"><strong>◇ Sentry · objetos conocidos</strong><span>Tabla recuperada {x.sentry?.retrieved_at ?? 'sin fecha'} · UTC</span><span className="fine">La fecha de un escenario es una posibilidad publicada, no un impacto anunciado.</span></div>;
  const f=x.selection.mode==='kp' ? x.kp?.forecast : x.field?.forecast;
  return <div className="product-time forecast-time" aria-label="Tiempo del pronóstico"><strong>◇ Pronóstico externo · {f ? temporalLabel[f.temporal_state] : 'No disponible'}</strong><span>{f ? period(f) : 'Seleccioná una entrada real'} · UTC</span><span className="fine">Inicialización {f?.initialized_at ? utc(f.initialized_at) : 'no informada'} · emisión {f?.issued_at ? utc(f.issued_at) : 'no informada'}. {f?.temporal_semantics==='monthly_interval' ? 'No se interpola a días.' : ''}</span></div>;
}
