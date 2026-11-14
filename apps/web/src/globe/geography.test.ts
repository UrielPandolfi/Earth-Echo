import { describe, expect, it } from "vitest";
import {
  americasPreset,
  antimeridianFrame,
  facingCamera,
  frameExtent,
  isClick,
  placeMarkers,
} from "./geography";

describe("encuadre geográfico", () => {
  it("centra el preset en América y mantiene el planeta en rango", () => {
    expect(americasPreset.longitude).toBeGreaterThan(-110);
    expect(americasPreset.longitude).toBeLessThan(-30);
    expect(americasPreset.latitude).toBeLessThan(10);
    expect(americasPreset.latitude).toBeGreaterThan(-40);
    expect(americasPreset.heightMeters).toBeGreaterThan(250_000);
    expect(americasPreset.heightMeters).toBeLessThan(28_000_000);
  });

  it("cruza el antimeridiano por el lado corto", () => {
    const framed = frameExtent(antimeridianFrame);
    expect(framed.status).toBe("framed");
    if (framed.status !== "framed") {
      return;
    }
    expect(Math.abs(framed.view.longitude)).toBeGreaterThan(150);
    expect(framed.view.heightMeters).toBeLessThan(8_000_000);
  });

  it("rechaza un oeste mayor que el este sin marcar la costura", () => {
    const framed = frameExtent({
      west: 170,
      south: -5,
      east: -170,
      north: 5,
      crossesAntimeridian: false,
    });
    expect(framed.status).toBe("unavailable");
  });

  it("encuadra una región diminuta sin colapsar la altura a cero", () => {
    const framed = frameExtent({
      west: -60,
      south: -3,
      east: -59.999,
      north: -2.999,
      crossesAntimeridian: false,
    });
    expect(framed.status).toBe("framed");
    if (framed.status === "framed") {
      expect(framed.view.heightMeters).toBeGreaterThanOrEqual(25_000);
    }
  });

  it("permite encuadrar un contorno glaciar por acción explícita", () => {
    const framed = frameExtent({west:-73.38148918,south:-50.687461237,east:-73.036936128,north:-50.460214006,crossesAntimeridian:false});
    expect(framed.status).toBe('framed');
    if (framed.status==='framed') {
      expect(framed.view.heightMeters).toBeGreaterThanOrEqual(25_000);
      expect(framed.view.heightMeters).toBeLessThan(100_000);
    }
    expect(americasPreset.heightMeters).toBe(13_200_000);
  });

  it("oculta el punto opuesto a la cámara", () => {
    expect(facingCamera(-64, -14, 120, 15)).toBe(false);
    expect(facingCamera(-64, -14, -60, -3)).toBe(true);
  });

  it("distingue un clic de un arrastre y esconde rótulos que no caben", () => {
    expect(isClick(2, 3)).toBe(true);
    expect(isClick(12, 0)).toBe(false);
    const placed = placeMarkers(
      [
        { id: "a", title: "A", x: 40, y: 80, facing: true, priority: 1 },
        { id: "b", title: "B", x: 48, y: 86, facing: true, priority: 2 },
        { id: "c", title: "C", x: 20, y: 20, facing: true, priority: 3 },
        { id: "d", title: "D", x: 100, y: 100, facing: false, priority: 4 },
      ],
      400,
      300,
    );
    expect(placed.find((item) => item.id === "b")?.visible).toBe(true);
    expect(placed.find((item) => item.id === "a")?.visible).toBe(false);
    expect(placed.find((item) => item.id === "c")?.visible).toBe(false);
    expect(placed.find((item) => item.id === "d")?.visible).toBe(false);
  });
});
