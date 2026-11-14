import type { ProductList, ScientificProduct,ProductTrack,ProductRegion,RefreshStatus } from '../domain/generated';
import { AnomalyChart } from '../shell/AnomalyChart';
import { useEffect,useMemo,useState } from 'react';
const apiBase = import.meta.env.VITE_API_BASE ?? '/api';

export function productKindLabel(p: ScientificProduct): string {
  if(p.calculation) return 'Campo calculado';
  return {observation:'Observaciones',indicator:'Indicador importado',forecast:'Pronóstico externo',historical:'Archivo histórico',static_context:'Contexto geográfico',orbital_assessment:'Evaluación orbital'}[p.kind];
}

export function ProductsPanel({ data, selected, activeProduct, refreshStatus, onSelect, onFocus, quakesOn, quakeCount, onQuakes, kpText, error, grouped, onGroup }: {
  data: ProductList | null; selected: string; onSelect: (key: string) => void; onFocus: () => void;
  activeProduct: ScientificProduct | undefined;
  refreshStatus: RefreshStatus | null;
  quakesOn: boolean; quakeCount: number; onQuakes: () => void; kpText: string | null; error: string | null;
  grouped: boolean; onGroup: () => void;
}) {
  const product = activeProduct;
  const forceGrouping=(product?.samples ?? []).filter(s=>s.map_eligible!==false && s.latitude!=null && s.longitude!=null).length>1500;
  return <aside className="sidebar" aria-label="Consulta real"><div className="sidebar-head"><h2>Observatorio · REAL</h2></div>
    <div className="sidebar-body">
      <p className="hint">{data?.connected_sources ?? '—'} fuentes con datos · {data?.field_products ?? '—'} campos científicos · {data?.calculated_field_products ?? '—'} calculados</p>
      <p className="hint">{data?.historical_records ?? '—'} registros históricos · {data?.imported_indicator_records ?? '—'} registros de indicadores importados. Contexto estático y celdas no suman observaciones.</p>
      <p className="hint">Actualizador: {refreshStatus?.recent_scan ? 'revisión reciente' : 'sin revisión reciente comprobada'} · {refreshStatus?.last_scan_at ?? 'No disponible'} UTC</p>
      {error && <p role="status" className="hint">{error} Se conserva la última carga disponible.</p>}
      <h3>Productos reales</h3>
      <ul className="rows">{data?.products.map(p => <li key={p.id}><label className="row"><input type="radio" name="real-product" checked={selected === p.id} onChange={() => onSelect(p.id)} /><span>{p.title}</span></label></li>)}
        <li><label className="row"><input type="radio" name="real-product" checked={selected === 'archive'} onChange={() => onSelect('archive')} /><span>SST · archivo del Caribe</span></label></li>
      </ul>
      {product && <figure className="legend"><figcaption><strong>{product.variable} · {product.unit}</strong><span>{productKindLabel(product)} · {product.source_id}</span></figcaption>
        <p className="hint">{product.observed_at || product.valid_from || product.issued_at ? `${product.observed_at ?? product.valid_from ?? `Emisión ${product.issued_at}`} UTC` : 'Fechas y época en los registros; sin instante UTC proporcionado.'}</p>
        {product.grid && <><div className="legend-bar legend-real" /><div className="legend-scale"><span>{product.grid.minimum?.toFixed(2)} {product.unit}</span><span>{product.grid.maximum?.toFixed(2)} {product.unit}</span></div><p className="hint">{product.grid.resolution}. {product.grid.missing_cells.toLocaleString('es')} celdas ausentes, transparentes.</p></>}
        {(product.grid || product.extent) && <button type="button" className="wide-toggle" onClick={onFocus}>Encuadrar cobertura</button>}
        <p className="hint">{product.coverage}</p>
        {product.representation==='points' && <p className="hint">{(product.samples ?? []).filter(s=>s.map_eligible===false).length} registros excluidos del mapa por calidad, conservados en la tabla/original.</p>}
      </figure>}
      <label className="row"><input type="checkbox" checked={quakesOn} onChange={onQuakes}/><span>Sismos observados</span><b>{quakeCount}</b></label>
      <label className="row"><input type="checkbox" checked={grouped || forceGrouping} disabled={forceGrouping} onChange={onGroup}/><span>Agrupar registros al alejar</span></label>
      {forceGrouping && <p className="hint">Este conjunto requiere agrupación para limitar el globo a 1.500 símbolos. Cada grupo conserva su cantidad real; todos los registros siguen seleccionables en la tabla.</p>}
      <p className="hint">{kpText ?? 'Kp no disponible'}</p>
      <p className="hint">31 fenómenos especificados en el catálogo. Las celdas de los campos no se cuentan como señales.</p>
      <p className="hint">IMERG, SMAP y GLDAS: acceso Earthdata pendiente. Detalles en docs/accesos.md.</p>
    </div></aside>;
}

