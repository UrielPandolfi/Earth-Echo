import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { EnsoOutlook } from "../domain/generated";
import { EnsoForecastView, ensoSentence } from "./EnsoForecast";

const outlook: EnsoOutlook = {
  status: "available",
  issue_time_basis: "Sin hora UTC.",
  source_url: "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/probabilities/",
  discussion_url: "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_advisory/ensodisc.shtml",
  edition: "2026-11",
  phases: [
    { season: "OND 2026", order: 0, valid_from: "2026-10-01T00:00:00Z", valid_to: "2027-01-01T00:00:00Z", temporal_state: "in_progress", la_nina_percent: 1, neutral_percent: 4, el_nino_percent: 95, roni_p50_c: 2.5 },
    { season: "FMA 2027", order: 4, valid_from: "2027-02-01T00:00:00Z", valid_to: "2027-05-01T00:00:00Z", temporal_state: "future", la_nina_percent: 0, neutral_percent: 2, el_nino_percent: 98, roni_p50_c: null },
  ],
  observation: { season_id: "ASO 2026", valid_from: "2026-08-01T00:00:00Z", valid_to: "2026-11-01T00:00:00Z", roni_c: 2, season_phase: "El Niño", note: "No es un episodio de cinco temporadas." },
  region: { id: "nino-3.4", name: "Niño 3.4", sample_id: "nino-3.4", geometry: { type: "MultiPolygon", coordinates: [] }, extent: { west: -170, south: -5, east: -120, north: 5, crosses_antimeridian: false }, quality: "referencia" },
  meaning: "Relación climática general, no un pronóstico local.",
  limitation: "No predice inundaciones.",
};

afterEach(() => cleanup());

describe("ENSO", () => {
  it("muestra la frase oficial del trimestre y permite cambiarlo", () => {
    const onSelect = vi.fn();
    render(<EnsoForecastView outlook={outlook} selected="FMA 2027" onSelect={onSelect} />);
    expect(screen.getByText(ensoSentence(outlook.phases[1]))).toBeTruthy();
    expect(screen.getByText(/cinco temporadas/)).toBeTruthy();
    expect(screen.getByRole("heading", { name: "¿Qué significa para el planeta?" })).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Trimestre ENSO"), { target: { value: "OND 2026" } });
    expect(onSelect).toHaveBeenCalledWith("OND 2026");
  });

  it("no inventa una frase cuando faltan las probabilidades", () => {
    render(<EnsoForecastView outlook={{ ...outlook, status: "missing_input", phases: [], reason: "Sin tabla oficial." }} selected={null} onSelect={() => undefined} />);
    expect(screen.getByText("Sin tabla oficial.")).toBeTruthy();
    expect(screen.queryByText(/NOAA estima/)).toBeNull();
  });
});
