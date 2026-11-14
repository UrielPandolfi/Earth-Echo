import type { ScientificProduct,ProductSample } from '../domain/generated';

/** Arrange provider rows only; probability and index arithmetic stay in the API. */
export function CpcEnsoPanel({product}:{product:ScientificProduct}) {
  const samples=product.samples ?? [];
  const columnMap=new Map<string,{key:string,label:string,order:number}>();
  const seasons=new Map<string,{order:number,entries:Map<string,ProductSample>}>();
  for(const sample of samples){
    const attrs=sample.attributes ?? {};
    const season=attrs.season,column=attrs.column;
    if(!season || !column) continue;
    columnMap.set(column,{key:column,label:attrs.column_label ?? column,order:Number(attrs.column_order)});
    const row=seasons.get(season)??{order:Number(attrs.season_order),entries:new Map<string,ProductSample>()};
    row.entries.set(column,sample);seasons.set(season,row);
  }
  const columns=[...columnMap.values()].sort((a,b)=>a.order-b.order);
  const probability=product.variable!=='RONI_forecast_percentile';
  return <section aria-label="Pronóstico oficial ENSO RONI" className="cpc-enso">
    <h3>Pronóstico oficial · RONI</h3>
    <p className="fine">Edición {samples[0]?.attributes?.issued_month ?? 'no informada'} · Niño 3.4 · base 1991–2020. Emisión mensual sin hora publicada.</p>
    <p className="fine">{probability ? 'Probabilidades por trimestre, no de impactos locales. El 0% publicado es aproximado.' : 'Los percentiles describen la distribución prevista del RONI. p50 es la mediana; los valores están en °C.'}</p>
    {product.variable==='enso_strength_probability' && <p className="fine">LN: La Niña · EN: El Niño. Intervalos de RONI en °C; límites exactos en cada encabezado y registro.</p>}
    <div className="product-table cpc-enso-table" role="region" aria-label="Tabla de ventanas ENSO RONI" tabIndex={0}>
      <table><caption>{product.variable==='enso_phase_probability' ? 'Fase ENSO · %' : probability ? 'Intensidad ENSO · %' : 'Percentiles RONI · °C'}</caption>
        <thead><tr><th scope="col">Trimestre</th>{columns.map(c=><th scope="col" key={c.key} title={c.key ?? ''}>{c.label}</th>)}</tr></thead>
        <tbody>{[...seasons].sort((a,b)=>a[1].order-b[1].order).map(([season,row])=><tr key={season}><th scope="row">{season}</th>{columns.map(c=>{
          const entry=c.key ? row.entries.get(c.key) : undefined;
          const value=entry?.value;
          return <td key={c.key} title={entry?.probability_definition ?? entry?.quality}>{value==null ? '—' : value.toLocaleString('es',{maximumFractionDigits:2})}{probability && value!=null && <span className="cpc-prob-bar" style={{width:`${value}%`}} aria-hidden="true"/>}</td>;
        })}</tr>)}</tbody></table>
    </div>
    <p className="fine">Ventanas civiles de tres meses que se solapan; algunas ya comenzaron al emitir. Sus fechas completas UTC y definiciones están en los registros. RONI y el ONI histórico son índices diferentes.</p>
  </section>;
}
