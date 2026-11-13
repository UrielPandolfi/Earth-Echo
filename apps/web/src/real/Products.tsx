import type { ProductList, ScientificProduct } from '../domain/generated';
const apiBase = import.meta.env.VITE_API_BASE ?? '/api';

export function ProductsPanel({ data, selected, onSelect, onFocus, quakesOn, quakeCount, onQuakes, kpText, error }: {
  data: ProductList | null; selected: string; onSelect: (key: string) => void; onFocus: () => void;
  quakesOn: boolean; quakeCount: number; onQuakes: () => void; kpText: string | null; error: string | null;
}) {
  const product = data?.products.find(p => p.id === selected);
  return <aside className="sidebar" aria-label="Consulta real"><div className="sidebar-head"><h2>Observatorio · REAL</h2></div>
    <div className="sidebar-body">
      <p className="hint">{data?.connected_sources ?? '—'} fuentes con datos · {data?.field_products ?? '—'} campos científicos</p>
      {error && <p role="status" className="hint">{error} Se conserva la última carga disponible.</p>}
      <h3>Productos reales</h3>
      <ul className="rows">{data?.products.map(p => <li key={p.id}><label className="row"><input type="radio" name="real-product" checked={selected === p.id} onChange={() => onSelect(p.id)} /><span>{p.title}</span></label></li>)}
        <li><label className="row"><input type="radio" name="real-product" checked={selected === 'archive'} onChange={() => onSelect('archive')} /><span>SST · archivo del Caribe</span></label></li>
      </ul>
      {product && <figure className="legend"><figcaption><strong>{product.variable} · {product.unit}</strong><span>{product.kind} · {product.source_id}</span></figcaption>
        <p className="hint">{product.observed_at ?? product.valid_from ?? 'Fecha en cada registro'} UTC</p>
        {product.grid && <><div className="legend-bar legend-real" /><div className="legend-scale"><span>{product.grid.minimum?.toFixed(2)} {product.unit}</span><span>{product.grid.maximum?.toFixed(2)} {product.unit}</span></div><p className="hint">{product.grid.resolution}. {product.grid.missing_cells.toLocaleString('es')} celdas ausentes, transparentes.</p><button type="button" className="wide-toggle" onClick={onFocus}>Encuadrar cobertura</button></>}
        <p className="hint">{product.coverage}</p>
      </figure>}
      <label className="row"><input type="checkbox" checked={quakesOn} onChange={onQuakes}/><span>Sismos observados</span><b>{quakeCount}</b></label>
      <p className="hint">{kpText ?? 'Kp no disponible'}</p>
      <p className="hint">31 fenómenos especificados en el catálogo. Las celdas de los campos no se cuentan como señales.</p>
      <p className="hint">IMERG, SMAP y GLDAS: acceso Earthdata pendiente. Detalles en docs/accesos.md.</p>
    </div></aside>;
}

export function ProductInspector({ product }: { product: ScientificProduct }) {
  const p = product;
  const samples = p.samples ?? [];
  return <aside className="inspector" aria-label="Producto real"><header className="inspector-head"><p className="kicker">{p.source_id} · REAL · {p.kind}</p><h2>{p.title}</h2><p className="region">{p.observed_at ?? p.valid_from ?? p.retrieved_at} UTC</p></header>
    <div className="inspector-body"><p>{p.limitation}</p>
      <dl className="facts"><div><dt>Variable</dt><dd>{p.variable} · {p.unit}</dd></div><div><dt>Producto</dt><dd>{p.collection_id} · {p.product_version}</dd></div>
        <div><dt>Recuperado</dt><dd>{p.retrieved_at} UTC</dd></div><div><dt>Emisión</dt><dd>{p.issued_at ?? 'No proporcionada'}</dd></div><div><dt>Validez</dt><dd>{p.valid_from ?? 'No aplica'} — {p.valid_to ?? 'No aplica'}</dd></div>
        <div><dt>Cadencia</dt><dd>{p.cadence_seconds / 3600} h; se conserva el dato si falla la actualización</dd></div></dl>
      {p.grid && <><h3>Campo geográfico</h3><p>{p.grid.width} × {p.grid.height} · {p.grid.resolution}</p><p className="fine">{p.grid.sampling}</p><p className="fine">Máscara: {p.grid.quality_mask}</p></>}
      {samples.length > 0 && <><h3>{samples.length} registros · {p.unit}</h3><div className="product-table"><table><thead><tr><th>Registro / UTC</th><th>Valor</th></tr></thead><tbody>{samples.slice(-40).map(s => <tr key={s.id}><td>{s.time ?? s.id}<br/><small>{Object.entries(s.attributes ?? {}).slice(0, 4).map(([k,v]) => `${k}: ${v ?? 'ausente'}`).join(' · ')}</small></td><td>{s.value === null ? 'Ausente' : s.value}</td></tr>)}</tbody></table></div></>}
      <h3>Comprobación independiente</h3><p className="fine">{p.verification.method}. Original: {p.verification.expected}; decodificado: {p.verification.actual}.</p>
      <h3>Procedencia</h3><p className="fine">{p.attribution} · {p.byte_size.toLocaleString('es')} bytes · SHA-256 {p.checksum_sha256}</p>
      <p><a href={`${apiBase}/v1/products/${p.id}/original`} target="_blank" rel="noreferrer">Archivo científico conservado</a></p><p><a href={p.original_url} target="_blank" rel="noreferrer">Producto original</a> · <a href={p.license_url} target="_blank" rel="noreferrer">Atribución y método</a></p>
    </div></aside>;
}
