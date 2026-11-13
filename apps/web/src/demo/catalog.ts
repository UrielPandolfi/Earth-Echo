import type { DemoSeriesPoint } from "./scenario";

/** Semilla fija. El mismo texto siempre produce el mismo escenario. */
export const DEMO_SEED = "earth-echo-demo-2026-11-13";
export const DEMO_EPOCH_MS = Date.parse("2026-11-13T00:00:00.000Z");
export const DAY_MS = 86_400_000;
export const HERO_ID = "demo-open-humidity-amazonia";

export type InfoKind = "observation" | "risk" | "forecast";

export interface DemoRecord {
  id: string;
  dataMode: "demo";
  title: string;
  categoryId: string;
  infoType: InfoKind;
  phenomenonId: string;
  variableId: string;
  /** Unidad del valor ilustrativo. No es una probabilidad de ocurrencia. */
  unit: string;
  unitMeaning: string;
  value: number | null;
  longitude: number;
  latitude: number;
  regionId: string;
  regionName: string;
  validFrom: string;
  validTo: string;
  availableAt: string;
  initializationTime: string | null;
  intendedSourceIds: string[];
  series: DemoSeriesPoint[];
  summary: string;
}

export interface DemoRegion {
  id: string;
  name: string;
  longitude: number;
  latitude: number;
  west: number;
  south: number;
  east: number;
  north: number;
  crossesAntimeridian: boolean;
}

export const demoRegions: DemoRegion[] = [
  { id: "amazonia", name: "Amazonía central", longitude: -60, latitude: -3, west: -72, south: -12, east: -48, north: 6, crossesAntimeridian: false },
  { id: "andes", name: "Andes centrales", longitude: -68, latitude: -16, west: -76, south: -28, east: -62, north: -6, crossesAntimeridian: false },
  { id: "atlantic", name: "Atlántico tropical", longitude: -38, latitude: 8, west: -52, south: -4, east: -24, north: 20, crossesAntimeridian: false },
  { id: "pacific", name: "Pacífico oriental", longitude: -92, latitude: 2, west: -108, south: -12, east: -78, north: 16, crossesAntimeridian: false },
  { id: "caribbean", name: "Caribe", longitude: -74, latitude: 16, west: -88, south: 8, east: -60, north: 24, crossesAntimeridian: false },
  { id: "patagonia", name: "Patagonia", longitude: -70, latitude: -46, west: -76, south: -55, east: -64, north: -38, crossesAntimeridian: false },
  { id: "sahel", name: "Sahel", longitude: 2, latitude: 16, west: -12, south: 10, east: 18, north: 22, crossesAntimeridian: false },
  { id: "dateline", name: "Pacífico occidental", longitude: 179, latitude: 1, west: 170, south: -8, east: -170, north: 10, crossesAntimeridian: true },
];

const openingRegions = ["amazonia", "andes", "atlantic", "pacific", "caribbean", "patagonia"] as const;

function hashSeed(text: string): number {
  let hash = 2_166_136_261;
  for (const char of text) {
    hash = Math.imul(hash ^ char.charCodeAt(0), 1_677_761_9);
  }
  return hash >>> 0;
}

function mulberry32(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4_294_967_296;
  };
}

function iso(ms: number): string {
  return new Date(ms).toISOString().replace(".000Z", "Z");
}

function seriesFor(random: () => number, infoType: InfoKind, withGap: boolean): DemoSeriesPoint[] {
  const labels = infoType === "forecast" ? ["E0", "+1 d", "+3 d", "+5 d", "+8 d", "+12 d"] : ["−12 d", "−9 d", "−6 d", "−3 d", "−1 d", "ahora"];
  return labels.map((label, index) => {
    const kind = infoType === "forecast" || index === labels.length - 1 && infoType !== "observation" ? "forecast" : "observed";
    const pointKind = infoType === "forecast" ? "forecast" : index < 4 ? "observed" : "forecast";
    if (withGap && index === 2) {
      return { label, kind: pointKind, value: null };
    }
    const drift = infoType === "risk" ? -0.02 * index : -0.008 * index;
    const value = Math.round((random() * 0.06 - 0.03 + drift) * 1000) / 1000;
    return { label, kind: pointKind === "forecast" ? "forecast" : kind === "forecast" ? "forecast" : "observed", value };
  });
}

