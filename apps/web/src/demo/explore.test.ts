import { describe, expect, it } from "vitest";
import { HERO_ID, openingRecords, wideRecords } from "./catalog";
import { buildField, clusterRecords, recordVisibleAt, searchDemo, visibleRecords, instantForDay } from "./explore";

const allOn = {
  wide: false,
  categoryIds: ["rain", "heat", "fire", "ocean", "land", "space"],
  infoTypeIds: ["observation", "risk", "forecast"],
  timelineDays: 0,
  clusterDegrees: 0,
};

describe("escenario demo", () => {
  it("es determinista y distingue la ficha de apertura", () => {
    expect(openingRecords()).toBe(openingRecords());
    expect(openingRecords()[0]?.id).toBe(HERO_ID);
    expect(openingRecords()[0]?.value).toBe(-0.041);
    expect(openingRecords()[0]?.series.some((point) => point.value === null)).toBe(true);
  });

  it("cambia las señales visibles entre el pasado, ahora y el futuro", () => {
    const now = visibleRecords(allOn).map((item) => item.id);
    const past = visibleRecords({ ...allOn, timelineDays: -30 }).map((item) => item.id);
    const future = visibleRecords({ ...allOn, timelineDays: 10 }).map((item) => item.id);
    expect(now).toContain(HERO_ID);
    expect(past).not.toContain(HERO_ID);
    expect(future).not.toContain(HERO_ID);
    expect(past.length).toBeGreaterThan(0);
    expect(future.every((id) => openingRecords().find((item) => item.id === id)?.infoType === "forecast")).toBe(true);
  });

  it("no muestra un pronóstico antes de su inicialización", () => {
    const forecast = openingRecords().find((item) => item.infoType === "forecast");
    expect(forecast).toBeTruthy();
    if (!forecast) {
      return;
    }
    expect(recordVisibleAt(forecast, instantForDay(-20))).toBe(false);
    expect(recordVisibleAt(forecast, instantForDay(2))).toBe(true);
  });

  it("no junta los dos lados del antimeridiano en un grupo", () => {
    const west = wideRecords().find((item) => item.id === "wide-dateline-west");
    const east = wideRecords().find((item) => item.id === "wide-dateline-east");
    expect(west && east).toBeTruthy();
    if (!west || !east) {
      return;
    }
    const grouped = clusterRecords([west, east], 10);
    expect(grouped.clusters).toHaveLength(0);
    expect(grouped.singles).toHaveLength(2);
  });

  it("deja huecos transparentes en el campo ilustrativo", () => {
    const field = buildField("soil");
    const transparent = field.rgba.filter((_, index) => index % 4 === 3 && field.rgba[index] === 0);
    const painted = field.rgba.filter((_, index) => index % 4 === 3 && field.rgba[index] === 170);
    expect(transparent.length).toBe(field.missingCells);
    expect(painted.length).toBeGreaterThan(0);
    const hole = field.rgba.findIndex((_, index) => index % 4 === 3 && field.rgba[index] === 0);
    expect(field.rgba[hole - 3]).toBe(0);
    expect(field.rgba[hole - 2]).toBe(0);
    expect(field.rgba[hole - 1]).toBe(0);
  });

  it("encuentra la señal de apertura por texto y la distingue de una región", () => {
    const hits = searchDemo("déficit", openingRecords());
    expect(hits.some((hit) => hit.kind === "signal" && hit.id === HERO_ID)).toBe(true);
    expect(searchDemo("amazonia", openingRecords()).some((hit) => hit.kind === "region")).toBe(true);
  });
});
