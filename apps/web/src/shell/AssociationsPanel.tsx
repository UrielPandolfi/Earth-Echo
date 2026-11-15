import { useEffect,useState } from 'react';
import type { AssociationView,AssociationPairView } from '../domain/generated';

const apiBase=import.meta.env.VITE_API_BASE ?? '/api';
const number=(value:number | null | undefined)=>value==null ? 'No evaluable' : value.toFixed(3);

function AssociationScatter({pair}:{pair:AssociationPairView}) {
  const points=pair.points.filter(p=>p.residual_x!==null && p.residual_y!==null);
  const xs=points.map(p=>p.residual_x as number),ys=points.map(p=>p.residual_y as number);
  if(!points.length)return null;
  const minX=Math.min(0,...xs),maxX=Math.max(0,...xs),minY=Math.min(0,...ys),maxY=Math.max(0,...ys);
  const x=(v:number)=>48+264*(v-minX)/(maxX-minX || 1);
  const y=(v:number)=>172-148*(v-minY)/(maxY-minY || 1);
  return <figure className="chart">
    <svg viewBox="0 0 350 220" role="img" aria-label={`Dispersión de residuos: ${pair.title}`}>
      <line className="chart-grid" x1="48" x2="312" y1={y(0)} y2={y(0)}/>
      <line className="chart-grid" x1={x(0)} x2={x(0)} y1="24" y2="172"/>
      {points.map(p=><circle key={`${p.year}-${p.quarter}`} cx={x(p.residual_x as number)} cy={y(p.residual_y as number)} r="2.5" fill="var(--accent, #46d5c5)"><title>{p.year} T{p.quarter}: {number(p.residual_x)} {pair.x_unit}, {number(p.residual_y)} {pair.y_unit}</title></circle>)}
      <text className="chart-tick" x="48" y="190">{minX.toFixed(2)}</text>
      <text className="chart-tick" x="312" y="190" textAnchor="end">{maxX.toFixed(2)}</text>
      <text className="chart-tick" x="4" y="30">{maxY.toFixed(2)}</text>
      <text className="chart-tick" x="4" y="172">{minY.toFixed(2)}</text>
      <text className="chart-tick" x="48" y="210">X: residuo · {pair.x_unit}</text>
      <text className="chart-tick" x="180" y="14">Y: SST · {pair.y_unit}</text>
    </svg>
    <figcaption className="fine">Cada punto es un trimestre emparejado. Se retiraron ciclo estacional y tendencia lineal de ambas series; no es una trayectoria geográfica.</figcaption>
  </figure>;
}

export function AssociationsPanel() {
  const [view,setView]=useState<AssociationView | null>(null);
  const [error,setError]=useState<string | null>(null);
  useEffect(()=>{
    const controller=new AbortController();
    void fetch(`${apiBase}/v1/analyses/associations`,{signal:controller.signal})
      .then(async r=>{if(!r.ok)throw new Error('Asociaciones no disponibles.');return r.json() as Promise<AssociationView>;})
      .then(setView).catch((e:unknown)=>{if(!controller.signal.aborted)setError(e instanceof Error ? e.message : 'Error de análisis.');});
    return ()=>controller.abort();
  },[]);
  return <section aria-labelledby="associations-title">
    <h3 id="associations-title">Conexiones exploratorias</h3>
    {error ? <p role="status">{error}</p> : !view ? <p>Cargando asociaciones reales.</p> : view.status==='unavailable' ? <p>{view.reason}</p> : <>
      <p className="fine">Dos pares fijados de antemano, sin buscar el mejor desfase. Asociación estadística; causalidad y predicción siguen sin demostrar.</p>
      {view.reason && <p role="status">{view.reason}</p>}
      {view.pairs.map(pair=><details key={pair.id}>
        <summary>{pair.title}</summary>
        <p className="fine">{pair.n_pairs} trimestres completos · {pair.missing_pairs} ausentes. {pair.points[0]?.start.slice(0,7)} a {pair.points.at(-1)?.end.slice(0,7)} exclusivo, UTC.</p>
        <dl className="facts"><div><dt>r sin ajustar</dt><dd>{number(pair.raw_r)}</dd></div><div><dt>r sin ciclo/tendencia</dt><dd>{number(pair.residual_r)}</dd></div></dl>
        {pair.status==='not_evaluable' ? <p>{pair.reason}</p> : <AssociationScatter pair={pair}/>}
        {pair.intervals.map(i=><p className="fine" key={i.block_quarters}>Intervalo condicional 95%, bloques de {i.block_quarters} trimestres: {number(i.low)} a {number(i.high)}. {i.valid_draws}/{i.draws} réplicas válidas.</p>)}
        <p className="fine">X: {pair.x_name} ({pair.x_unit}). {pair.x_scope}. Y: {pair.y_name} ({pair.y_unit}). {pair.y_scope}.</p>
        <details><summary>Método, supuestos y procedencia</summary>
          {pair.warnings.map(w=><p className="fine" key={w}>{w}</p>)}
          {pair.inputs.map(i=><p className="fine" key={i.product_id}>{i.product_id} · {i.unit} · SHA256 {i.checksum_sha256}</p>)}
        </details>
        <p><a href={`${apiBase}/v1/analyses/associations/${pair.id}.csv`}>Exportar pares CSV</a></p>
      </details>)}
      <p className="fine">Método {view.method_version}. Cálculo {view.computed_at} UTC.</p>
      <p><a href={`${apiBase}/v1/analyses/associations`} target="_blank" rel="noreferrer">Resultado completo y trazabilidad</a></p>
    </>}
  </section>;
}
