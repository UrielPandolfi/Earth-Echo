import { describe, expect, it } from "vitest";
import { demoScenario } from "./scenario";
import { formatCount, signalDisplayCount, timelineKind, timelineLabel } from "./queries";

describe("consultas del escenario demo", () => {
  it("suma los tipos activos y no trata el total como un número suelto", () => {
    const ids = demoScenario.informationTypes.map((item) => item.id);
    const expected = demoScenario.informationTypes.reduce((sum, item) => sum + item.displayCount, 0);
    expect(signalDisplayCount(ids)).toBe(expected);
    expect(formatCount(expected)).toBe("1.284");
  });

  it("al quitar observaciones resta solo ese conteo", () => {
    const ids = demoScenario.informationTypes.map((item) => item.id).filter((id) => id !== "observation");
    expect(signalDisplayCount(ids)).toBe(213 + 229);
  });

  it("separa el pasado observado del tramo futuro", () => {
    expect(timelineKind(0)).toBe("observado");
    expect(timelineKind(-7)).toBe("observado");
    expect(timelineKind(7)).toBe("pronostico");
    expect(timelineLabel(0)).toBe("Ahora");
    expect(timelineLabel(7)).toBe("+7 días");
  });
});
