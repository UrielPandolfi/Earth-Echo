import { describe, expect, it } from "vitest";
import type { DemoRecord } from "./catalog";
import { clusterRecords } from "./explore";

function synthetic(index: number): DemoRecord {
  return {
    id: `bench-${index}`,
    dataMode: "demo",
    title: "carga",
    categoryId: "ocean",
    infoType: "observation",
    phenomenonId: "F19",
    variableId: "V15",
    unit: "1",
    unitMeaning: "Carga sintética de rendimiento. No es una observación.",
    value: 1,
    longitude: ((index * 17) % 360) - 180,
    latitude: ((index * 13) % 160) - 80,
    regionId: "bench",
    regionName: "carga",
    validFrom: "2026-01-01T00:00:00Z",
    validTo: "2026-01-02T00:00:00Z",
    availableAt: "2026-01-01T00:00:00Z",
    initializationTime: null,
    intendedSourceIds: [],
    series: [],
    summary: "Carga sintética de rendimiento. No es una observación.",
  };
}

describe("agrupación de una carga sintética", () => {
  it("conserva el total científico al agrupar mil y diez mil puntos", () => {
    for (const size of [1_000, 10_000]) {
      const points = Array.from({ length: size }, (_, index) => synthetic(index));
      const started = performance.now();
      const grouped = clusterRecords(points, 8);
      const elapsed = performance.now() - started;
      const represented =
        grouped.singles.length + grouped.clusters.reduce((sum, cluster) => sum + cluster.count, 0);
      expect(represented).toBe(size);
      expect(grouped.clusters.length).toBeLessThan(size);
      expect(elapsed).toBeLessThan(size === 1_000 ? 150 : 500);
    }
  });
});
