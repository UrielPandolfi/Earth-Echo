import { useEffect, useState } from 'react';
import type { SSTAnomalyView } from '../domain/generated';
import { TrendChart } from './TrendChart';

const apiBase=import.meta.env.VITE_API_BASE ?? '/api';

export function SSTAnomalies({onShowProduct}:{onShowProduct?:(key:string)=>void}) {
  const [view,setView]=useState<SSTAnomalyView | null>(null);
  const [error,setError]=useState<string | null>(null);
  useEffect(()=>{
    const controller=new AbortController();
    void fetch(`${apiBase}/v1/analyses/d15-anomalies`,{signal:controller.signal})
      .then(async response=>{if(!response.ok) throw new Error('Análisis de anomalías no disponible.');return response.json() as Promise<SSTAnomalyView>;})
      .then(data=>{setView(data);setError(null);})
      .catch((caught:unknown)=>{if(!controller.signal.aborted)setError(caught instanceof Error ? caught.message : 'No se pudo leer el análisis.');});
    return ()=>controller.abort();
  },[]);
  const product=view?.product;
  const samples=product?.samples ?? [];
  const candidates=samples.filter(s=>s.category==='warm_departure' || s.category==='cold_departure');
  const points=samples.filter(s=>s.category!=='reference' && s.category!=='before_reference').map(s=>({
    year:Number(s.id.slice(0,4)),month:Number(s.id.slice(5,7)),anomaly_c:s.value ?? null,
  }));
  const number=(text:string | null | undefined)=>text!==null && text!==undefined && Number.isFinite(Number(text)) ? Number(text).toFixed(3) : 'Ausente';
  return <section aria-labelledby="sst-anomalies-title">
    <h3 id="sst-anomalies-title">Anomalías históricas</h3>
    {error ? <p role="status">{error} El modo REAL conserva sus datos.</p> : !view ? <p>Cargando anomalías reales.</p> : !product ? <p>{view.reason}</p> : <>
      <p>{view.flagged_months} meses candidatos de {view.assessed_months} evaluados · {view.assessment_period}.</p>
      <p className="fine">Desvío respecto a la mediana del mismo mes en 2014–2021. Ocho años de referencia; candidato si |M| &gt; 3,5. M es un score robusto, sin probabilidad de daño. No es una alerta actual.</p>
      {view.reason && <p role="status">{view.reason}</p>}
      {view.status==='not_evaluable' && <p>Referencia o dispersión insuficientes: no evaluable.</p>}
      <details>
        <summary>Ver serie y meses candidatos</summary>
        <TrendChart series={points} trendLine={[]} lowLine={[]} highLine={[]} label="Desvío mensual de SST respecto a mediana de referencia, 2022–2025" />
        <p className="fine">ΔSST en °C. {view.warm_months} cálidos, {view.cold_months} fríos. {view.missing_months} meses ausentes o no evaluables; no se rellenan.</p>
        <div className="product-table"><table><thead><tr><th>Mes UTC</th><th>ΔSST °C</th><th>M</th></tr></thead><tbody>
          {candidates.map(s=><tr key={s.id}><td>{s.id}</td><td>{s.value==null ? 'Ausente' : s.value.toFixed(3)}</td><td>{number(s.attributes?.modified_z)}</td></tr>)}
        </tbody></table></div>
        <p className="fine">{product.coverage}</p>
        <p className="fine">{product.limitation}</p>
        <p className="fine">Método {product.method_version}. {product.attribution}</p>
        <p><a href={`${apiBase}/v1/products/${product.id}`} target="_blank" rel="noreferrer">Método, calidad y procedencia</a> · <a href={`${apiBase}/v1/products/${product.id}/original`}>Entrada mensual retenida</a></p>
      </details>
    </>}
    {view?.current_daily_anomaly_id && <section>
      <h4>Anomalía diaria mundial</h4>
      <p className="fine">NOAA OISST · dato {view.current_daily_anomaly_at} UTC. Campo publicado en °C respecto a base 1971–2000; referencia distinta del análisis histórico regional.</p>
      {onShowProduct ? <button type="button" className="wide-toggle" onClick={()=>onShowProduct(view.current_daily_anomaly_id!)}>Ver campo diario en el globo</button> : <a href={`${apiBase}/v1/products/${view.current_daily_anomaly_id}`}>Consultar campo diario y procedencia</a>}
    </section>}
  </section>;
}
