import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { TechnicalApp } from "./TechnicalApp";
import { activeGlobeCount, type GlobeFactory, type GlobeHandle } from "./globe/lifecycle";

function factory(): GlobeFactory {
  return () => {
    const handle: GlobeHandle = { destroy() {} };
    return handle;
  };
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("pantalla técnica", () => {
  it("vuelve a montar el globo sin dejar dos instancias", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo) => {
        const url = String(input);
        const body = url.endsWith("/health")
          ? {
              schema_version: "1.0",
              status: "ok",
              service: "earth-echo-api",
              time: "2026-11-13T00:00:00Z",
              checks: ["process"],
            }
          : {
              schema_version: "1.0",
              checked_at: "2026-11-13T00:00:00Z",
              live_probe: "not_performed",
              note: "sin sondeo",
              providers: [],
            };
        return new Response(JSON.stringify(body), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }),
    );
    render(<TechnicalApp createGlobe={factory()} />);
    expect(await screen.findByText("Proceso de la API en ejecución. Chequeo: process.")).toBeTruthy();
    expect(activeGlobeCount()).toBe(1);
    fireEvent.click(screen.getByRole("button", { name: "Desmontar y volver a montar" }));
    expect(activeGlobeCount()).toBe(1);
    expect(screen.getByText("Instancias activas: 1")).toBeTruthy();
  });
});
