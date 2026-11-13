import { describe, expect, it } from "vitest";
import { formatCount, timelineKind, timelineLabel } from "./queries";

describe("etiquetas de consulta", () => {
  it("formatea miles con el separador local", () => {
    expect(formatCount(1284)).toBe("1.284");
  });

  it("separa el pasado observado del tramo futuro", () => {
    expect(timelineKind(0)).toBe("observado");
    expect(timelineKind(-7)).toBe("observado");
    expect(timelineKind(7)).toBe("pronostico");
    expect(timelineLabel(0)).toBe("Ahora");
    expect(timelineLabel(7)).toBe("+7 días");
  });
});
