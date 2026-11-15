import type { ProductList, ScientificProduct,ProductTrack,ProductRegion,RefreshStatus } from '../domain/generated';
import { AnomalyChart } from '../shell/AnomalyChart';
import { CpcEnsoPanel } from './CpcEnsoPanel';
import { useEffect,useMemo,useState,useRef } from 'react';
import { fieldColorBounds } from './view';
const apiBase = import.meta.env.VITE_API_BASE ?? '/api';

function DistributorCredit({product}:{product:ScientificProduct}) {
  return product.license_url==='https://open-meteo.com/en/licence' ? <p className="fine"><a href="https://open-meteo.com/" target="_blank" rel="noreferrer">Weather data by Open-Meteo.com</a> · <a href={product.license_url} target="_blank" rel="noreferrer">CC BY4.0</a> · {product.source_id}</p> : null;
}

export function ProductFieldLegend({product}:{product:ScientificProduct}) {
  const grid=product.grid;
  if(!grid)return null;
  const centered=grid.color_center!=null;
  const [low,high]=fieldColorBounds(grid);
  return <>
    {grid.minimum==null || grid.maximum==null ? <p className="hint">Rango no disponible: no hay valores válidos.</p> : <>
      <div className={`legend-bar legend-real${centered ? ' legend-diverging' : grid.reverse_colors ? ' legend-real-reversed' : ''}`}/>
      <div className="legend-scale"><span>{low.toFixed(2)} {product.unit}</span>{centered && <span>{grid.color_center} {product.unit}</span>}<span>{high.toFixed(2)} {product.unit}</span></div>
    </>}
    <p className="hint">Escala {grid.color_scale==='log10' ? 'logarítmica log10' : 'lineal'} de color{centered ? ` centrada en ${grid.color_center}` : ''}; valores en {product.unit}.</p>
    {centered && <p className="hint">Azul: anomalía negativa. Centro neutro: cero válido. Naranja: positiva. Datos: {grid.minimum?.toFixed(2)} a {grid.maximum?.toFixed(2)} {product.unit}. Sin probabilidad de evento.</p>}
    {grid.reverse_colors && <p className="hint">Rojo: bajo percentil. Azul: alto percentil. No son probabilidades de eventos.</p>}
    <p className="hint">{grid.resolution}. {grid.missing_cells.toLocaleString('es')} celdas ausentes, transparentes.</p>
  </>;
}

export function productKindLabel(p: ScientificProduct): string {
  if(p.calculation) return p.representation==='field' ? 'Campo calculado' : 'Análisis descriptivo calculado';
  return {observation:'Observaciones',indicator:'Indicador importado',forecast:'Pronóstico externo',historical:'Archivo histórico',static_context:'Contexto geográfico',orbital_assessment:'Evaluación orbital'}[p.kind];
}

/** kind=forecast does not mean its validity is still in the future. */
export function productForecastState(p:Pick<ScientificProduct,'kind'|'valid_from'|'valid_to'>,now=Date.now()):string|null {
  if(p.kind!=='forecast')return null;
  const start=p.valid_from ? Date.parse(p.valid_from) : NaN;
  if(!Number.isFinite(start))return 'Validez no informada';
  if(start>now)return 'Futuro';
  const end=p.valid_to ? Date.parse(p.valid_to) : start;
  return (p.valid_to ? end<=now : start<now) ? 'Archivado · vencido' : 'En curso';
}

export function productTimeLabel(p: ScientificProduct): string {
  if(p.observed_at) return `Dato ${p.observed_at}`;
  if(p.valid_from) return `${p.valid_to ? 'Validez desde' : 'Fecha de validez'} ${p.valid_from}`;
  if(p.issued_at) return `Emisión ${p.issued_at}`;
  return `Recuperado ${p.retrieved_at}`;
}

