import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { visibleRecords } from "../demo/explore";
import { formatCount } from "../demo/queries";
import { activeGlobeCount, type GlobeFactory, type GlobeHandle } from "../globe/lifecycle";
import { ObservatoryApp } from "./ObservatoryApp";

const categories = ["rain", "heat", "fire", "ocean", "land", "space"];

function createGlobe(): GlobeFactory {
  return () => {
    const handle: GlobeHandle = { destroy() {} };
    return handle;
  };
}

function countAt(days: number, infoTypeIds: string[]): number {
  return visibleRecords({
    wide: false,
    categoryIds: categories,
    infoTypeIds,
    timelineDays: days,
    clusterDegrees: 0,
  }).length;
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("observatorio demo", () => {
  it("filtra, busca y cambia el instante sin salir del modo simulado", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ schema_version: "1.0", total: 31, returned: 1, phenomena: [] }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );
    render(<ObservatoryApp createGlobe={createGlobe()} />);
    expect(await screen.findByText("31 fenómenos")).toBeTruthy();
    expect(screen.getByText("Concepto · datos simulados")).toBeTruthy();
    expect(screen.getByText(`${formatCount(countAt(0, ["observation", "risk", "forecast"]))} señales`)).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Déficit de humedad" })).toBeTruthy();
    expect(activeGlobeCount()).toBe(1);

    fireEvent.click(screen.getByRole("checkbox", { name: /Observaciones/ }));
    expect(screen.getByText(`${formatCount(countAt(0, ["risk", "forecast"]))} señales`)).toBeTruthy();
    expect(screen.getByText(/no cumple el filtro/)).toBeTruthy();

    fireEvent.change(screen.getByRole("searchbox", { name: "Buscar región o fenómeno" }), {
      target: { value: "Déficit" },
    });
    fireEvent.click(screen.getByRole("option", { name: /Déficit de humedad/ }));
    expect(screen.getByRole("heading", { name: "Déficit de humedad" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "+7 días" }));
    fireEvent.click(screen.getByRole("tab", { name: "Datos" }));
    expect(screen.getByText("Instante de la vista").closest("div")?.textContent).toMatch(/\+7 días/);
    expect(screen.getByText("No disponible")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Ver análisis completo" }));
    expect(screen.getByRole("dialog").textContent).toMatch(/Déficit de humedad/);
    expect(screen.getByRole("dialog").textContent).toMatch(/Fuentes previstas/);
    expect(activeGlobeCount()).toBe(1);

    fireEvent.click(screen.getByRole("button", { name: "REAL" }));
    expect((await screen.findAllByText(/El escenario DEMO no se usó como reemplazo/)).length).toBeGreaterThan(0);
    expect(screen.queryByRole("heading", { name: "Déficit de humedad" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "DEMO" }));
    expect(screen.getByRole("heading", { name: "Déficit de humedad" })).toBeTruthy();
  });
});
