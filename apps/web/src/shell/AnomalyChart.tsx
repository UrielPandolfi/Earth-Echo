import type { DemoSeriesPoint } from "../demo/scenario";

interface AnomalyChartProps {
  points: DemoSeriesPoint[];
  caption: string;
}

const width = 320;
const height = 112;
const padX = 28;
const padY = 12;

function yOf(value: number): number {
  const max = 4;
  const min = -48;
  return padY + ((max - value) / (max - min)) * (height - padY * 2);
}

function xOf(index: number, count: number): number {
  if (count <= 1) {
    return padX;
  }
  return padX + (index / (count - 1)) * (width - padX - 8);
}

function line(points: Array<{ x: number; y: number }>): string {
  return points.map((point, index) => `${index === 0 ? "M" : "L"}${point.x.toFixed(1)} ${point.y.toFixed(1)}`).join(" ");
}

export function AnomalyChart({ points, caption }: AnomalyChartProps) {
  const placed = points.map((point, index) => ({
    ...point,
    x: xOf(index, points.length),
    y: point.value === null ? null : yOf(point.value),
  }));
  const observed = placed.filter((point) => point.kind === "observed" && point.y !== null);
  const forecast = placed.filter((point) => point.kind === "forecast" && point.y !== null);
  const bridge =
    observed.length > 0 && forecast.length > 0
      ? [observed[observed.length - 1], forecast[0]]
      : [];
  const band = placed.filter((point) => point.low !== undefined && point.high !== undefined && point.y !== null);
  const bandPath =
    band.length > 0
      ? `${line(band.map((point) => ({ x: point.x, y: yOf(point.high ?? 0) })))} ${line(
          [...band].reverse().map((point) => ({ x: point.x, y: yOf(point.low ?? 0) })),
        ).replace("M", "L")} Z`
      : "";

  return (
    <figure className="chart">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={caption}>
        {[0, -20, -40].map((tick) => (
          <g key={tick}>
            <line className="chart-grid" x1={padX} x2={width - 4} y1={yOf(tick)} y2={yOf(tick)} />
            <text className="chart-tick" x={2} y={yOf(tick) + 3}>
              {tick}
            </text>
          </g>
        ))}
        {bandPath ? <path className="chart-band" d={bandPath} /> : null}
        {observed.length > 1 ? <path className="chart-observed" d={line(observed.map((point) => ({ x: point.x, y: point.y ?? 0 })))} /> : null}
        {bridge.length === 2 ? (
          <path
            className="chart-forecast"
            d={line(bridge.map((point) => ({ x: point.x, y: point.y ?? 0 })))}
          />
        ) : null}
        {forecast.length > 1 ? <path className="chart-forecast" d={line(forecast.map((point) => ({ x: point.x, y: point.y ?? 0 })))} /> : null}
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
        {points.map((point) => (
          <span key={point.label}>{point.label}</span>
        ))}
      </div>
      <figcaption className="chart-key">
        <span><i className="swatch observed" /> Observado</span>
        <span><i className="swatch forecast" /> Pronóstico</span>
        <span><i className="swatch band" /> Incertidumbre</span>
      </figcaption>
    </figure>
  );
}
