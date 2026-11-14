import type { DemoSeriesPoint } from "../demo/scenario";

interface AnomalyChartProps {
  points: DemoSeriesPoint[];
  caption: string;
  domain?: { min: number; max: number; ticks: number[] };
  observedLabel?: string;
}

const width = 320;
const height = 112;
const padX = 28;
const padY = 12;

function yOf(value: number, min: number, max: number): number {
  return padY + ((max - value) / (max - min)) * (height - padY * 2);
}

function xOf(index: number, count: number, left=padX): number {
  if (count <= 1) {
    return left;
  }
  return left + (index / (count - 1)) * (width - left - 8);
}

function line(points: Array<{ x: number; y: number }>): string {
  return points.map((point, index) => `${index === 0 ? "M" : "L"}${point.x.toFixed(1)} ${point.y.toFixed(1)}`).join(" ");
}

function seriesPath(points:Array<{x:number;y:number|null;kind:DemoSeriesPoint['kind']}>,kind:DemoSeriesPoint['kind']):string {
  let connected=false;
  return points.map(p=>{
    if(p.y===null || p.kind!==kind){connected=false;return '';}
    const command=connected?'L':'M';connected=true;
    return `${command}${p.x.toFixed(1)} ${p.y.toFixed(1)}`;
  }).filter(Boolean).join(' ');
}

export function AnomalyChart({ points, caption, domain, observedLabel='Observado' }: AnomalyChartProps) {
  const min = domain?.min ?? -48;
  const max = domain?.max ?? 4;
  const ticks = domain?.ticks ?? [0, -20, -40];
  const tickLabels=ticks.map(t=>t.toLocaleString('es',{maximumFractionDigits:2}));
  const plotLeft=Math.max(padX,Math.max(0,...tickLabels.map(t=>t.length))*5+8);
  const placed = points.map((point, index) => ({
    ...point,
    x: xOf(index, points.length,plotLeft),
    y: point.value === null ? null : yOf(point.value, min, max),
  }));
  const observed = placed.filter((point) => point.kind === "observed" && point.y !== null);
  const forecast = placed.filter((point) => point.kind === "forecast" && point.y !== null);
  const firstForecast=placed.findIndex(p=>p.kind==='forecast' && p.y!==null);
  const previous=placed[firstForecast-1];
  const bridge=previous?.kind==='observed' && previous.y!==null ? [previous,placed[firstForecast]] : [];
  const longestLabel=Math.max(0,...points.map(p=>p.label.length));
  const labelSlots=longestLabel>10 ? 3 : longestLabel>7 ? 4 : 6;
  const labelIndices=new Set(Array.from({length:labelSlots},(_,i)=>Math.round(i*(points.length-1)/(labelSlots-1))));
  const band = placed.filter((point) => point.low !== undefined && point.high !== undefined && point.y !== null);
  const bandPath =
    band.length > 0
      ? `${line(band.map((point) => ({ x: point.x, y: yOf(point.high ?? 0, min, max) })))} ${line(
          [...band].reverse().map((point) => ({ x: point.x, y: yOf(point.low ?? 0, min, max) })),
        ).replace("M", "L")} Z`
      : "";

  return (
    <figure className="chart">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={caption}>
        {ticks.map((tick,index) => (
          <g key={tick}>
            <line className="chart-grid" x1={plotLeft} x2={width - 4} y1={yOf(tick, min, max)} y2={yOf(tick, min, max)} />
            <text className="chart-tick" x={2} y={yOf(tick, min, max) + 3}>
              {tickLabels[index]}
            </text>
          </g>
        ))}
        {bandPath ? <path className="chart-band" d={bandPath} /> : null}
        {observed.length > 1 ? <path className="chart-observed" d={seriesPath(placed,'observed')} /> : null}
        {bridge.length === 2 ? (
          <path
            className="chart-forecast"
            d={line(bridge.map((point) => ({ x: point.x, y: point.y ?? 0 })))}
          />
        ) : null}
        {forecast.length > 1 ? <path className="chart-forecast" d={seriesPath(placed,'forecast')} /> : null}
        {placed.map((point) =>
          point.y === null ? (
            <text key={point.label} className="chart-gap" x={point.x} y={height - 2}>
              ·
            </text>
          ) : (
            <circle key={point.label} className={point.kind === "forecast" ? "chart-dot-forecast" : "chart-dot"} cx={point.x} cy={point.y} r="2.2" />
          ),
        )}
      </svg>
      <div className="chart-labels">
        {points.filter((_,i)=>points.length<=labelSlots || labelIndices.has(i)).map((point) => (
          <span key={point.label}>{point.label}</span>
        ))}
      </div>
      <figcaption className="chart-key">
        {observed.length > 0 ? <span><i className="swatch observed" /> {observedLabel}</span> : null}
        {points.some((point) => point.kind === "forecast") ? <span><i className="swatch forecast" /> Pronóstico</span> : null}
        {points.some((point) => point.low !== undefined && point.high !== undefined) ? <span><i className="swatch band" /> Incertidumbre</span> : null}
      </figcaption>
    </figure>
  );
}