export function ProductInspector({ product, selectedId,onTrackFocus,onRegionFocus,onSampleSelect,refreshStatus }: { product: ScientificProduct; selectedId: string | null; onTrackFocus?: (track:ProductTrack)=>void; onRegionFocus?: (region:ProductRegion)=>void; onSampleSelect?: (id:string)=>void; refreshStatus?: RefreshStatus | null }) {
  const p = product;
  const samples = p.samples ?? [];
  const [sampleQuery,setSampleQuery]=useState('');
  const [samplePage,setSamplePage]=useState(0);
  useEffect(()=>{setSampleQuery('');setSamplePage(0);},[p.id]);
  const matching=useMemo(()=>samples.filter(s=>!sampleQuery || `${s.id} ${s.time ?? ''} ${s.category ?? ''} ${JSON.stringify(s.attributes)}`.toLocaleLowerCase('es').includes(sampleQuery.toLocaleLowerCase('es'))),[samples,sampleQuery]);
  const pages=Math.max(1,Math.ceil(matching.length/40));const page=Math.min(samplePage,pages-1);
  const selected = samples.find(s=>s.id===selectedId);
  const jobKey=p.source_id==='D04' ? `mod13q1-${p.id.split('-').at(-1)}` : p.source_id==='D05' ? `mod11a2-${p.id.split('-').at(-1)}` : p.source_id==='D07' ? p.calculation ? 'd07-derived-fields' : 'd07-ifs-24h' : p.source_id==='D16' ? 'd16-mhw-monthly' : p.source_id==='D20' ? 'd20-asi-s1' : p.id;
  const job=refreshStatus?.jobs?.[jobKey];
  const chartSamples = p.representation === 'planetary' ? samples.slice(-60) : [];
  const present = chartSamples.flatMap(s=>s.value === null || s.value === undefined ? [] : [s.value]);
  const low = present.length ? Math.min(...present) : 0;
  const high = present.length ? Math.max(...present) : 1;
  return <aside className="inspector" aria-label="Producto real"><header className="inspector-head"><p className="kicker">{p.source_id} · REAL · {productKindLabel(p)}</p><h2>{p.title}</h2><p className="region">{p.observed_at ?? p.valid_from ?? (p.issued_at ? `Emitido ${p.issued_at}` : `Recuperado ${p.retrieved_at}`)} UTC</p></header>
    <div className="inspector-body"><p>{p.limitation}</p>
      {job && <section><h3>Actualización · UTC</h3>{job.error && <p role="status">Falló el último intento: {job.error}. Se conserva el último producto válido en REAL.</p>}<dl className="facts"><div><dt>Último intento</dt><dd>{job.last_attempt_at} · {job.status}</dd></div><div><dt>{p.calculation ? 'Último cálculo correcto' : 'Última descarga correcta'}</dt><dd>{job.last_success_at ?? 'No disponible'}</dd></div><div><dt>Último cambio</dt><dd>{job.last_change_at ?? 'Sin cambio nuevo registrado'}</dd></div><div><dt>Próximo intento</dt><dd>{job.next_attempt_at}</dd></div></dl></section>}
      {p.calculation && <section><h3>Cálculo reproducible</h3><p>{p.calculation.formula}</p><p className="fine">{p.calculation.applicability}</p><p className="fine">{p.calculation.reference_period} · {p.calculation.method_version}</p><p className="fine">Parámetros: {JSON.stringify(p.calculation.parameters)}. Calculado {p.ingested_at} UTC; entradas recuperadas {p.retrieved_at} UTC.</p>{p.calculation.inputs.map(i=><p className="fine" key={i.product_id}>{i.product_id} · {i.variable} · {i.unit} · SHA-256 {i.checksum_sha256}</p>)}<p><a href={p.calculation.reference_url} target="_blank" rel="noreferrer">Definición del método</a></p></section>}
      {!!p.tracks?.length && <section><h3>{p.tracks.length} trayectorias históricas</h3><p className="fine">Línea dorada: centros publicados, no trayectoria futura. Seleccioná un sistema para encuadrarlo.</p><div className="product-table">{p.tracks.map(t=><button key={t.id} type="button" className="wide-toggle" onClick={()=>onTrackFocus?.(t)}>Encuadrar {t.name} · {t.sample_ids.length} posiciones</button>)}</div></section>}
      {!!p.regions?.length && <section><h3>{p.kind==='static_context' ? 'Unidades geográficas' : 'Áreas publicadas'}</h3><p className="fine">{p.kind==='static_context' ? 'Geometría de contexto; consultá resolución y transformación de visualización. No es un aviso ni un área afectada.' : 'Contorno del proveedor; la fecha del evento no determina vigencia del aviso. Consultá estado, urgencia y expiración en la ficha.'}</p>{p.regions.map(r=><button key={r.id} type="button" className="wide-toggle" onClick={()=>onRegionFocus?.(r)}>Encuadrar {r.name}</button>)}</section>}
      {selected && <section><h3>{selected.attributes?.nombre ?? selected.id}</h3><p>{selected.value ?? selected.category ?? 'Ausente'} {p.unit}</p>{selected.map_eligible===false && <p className="fine">Excluido del mapa por calidad; el registro original permanece accesible.</p>}{selected.latitude!=null && selected.longitude!=null && <p>{selected.latitude}°, {selected.longitude}° WGS84</p>}<p className="fine">{Object.entries(selected.attributes ?? {}).map(([k,v])=>`${k}: ${v ?? 'ausente'}`).join(' · ')}</p><p className="fine">{selected.quality}</p></section>}
      {chartSamples.length > 0 && <AnomalyChart points={chartSamples.map(s=>({label:s.time?.slice(0,10) ?? s.id,kind:p.kind==='forecast'?'forecast':'observed',value:s.value ?? null}))} domain={{min:low-.1,max:high+.1,ticks:[high,(low+high)/2,low]}} caption={`${p.variable} · ${p.unit}; últimos ${chartSamples.length} registros. UTC; los huecos siguen ausentes.`}/>}
      <dl className="facts"><div><dt>Variable</dt><dd>{p.variable} · {p.unit}</dd></div><div><dt>Producto</dt><dd>{p.collection_id} · {p.product_version}</dd></div>
        <div><dt>Observación / período</dt><dd>{p.observed_at ?? 'No informada'}{p.observation_end ? ` → ${p.observation_end}` : ''} UTC</dd></div><div><dt>Recuperado</dt><dd>{p.retrieved_at} UTC</dd></div><div><dt>Emisión</dt><dd>{p.issued_at ?? 'No proporcionada'}</dd></div><div><dt>Validez</dt><dd>{p.valid_from ?? 'No aplica'} — {p.valid_to ?? 'No aplica'}</dd></div>
        <div><dt>Cadencia</dt><dd>{p.cadence_seconds / 3600} h; se conserva el dato si falla la actualización</dd></div></dl>
      {p.grid && <><h3>Campo geográfico</h3><p>{p.grid.width} × {p.grid.height} · {p.grid.resolution}</p><p className="fine">{p.grid.sampling}</p><p className="fine">Máscara: {p.grid.quality_mask}</p></>}
      {p.grid?.quality_values && <section><h3>Calidad y códigos por celda</h3><p className="fine">Códigos alineados con la malla, accesibles en la API y el original conservado. No son confianza.</p>{Object.entries(p.grid.quality_legend ?? {}).map(([code,label])=><p key={code} className="fine">{code}: {label} · {p.grid!.quality_values!.filter(v=>v===Number(code)).length.toLocaleString('es')} celdas</p>)}</section>}
      {samples.length > 0 && <><h3>{samples.length} registros · {p.unit}</h3><label className="record-search">Buscar registros<input aria-label="Buscar registros del producto" value={sampleQuery} onChange={e=>{setSampleQuery(e.target.value);setSamplePage(0);}}/></label><p className="fine">{matching.length} coincidencias · página {page+1} de {pages}. Seleccioná cualquier registro, aunque sus puntos se superpongan.</p><div className="product-table"><table><thead><tr><th>Registro / UTC</th><th>Valor</th></tr></thead><tbody>{matching.slice(page*40,page*40+40).map(s => <tr key={s.id}><td><button type="button" className="record-link" onClick={()=>onSampleSelect?.(s.id)}>Ver {s.attributes?.nombre ?? s.id}</button><br/>{s.time ?? 'Fecha no informada'}{s.valid_to ? ` → ${s.valid_to}` : ''}<br/><small>{Object.entries(s.attributes ?? {}).slice(0, 4).map(([k,v]) => `${k}: ${v ?? 'ausente'}`).join(' · ')}</small>{s.probability_definition && <details><summary>Definición de probabilidad</summary>{s.probability_definition}</details>}</td><td>{s.value ?? s.category ?? 'Ausente'}</td></tr>)}</tbody></table></div><div className="record-pages"><button type="button" className="wide-toggle" disabled={page===0} onClick={()=>setSamplePage(page-1)}>Página anterior</button><button type="button" className="wide-toggle" disabled={page+1>=pages} onClick={()=>setSamplePage(page+1)}>Siguiente página</button></div></>}
      <h3>Comprobación independiente</h3><p className="fine">{p.verification.method}. Original: {p.verification.expected}; decodificado: {p.verification.actual}.</p>
      <h3>Procedencia</h3><p className="fine">{p.attribution} · {p.byte_size.toLocaleString('es')} bytes · SHA-256 {p.checksum_sha256}</p>
      <p><a href={`${apiBase}/v1/products/${p.id}/original`} target="_blank" rel="noreferrer">Archivo científico conservado</a></p><p><a href={p.original_url} target="_blank" rel="noreferrer">Producto original</a> · <a href={p.license_url} target="_blank" rel="noreferrer">Atribución y método</a></p>
    </div></aside>;
}