function windows(index: number, infoType: InfoKind): Pick<DemoRecord, "validFrom" | "validTo" | "availableAt" | "initializationTime"> {
  if (infoType === "observation" && index % 5 === 0) {
    return {
      validFrom: iso(DEMO_EPOCH_MS - 40 * DAY_MS),
      validTo: iso(DEMO_EPOCH_MS - 10 * DAY_MS),
      availableAt: iso(DEMO_EPOCH_MS - 40 * DAY_MS),
      initializationTime: null,
    };
  }
  if (infoType === "forecast") {
    return {
      validFrom: iso(DEMO_EPOCH_MS),
      validTo: iso(DEMO_EPOCH_MS + 12 * DAY_MS),
      availableAt: iso(DEMO_EPOCH_MS - DAY_MS),
      initializationTime: iso(DEMO_EPOCH_MS - DAY_MS),
    };
  }
  if (infoType === "risk") {
    return {
      validFrom: iso(DEMO_EPOCH_MS - 5 * DAY_MS),
      validTo: iso(DEMO_EPOCH_MS + 4 * DAY_MS),
      availableAt: iso(DEMO_EPOCH_MS - 5 * DAY_MS),
      initializationTime: null,
    };
  }
  return {
    validFrom: iso(DEMO_EPOCH_MS - 15 * DAY_MS),
    validTo: iso(DEMO_EPOCH_MS + 2 * DAY_MS),
    availableAt: iso(DEMO_EPOCH_MS - 15 * DAY_MS),
    initializationTime: null,
  };
}

const profiles = {
  rain: { categoryId: "rain", phenomenonId: "F01", variableId: "V01", unit: "mm", unitMeaning: "acumulado ilustrativo del intervalo, no una probabilidad" },
  heat: { categoryId: "heat", phenomenonId: "F11", variableId: "V08", unit: "m³/m³", unitMeaning: "anomalía ilustrativa de humedad, no humedad absoluta ni probabilidad" },
  fire: { categoryId: "fire", phenomenonId: "F15", variableId: "V13", unit: "índice", unitMeaning: "índice ilustrativo de peligro meteorológico, no probabilidad de ignición" },
  ocean: { categoryId: "ocean", phenomenonId: "F19", variableId: "V15", unit: "°C", unitMeaning: "anomalía ilustrativa de temperatura superficial, no daño confirmado" },
  land: { categoryId: "land", phenomenonId: "F25", variableId: "V01", unit: "mm", unitMeaning: "lluvia ilustrativa usada como contexto, no un deslizamiento fechado" },
  space: { categoryId: "space", phenomenonId: "F29", variableId: "V24", unit: "km/s", unitMeaning: "velocidad ilustrativa, no un índice de tormenta real" },
} as const;

const regionProfile: Record<string, keyof typeof profiles> = {
  amazonia: "heat",
  andes: "land",
  atlantic: "ocean",
  pacific: "rain",
  caribbean: "rain",
  patagonia: "heat",
  sahel: "fire",
  dateline: "ocean",
};

function makeRecord(random: () => number, region: DemoRegion, index: number, infoType: InfoKind): DemoRecord {
  const profile = profiles[regionProfile[region.id] ?? "heat"];
  const angle = random() * Math.PI * 2;
  const radius = random() * 6;
  const longitude = region.crossesAntimeridian ? region.longitude : region.longitude + Math.cos(angle) * radius;
  const latitude = Math.max(-80, Math.min(80, region.latitude + Math.sin(angle) * radius * 0.6));
  const titles = {
    observation: "Lectura ilustrativa",
    risk: "Condición ilustrativa",
    forecast: "Pronóstico ilustrativo",
  };
  return {
    id: `demo-${region.id}-${infoType}-${index}`,
    dataMode: "demo",
    title: titles[infoType],
    ...profile,
    infoType,
    value: infoType === "observation" && index % 11 === 0 ? null : Math.round((random() * 0.08 - 0.05) * 1000) / 1000,
    longitude,
    latitude,
    regionId: region.id,
    regionName: region.name,
    ...windows(index, infoType),
    intendedSourceIds: profile.variableId === "V08" ? ["D02", "D03"] : ["D07"],
    series: seriesFor(random, infoType, index % 7 === 0),
    summary: `${titles[infoType]} en ${region.name}. El valor es del escenario demo y la fuente está prevista, no conectada.`,
  };
}

