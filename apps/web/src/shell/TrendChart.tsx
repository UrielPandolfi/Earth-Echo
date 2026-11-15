interface TrendPoint {
  year: number;
  month: number;
  anomaly_c: number | null;
}

interface GuidePoint {
  year: number;
  month: number;
  anomaly_c: number;
}

interface TrendChartProps {
  label?: string;
  series: TrendPoint[];
  trendLine: GuidePoint[];
  lowLine: GuidePoint[];
  highLine: GuidePoint[];
}

const width = 640;
const height = 220;
const padLeft = 46;
const padRight = 12;
const padY = 16;

function keyOf(point: { year: number; month: number }): string {
  return `${point.year}-${point.month}`;
}

export function TrendChart({ series, trendLine, lowLine, highLine, label="Anomalía mensual de SST y recta ajustada" }: TrendChartProps) {
  const numbers = [
    ...series.flatMap((point) => (point.anomaly_c === null ? [] : [point.anomaly_c])),
    ...trendLine.map((point) => point.anomaly_c),
    ...lowLine.map((point) => point.anomaly_c),
    ...highLine.map((point) => point.anomaly_c),
  ];
  const min = numbers.length ? Math.min(...numbers) : -1;
  const max = numbers.length ? Math.max(...numbers) : 1;
  const span = max - min || 1;
  const yOf = (value: number) => padY + ((max - value) / span) * (height - padY * 2);
  const xOf = (index: number) =>
    padLeft + (series.length <= 1 ? 0 : (index / (series.length - 1)) * (width - padLeft - padRight));
  const indexOf = new Map(series.map((point, index) => [keyOf(point), index]));
  const segments: Array<Array<{ x: number; y: number }>> = [];
  let current: Array<{ x: number; y: number }> = [];
  series.forEach((point, index) => {
    if (point.anomaly_c === null) {
      if (current.length) {
        segments.push(current);
        current = [];
      }
      return;
    }
    current.push({ x: xOf(index), y: yOf(point.anomaly_c) });
  });
  if (current.length) {
    segments.push(current);
  }
  const guide = (points: GuidePoint[]) => {
    const placed = points.flatMap((point) => {
      const index = indexOf.get(keyOf(point));
      return index === undefined ? [] : [{ x: xOf(index), y: yOf(point.anomaly_c) }];
    });
    return placed.map((point, index) => `${index === 0 ? "M" : "L"}${point.x.toFixed(1)} ${point.y.toFixed(1)}`).join(" ");
  };

  return (
    <figure className="chart trend-chart">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={label}>
        <line className="chart-grid" x1={padLeft} x2={width - padRight} y1={yOf(0)} y2={yOf(0)} />
        <text className="chart-tick" x={4} y={yOf(0) + 3}>0 °C</text>
        {lowLine.length > 1 && highLine.length > 1 ? (
          <path className="chart-band" d={`${guide(lowLine)} ${guide([...highLine].reverse()).replace("M", "L")} Z`} />
        ) : null}
        {segments.map((segment, index) => (
          <path key={index} className="chart-observed" d={segment.map((point, pointIndex) => `${pointIndex === 0 ? "M" : "L"}${point.x.toFixed(1)} ${point.y.toFixed(1)}`).join(" ")} />
        ))}
        {guide(trendLine) ? <path className="chart-trend" d={guide(trendLine)} /> : null}
      </svg>
      <figcaption className="chart-key">
        <span><i className="swatch observed" /> Anomalía mensual</span>
        {trendLine.length>1 && <span><i className="swatch trend" /> Componente lineal</span>}
        {lowLine.length>1 && highLine.length>1 && <span><i className="swatch band" /> Intervalo de la pendiente</span>}
      </figcaption>
    </figure>
  );
}
