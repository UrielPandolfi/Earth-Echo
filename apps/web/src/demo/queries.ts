import { demoScenario } from "./scenario";

export function formatCount(value: number): string {
  return new Intl.NumberFormat("es-AR").format(value);
}

export function signalDisplayCount(enabledInfoTypeIds: readonly string[]): number {
  return demoScenario.informationTypes
    .filter((item) => enabledInfoTypeIds.includes(item.id))
    .reduce((sum, item) => sum + item.displayCount, 0);
}

export function timelineLabel(days: number): string {
  if (days === 0) {
    return "Ahora";
  }
  const sign = days > 0 ? "+" : "";
  return `${sign}${days} días`;
}

export function timelineKind(days: number): "observado" | "pronostico" {
  return days > 0 ? "pronostico" : "observado";
}
