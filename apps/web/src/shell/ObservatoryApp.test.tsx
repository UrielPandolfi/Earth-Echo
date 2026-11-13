import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ObservatoryApp } from "./ObservatoryApp";
import { activeGlobeCount, type GlobeFactory, type GlobeHandle } from "../globe/lifecycle";

function createGlobe(): GlobeFactory {
  return () => {
    const handle: GlobeHandle = { destroy() {} };
    return handle;
  };
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("observatorio demo", () => {
  it("cambia conteos, tiempo y análisis sin salir del modo simulado", async () => {
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
    expect(screen.getByText("1.284 señales")).toBeTruthy();
    expect(activeGlobeCount()).toBe(1);

    fireEvent.click(screen.getByRole("checkbox", { name: /Observaciones/ }));
    expect(screen.getByText("442 señales")).toBeTruthy();
    expect(screen.getByText("Concepto · datos simulados")).toBeTruthy();

    fireEvent.change(screen.getByRole("searchbox", { name: "Buscar región o fenómeno" }), {
      target: { value: "Amazonía" },
    });
    expect(screen.getByText("Sin consulta. La búsqueda se conecta en la fase 04.")).toBeTruthy();
    expect(screen.queryByRole("listbox", { name: /resultados/i })).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "+7 días" }));
    fireEvent.click(screen.getByRole("tab", { name: "Datos" }));
    expect(screen.getByText(/\+7 días · tramo estimado/)).toBeTruthy();
    expect(screen.getByText("No disponible")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Ver análisis completo" }));
    expect(screen.getByRole("dialog").textContent).toMatch(/No hay un análisis calculado/);
    expect(activeGlobeCount()).toBe(1);
  });
});