function hero(random: () => number): DemoRecord {
  const region = demoRegions[0];
  if (!region) {
    throw new Error("Falta la región de apertura.");
  }
  const record = makeRecord(random, region, 0, "observation");
  return {
    ...record,
    id: HERO_ID,
    title: "Déficit de humedad",
    categoryId: "heat",
    phenomenonId: "F11",
    variableId: "V08",
    unit: "m³/m³",
    unitMeaning: "anomalía ilustrativa respecto de un valor de referencia inventado; no es humedad medida ni una probabilidad",
    value: -0.041,
    longitude: -60,
    latitude: -3,
    intendedSourceIds: ["D02", "D03"],
    validFrom: iso(DEMO_EPOCH_MS - 15 * DAY_MS),
    validTo: iso(DEMO_EPOCH_MS + 2 * DAY_MS),
    availableAt: iso(DEMO_EPOCH_MS - 15 * DAY_MS),
    initializationTime: null,
    summary: "La humedad ilustrativa del escenario está por debajo del valor de referencia inventado para esta ficha.",
    series: [
      { label: "−12 d", kind: "observed", value: -0.008 },
      { label: "−9 d", kind: "observed", value: -0.012 },
      { label: "−6 d", kind: "observed", value: null },
      { label: "−3 d", kind: "observed", value: -0.027 },
      { label: "−1 d", kind: "observed", value: -0.036 },
      { label: "+5 d", kind: "forecast", value: -0.044, low: -0.058, high: -0.031 },
    ],
  };
}

let openingCache: DemoRecord[] | null = null;
let wideCache: DemoRecord[] | null = null;

export function openingRecords(): DemoRecord[] {
  if (openingCache) {
    return openingCache;
  }
  const random = mulberry32(hashSeed(DEMO_SEED));
  const records = [hero(random)];
  for (const regionId of openingRegions) {
    const region = demoRegions.find((item) => item.id === regionId);
    if (!region) {
      continue;
    }
    for (let index = 0; index < 28; index += 1) {
      const infoType: InfoKind = index % 6 === 0 ? "forecast" : index % 4 === 0 ? "risk" : "observation";
      records.push(makeRecord(random, region, index + 1, infoType));
    }
  }
  const caribbean = demoRegions.find((item) => item.id === "caribbean");
  const pacific = demoRegions.find((item) => item.id === "pacific");
  if (caribbean && pacific) {
    for (let index = 0; index < 10; index += 1) {
      const fire = makeRecord(random, caribbean, 40 + index, index % 3 === 0 ? "risk" : "observation");
      records.push({ ...fire, ...profiles.fire, id: `demo-fire-${index}` });
      const space = makeRecord(random, pacific, 60 + index, index % 4 === 0 ? "forecast" : "observation");
      records.push({ ...space, ...profiles.space, id: `demo-space-${index}` });
    }
  }
  openingCache = records;
  return records;
}

export function wideRecords(): DemoRecord[] {
  if (wideCache) {
    return wideCache;
  }
  const random = mulberry32(hashSeed(`${DEMO_SEED}:wide`));
  const extra: DemoRecord[] = [
    {
      ...makeRecord(random, demoRegions[7] ?? demoRegions[0]!, 1, "observation"),
      id: "wide-dateline-west",
      longitude: 179.2,
      latitude: 1,
    },
    {
      ...makeRecord(random, demoRegions[7] ?? demoRegions[0]!, 2, "observation"),
      id: "wide-dateline-east",
      longitude: -179.2,
      latitude: 1.1,
    },
  ];
  for (let index = 0; index < 1200; index += 1) {
    const region = demoRegions[index % demoRegions.length] ?? demoRegions[0]!;
    const infoType: InfoKind = index % 7 === 0 ? "forecast" : index % 5 === 0 ? "risk" : "observation";
    extra.push({ ...makeRecord(random, region, index + 20, infoType), id: `wide-${index}` });
  }
  wideCache = [...openingRecords(), ...extra];
  return wideCache;
}

export function recordsFor(wide: boolean): DemoRecord[] {
  return wide ? wideRecords() : openingRecords();
}
