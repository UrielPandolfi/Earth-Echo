/**
 * Escenario visual DEMO. Los conteos y la serie reproducen la composición
 * de la referencia. No son observaciones, pronósticos ni un censo de señales.
 */

export interface DemoCategory {
  id: string;
  label: string;
  icon: "rain" | "heat" | "fire" | "ocean" | "land" | "space";
  displayCount: number;
  phenomenonIds: string[];
}

export interface DemoInfoType {
  id: string;
  label: string;
  symbol: "observation" | "risk" | "forecast";
  displayCount: number;
}

export interface DemoLayer {
  id: string;
  label: string;
  variableId: string;
  legendTitle: string;
  legendCaption: string;
  scaleMin: string;
  scaleMax: string;
}

export interface DemoSeriesPoint {
  label: string;
  kind: "observed" | "forecast";
  /** Anomalía sintética en puntos porcentuales. null es un hueco, no cero. */
  value: number | null;
  low?: number;
  high?: number;
}

export interface DemoRelatedSignal {
  id: string;
  title: string;
  detail: string;
  level: string;
  icon: "heat" | "leaf";
}

export interface DemoSignal {
  id: string;
  title: string;
  regionName: string;
  regionId: string;
  statusLabel: string;
  summary: string;
  variableLabel: string;
  variableId: string;
  anomalyLabel: string;
  horizonLabel: string;
  coverageLabel: string;
  sources: Array<{ id: string; name: string; integration: string }>;
  series: DemoSeriesPoint[];
  related: DemoRelatedSignal[];
}

export const demoScenario = {
  id: "amazonia-central-visual",
  mode: "demo" as const,
  badge: "Concepto · datos simulados",
  signalQuery:
    "Suma de displayCount de los tipos de información activos en este escenario. No consulta observaciones.",
  categories: [
    { id: "rain", label: "Lluvia e inundación", icon: "rain", displayCount: 324, phenomenonIds: ["F01", "F07", "F12", "F13"] },
    { id: "heat", label: "Calor y sequía", icon: "heat", displayCount: 287, phenomenonIds: ["F02", "F03", "F11", "F14"] },
    { id: "fire", label: "Incendios", icon: "fire", displayCount: 146, phenomenonIds: ["F15"] },
    { id: "ocean", label: "Océanos y corales", icon: "ocean", displayCount: 118, phenomenonIds: ["F17", "F18", "F19", "F20"] },
    { id: "land", label: "Tierra y volcanes", icon: "land", displayCount: 96, phenomenonIds: ["F24", "F25", "F26", "F27", "F28"] },
    { id: "space", label: "Clima espacial", icon: "space", displayCount: 42, phenomenonIds: ["F29", "F30"] },
  ] satisfies DemoCategory[],
  informationTypes: [
    { id: "observation", label: "Observaciones", symbol: "observation", displayCount: 842 },
    { id: "risk", label: "Condiciones de riesgo", symbol: "risk", displayCount: 213 },
    { id: "forecast", label: "Pronósticos", symbol: "forecast", displayCount: 229 },
  ] satisfies DemoInfoType[],
  layers: [
    {
      id: "soil",
      label: "Humedad del suelo",
      variableId: "V08",
      legendTitle: "Humedad del suelo",
      legendCaption: "Anomalía respecto de lo habitual",
      scaleMin: "−40 %",
      scaleMax: "+40 %",
    },
    {
      id: "temperature",
      label: "Temperatura",
      variableId: "V02",
      legendTitle: "Temperatura del aire",
      legendCaption: "Anomalía sintética, no temperatura medida",
      scaleMin: "−8 °C",
      scaleMax: "+8 °C",
    },
    {
      id: "precipitation",
      label: "Precipitación",
      variableId: "V01",
      legendTitle: "Precipitación",
      legendCaption: "Anomalía sintética del acumulado",
      scaleMin: "−50 %",
      scaleMax: "+50 %",
    },
  ] satisfies DemoLayer[],
  signal: {
    id: "demo-f11-humedad-suelo",
    title: "Déficit de humedad",
    regionName: "Amazonía central",
    regionId: "demo-amazonia-central",
    statusLabel: "Riesgo en evaluación",
    summary: "La humedad del suelo está por debajo de lo habitual para esta época.",
    variableLabel: "Humedad del suelo",
    variableId: "V08",
    anomalyLabel: "Anomalía respecto de lo habitual",
    horizonLabel: "2–4 semanas",
    coverageLabel: "Amazonía central",
    sources: [
      { id: "D02", name: "NASA SMAP SPL3SMP E", integration: "credencial requerida" },
      { id: "D03", name: "NASA GLDAS", integration: "documentada" },
    ],
    series: [
      { label: "Dic", kind: "observed", value: -1 },
      { label: "Ene", kind: "observed", value: -4 },
      { label: "Feb", kind: "observed", value: -3 },
      { label: "Mar", kind: "observed", value: -12 },
      { label: "Abr", kind: "observed", value: -27 },
      { label: "+7 d", kind: "forecast", value: -31, low: -38, high: -23 },
      { label: "May", kind: "forecast", value: -34, low: -45, high: -22 },
    ],
    related: [
      {
        id: "demo-temp-elevada",
        title: "Temperatura elevada",
        detail: "+1,8 °C sobre el promedio estacional",
        level: "Moderada",
        icon: "heat",
      },
      {
        id: "demo-ndvi",
        title: "Vegetación bajo estrés",
        detail: "Índice de verdor de referencia · −14 %",
        level: "Moderada",
        icon: "leaf",
      },
    ],
  } satisfies DemoSignal,
  timelineStops: [-30, -7, 0, 7, 30],
};

export type DemoScenario = typeof demoScenario;