export function ProductsPanel({ data, selected, activeProduct, refreshStatus, onSelect, onFocus, quakesOn, quakeCount, onQuakes, kpText, error, grouped, onGroup }: {
  data: ProductList | null; selected: string; onSelect: (key: string) => void; onFocus: () => void;
  activeProduct: ScientificProduct | undefined;
  refreshStatus: RefreshStatus | null;
  quakesOn: boolean; quakeCount: number; onQuakes: () => void; kpText: string | null; error: string | null;
  grouped: boolean; onGroup: () => void;
}) {
  const product = activeProduct;
  const listRef=useRef<HTMLUListElement>(null);
  useEffect(()=>{
    const list=listRef.current;
    const row=list?.querySelector('input:checked')?.closest('li');
    if(!list || !row) return;
    const box=list.getBoundingClientRect(),item=row.getBoundingClientRect();
    if(item.top<box.top) list.scrollTop+=item.top-box.top;
    else if(item.bottom>box.bottom) list.scrollTop+=item.bottom-box.bottom;
  },[selected,data?.products.length]);
  const forceGrouping=(product?.samples ?? []).filter(s=>s.map_eligible!==false && s.latitude!=null && s.longitude!=null).length>1500;
  return <aside className="sidebar" aria-label="Consulta real"><div className="sidebar-head"><h2>Observatorio · REAL</h2></div>
    <div className="sidebar-body">
      <p className="hint">{data?.connected_sources ?? '—'} fuentes con datos · {data?.field_products ?? '—'} campos científicos · {data?.calculated_field_products ?? '—'} calculados</p>
      <p className="hint">{data?.historical_records ?? '—'} registros históricos · {data?.imported_indicator_records ?? '—'} registros de indicadores importados. Contexto estático y celdas no suman observaciones.</p>
      {!!data?.calculated_indicator_products && <p className="hint">{data.calculated_indicator_products} productos de indicadores calculados; los campos están incluidos arriba. No son eventos detectados.</p>}
      <p className="hint">Actualizador: {refreshStatus?.recent_scan ? 'revisión reciente' : 'sin revisión reciente comprobada'} · {refreshStatus?.last_scan_at ?? 'No disponible'} UTC</p>
      {error && <p role="status" className="hint">{error} Se conserva la última carga disponible.</p>}
      <h3>Productos reales</h3>
      <ul className="rows product-list" ref={listRef}>{data?.products.map(p => <li key={p.id}><label className="row"><input type="radio" name="real-product" checked={selected === p.id} onChange={() => onSelect(p.id)} /><span>{p.title}{p.kind==='forecast' && <small> · {productForecastState(p)}</small>}</span></label></li>)}
        <li><label className="row"><input type="radio" name="real-product" checked={selected === 'archive'} onChange={() => onSelect('archive')} /><span>SST · archivo del Caribe</span></label></li>
      </ul>
      {product && <figure className="legend"><figcaption><strong>{product.variable} · {product.unit}</strong><span>{productKindLabel(product)} · {product.source_id}</span></figcaption>
        {product.kind==='forecast' && <p className="forecast-warning">{productForecastState(product)} · consultar validez; su recuperación no define el horizonte.</p>}
        <p className="hint">{product.observed_at || product.valid_from || product.issued_at ? `${productTimeLabel(product)} UTC` : 'Fechas y época en los registros; sin instante UTC proporcionado.'}</p>
        <ProductFieldLegend product={product}/>
        {(product.grid || product.extent) && <button type="button" className="wide-toggle" onClick={onFocus}>Encuadrar cobertura</button>}
        <p className="hint">{product.coverage}</p>
        <DistributorCredit product={product}/>
        {product.representation==='points' && <p className="hint">{(product.samples ?? []).filter(s=>s.map_eligible===false).length} registros excluidos del mapa por calidad, conservados en la tabla/original.</p>}
      </figure>}
      <label className="row"><input type="checkbox" checked={quakesOn} onChange={onQuakes}/><span>Sismos observados</span><b>{quakeCount}</b></label>
      <label className="row"><input type="checkbox" checked={grouped || forceGrouping} disabled={forceGrouping} onChange={onGroup}/><span>Agrupar registros al alejar</span></label>
      {forceGrouping && <p className="hint">Este conjunto requiere agrupación para limitar el globo a 1.500 símbolos. Cada grupo conserva su cantidad real; todos los registros siguen seleccionables en la tabla.</p>}
      <p className="hint">{kpText ?? 'Kp no disponible'}</p>
      <p className="hint">31 fenómenos especificados en el catálogo. Las celdas de los campos no se cuentan como señales.</p>
      <p className="hint">Al superponerse símbolos se prioriza uno en pantalla; todos los registros permanecen en la tabla y pueden seleccionarse.</p><p className="hint">IMERG reciente, SMAP y GLDAS: acceso Earthdata/PPS pendiente. La climatología IMERG es una referencia histórica. Detalles en docs/accesos.md.</p>
    </div></aside>;
}

export function ProductInspector({ product, selectedId,onTrackFocus,onRegionFocus,onSampleSelect,refreshStatus }: { product: ScientificProduct; selectedId: string | null; onTrackFocus?: (track:ProductTrack)=>void; onRegionFocus?: (region:ProductRegion)=>void; onSampleSelect?: (id:string)=>void; refreshStatus?: RefreshStatus | null }) {
  const p = product;
  const samples = p.samples ?? [];
  const [sampleQuery,setSampleQuery]=useState('');
  const [samplePage,setSamplePage]=useState(0);
  const inspectorBody=useRef<HTMLDivElement>(null);
  useEffect(()=>{setSampleQuery('');setSamplePage(0);},[p.id]);
  useEffect(()=>{if(inspectorBody.current) inspectorBody.current.scrollTop=0;},[p.id,selectedId]);
  const matching=useMemo(()=>samples.filter(s=>!sampleQuery || `${s.id} ${s.time ?? ''} ${s.category ?? ''} ${JSON.stringify(s.attributes)}`.toLocaleLowerCase('es').includes(sampleQuery.toLocaleLowerCase('es'))),[samples,sampleQuery]);
  const pages=Math.max(1,Math.ceil(matching.length/40));const page=Math.min(samplePage,pages-1);
  const selected = samples.find(s=>s.id===selectedId);
  const jobKey=p.id==='d14-so-surface' ? 'd14-so-native' : p.id.startsWith('d14-mol-') ? 'd14-mol-native' : p.id==='d14-thetao-surface' ? 'd14-thetao-native' : p.id.startsWith('d14-smoc-') ? 'd14-smoc-native' : p.source_id==='D12' ? 'd12-cams-global' : p.id.startsWith('d10-glofas-') ? 'd10-glofas-discharge' : p.id.startsWith('d09-seas5-') ? 'd09-seas5-monthly' : p.id.startsWith('d48-roni-') ? 'd48-roni-outlook-tables' : p.id.startsWith('d25-s2-pampa-') ? 'd25-s2-pampa' : p.source_id==='D04' ? `mod13q1-${p.id.split('-').at(-1)}` : p.source_id==='D05' ? `mod11a2-${p.id.split('-').at(-1)}` : p.source_id==='D07' ? p.calculation ? 'd07-derived-fields' : 'd07-ifs-24h' : p.source_id==='D16' ? 'd16-mhw-monthly' : p.source_id==='D20' ? 'd20-asi-s1' : p.source_id==='D33' ? 'd33-grace-global' : p.source_id==='D34' && !p.calculation ? 'd34-rapid-monthly' : p.id;
  const derivedJobKeys:Record<string,string>={'d13-oisst-anomaly-global':'d13-current-anomaly','d15-sst-seasonal-departures':'d15-sst-anomalies'};
  const job=refreshStatus?.jobs?.[derivedJobKeys[p.id] ?? jobKey];
  const upstreamFailure=p.id==='d13-oisst-anomaly-global' ? refreshStatus?.jobs?.['d13-oisst-global']?.error : null;
  const chartSamples = p.representation === 'planetary' ? samples.slice(-60) : p.representation==='time_series' ? samples : [];
  const present = chartSamples.flatMap(s=>s.value === null || s.value === undefined ? [] : [s.value]);
  const low = present.length ? Math.min(...present) : 0;
  const high = present.length ? Math.max(...present) : 1;
  const timeLabelDigits=p.calculation ? 4 : [7,10,16,24].find(digits=>new Set(chartSamples.map(s=>s.time?.slice(0,digits) ?? s.id)).size===chartSamples.length) ?? 24;
  const chart=p.kind==='forecast' && p.id.startsWith('d48-roni-') ? <CpcEnsoPanel product={p}/> : chartSamples.length > 0 ? <section aria-label="Serie del producto"><h3>{p.calculation ? 'Serie calculada' : p.kind==='forecast' ? 'Serie del pronóstico' : p.kind==='historical' ? 'Serie histórica' : 'Serie del índice'}</h3><p className="fine">{p.unit} · {p.coverage}</p><AnomalyChart observedLabel={p.calculation ? 'Agregado calculado' : 'Observado'} points={chartSamples.map(s=>({label:s.time?.slice(0,timeLabelDigits) ?? s.id,kind:p.kind==='forecast'?'forecast':'observed',value:s.value ?? null}))} domain={{min:low-.1,max:high+.1,ticks:[high,(low+high)/2,low]}} caption={`${p.variable} · ${p.unit}; ${chartSamples.length} registros conservados. ${p.coverage} UTC; los huecos siguen ausentes.`}/></section> : null;
  return <aside className="inspector" aria-label="Producto real"><header className="inspector-head"><p className="kicker">{p.source_id} · REAL · {productKindLabel(p)}</p><h2>{p.title}</h2><p className="region">{productTimeLabel(p)} UTC</p></header>
    <div className="inspector-body" ref={inspectorBody}><DistributorCredit product={p}/>{p.kind==='forecast' && <p className="forecast-warning">{productForecastState(p)}. Un producto vencido se consulta como archivo, no como futuro actual.</p>}{selected && <section aria-label="Registro seleccionado"><h3>{selected.attributes?.nombre ?? selected.id}</h3><p>{selected.value ?? selected.category ?? 'Ausente'} {p.unit}</p>{selected.map_eligible===false && selected.latitude!=null && selected.longitude!=null && <p className="fine">Excluido del mapa por calidad; el registro original permanece accesible.</p>}{selected.latitude!=null && selected.longitude!=null && <p>{selected.latitude}°, {selected.longitude}° WGS84</p>}<details><summary>Atributos nativos y método</summary><p className="fine">{Object.entries(selected.attributes ?? {}).map(([k,v])=>`${k}: ${v ?? 'ausente'}`).join(' · ')}</p></details><p className="fine">{selected.quality}</p></section>}{p.calculation?.result && <section aria-label="Resultado descriptivo"><h3>{p.calculation.result.label}</h3><p className="calculation-result">{p.calculation.result.value.toLocaleString('es',{maximumFractionDigits:4,signDisplay:'exceptZero'})} {p.calculation.result.unit}</p><p className="fine">Describe el período indicado. Sin prueba de significación ni extrapolación.</p></section>}{chart}<p>{p.limitation}</p>
      {upstreamFailure && <p role="status">Falló la actualización de la fuente diaria OISST: {upstreamFailure}. Se conserva el campo válido en REAL, con dato de {p.observed_at} y original recuperado {p.retrieved_at} UTC; un procesamiento local correcto no actualiza esas fechas.</p>}
      {job && <section><h3>Actualización · UTC</h3>{job.error && <p role="status">Falló el último intento: {job.error}. Se conserva el último producto válido en REAL.</p>}<dl className="facts"><div><dt>Último intento</dt><dd>{job.last_attempt_at} · {job.status}</dd></div><div><dt>{p.id==='d13-oisst-anomaly-global' ? 'Último procesamiento correcto' : p.source_id==='D12' || p.source_id==='D14' || p.id.startsWith('d25-s2-pampa-') ? 'Última consulta satisfactoria' : p.calculation ? 'Último cálculo correcto' : 'Última descarga correcta'}</dt><dd>{job.last_success_at ?? 'No disponible'}</dd></div><div><dt>Último cambio del lote</dt><dd>{job.last_change_at ?? 'Sin cambio nuevo registrado'}</dd></div><div><dt>Próximo intento</dt><dd>{job.next_attempt_at}</dd></div></dl></section>}
      {p.calculation && <section><h3>Cálculo reproducible</h3><p>{p.calculation.formula}</p><p className="fine">{p.calculation.applicability}</p><p className="fine">{p.calculation.reference_period} · {p.calculation.method_version}</p><p className="fine">Parámetros: {JSON.stringify(p.calculation.parameters)}. Calculado {p.ingested_at} UTC; entradas recuperadas {p.retrieved_at} UTC.</p>{p.calculation.inputs.map(i=><p className="fine" key={i.product_id}>{i.product_id} · {i.variable} · {i.unit} · SHA-256 {i.checksum_sha256}</p>)}<p><a href={p.calculation.reference_url} target="_blank" rel="noreferrer">Definición del método</a></p></section>}
      {!!p.tracks?.length && <section><h3>{p.tracks.length} trayectorias históricas</h3><p className="fine">Línea dorada: centros publicados, no trayectoria futura. Seleccioná un sistema para encuadrarlo.</p><div className="product-table">{p.tracks.map(t=><button key={t.id} type="button" className="wide-toggle" onClick={()=>onTrackFocus?.(t)}>Encuadrar {t.name} · {t.sample_ids.length} posiciones</button>)}</div></section>}
      {!!p.regions?.length && <section><h3>{p.kind==='static_context' ? 'Unidades geográficas' : 'Áreas publicadas'}</h3><p className="fine">{p.kind==='static_context' ? 'Geometría de contexto; consultá resolución y transformación de visualización. No es un aviso ni un área afectada.' : 'Contorno del proveedor; la fecha del evento no determina vigencia del aviso. Consultá estado, urgencia y expiración en la ficha.'}</p>{p.regions.map(r=><button key={r.id} type="button" className="wide-toggle" onClick={()=>onRegionFocus?.(r)}>Encuadrar {r.name}</button>)}</section>}
      <dl className="facts"><div><dt>Variable</dt><dd>{p.variable} · {p.unit}</dd></div><div><dt>Producto</dt><dd>{p.collection_id} · {p.product_version}</dd></div>
        <div><dt>Observación / período</dt><dd>{p.observed_at ?? 'No informada'}{p.observation_end ? ` → ${p.observation_end}` : ''} UTC</dd></div><div><dt>Recuperado</dt><dd>{p.retrieved_at} UTC</dd></div><div><dt>Inicialización</dt><dd>{p.initialized_at ?? 'No proporcionada'}</dd></div><div><dt>Emisión</dt><dd>{p.issued_at ?? 'No proporcionada'}</dd></div><div><dt>Validez</dt><dd>{p.valid_from ?? 'No aplica'} — {p.valid_to ?? 'No aplica'}</dd></div>
        <div><dt>Cadencia</dt><dd>{p.cadence_seconds / 3600} h; se conserva el dato si falla la actualización</dd></div></dl>
      {p.issue_time_basis && <p className="fine">Referencia temporal: {p.issue_time_basis}</p>}
      {p.grid && <><h3>Campo geográfico</h3><p>{p.grid.width} × {p.grid.height} · {p.grid.resolution}</p><p className="fine">{p.grid.sampling}</p><p className="fine">Máscara: {p.grid.quality_mask}</p></>}
      {p.grid?.quality_values && <section><h3>Calidad y códigos por celda</h3><p className="fine">Códigos alineados con la malla, accesibles en la API y el original conservado. No son confianza.</p>{Object.entries(p.grid.quality_legend ?? {}).map(([code,label])=><p key={code} className="fine">{code}: {label} · {p.grid!.quality_values!.filter(v=>v===Number(code)).length.toLocaleString('es')} celdas</p>)}</section>}
      {samples.length > 0 && <><h3>{samples.length} registros · {p.unit}</h3><label className="record-search">Buscar registros<input aria-label="Buscar registros del producto" value={sampleQuery} onChange={e=>{setSampleQuery(e.target.value);setSamplePage(0);}}/></label><p className="fine">{matching.length} coincidencias · página {page+1} de {pages}. Seleccioná cualquier registro, aunque sus puntos se superpongan.</p><div className="product-table"><table><thead><tr><th>Registro / UTC</th><th>Valor</th></tr></thead><tbody>{matching.slice(page*40,page*40+40).map(s => <tr key={s.id}><td><button type="button" className="record-link" onClick={()=>onSampleSelect?.(s.id)}>Ver {s.attributes?.nombre ?? s.id}</button><br/>{s.time ?? 'Fecha no informada'}{s.valid_to ? ` → ${s.valid_to}` : ''}<br/><small>{Object.entries(s.attributes ?? {}).slice(0, 4).map(([k,v]) => `${k}: ${v ?? 'ausente'}`).join(' · ')}</small>{s.probability_definition && <details><summary>Definición de probabilidad</summary>{s.probability_definition}</details>}</td><td>{s.value ?? s.category ?? 'Ausente'}</td></tr>)}</tbody></table></div><div className="record-pages"><button type="button" className="wide-toggle" disabled={page===0} onClick={()=>setSamplePage(page-1)}>Página anterior</button><button type="button" className="wide-toggle" disabled={page+1>=pages} onClick={()=>setSamplePage(page+1)}>Siguiente página</button></div></>}
      <h3>Comprobación independiente</h3><p className="fine">{p.verification.method}. Original: {p.verification.expected}; decodificado: {p.verification.actual}.</p>
      <h3>Procedencia</h3><p className="fine">{p.attribution} · {p.byte_size.toLocaleString('es')} bytes · SHA-256 {p.checksum_sha256}</p>
      <p><a href={`${apiBase}/v1/products/${p.id}/original`} target="_blank" rel="noreferrer">Archivo científico conservado</a></p><p><a href={p.original_url} target="_blank" rel="noreferrer">Producto original</a> · <a href={p.license_url} target="_blank" rel="noreferrer">Atribución y método</a></p>
    </div></aside>;
}
