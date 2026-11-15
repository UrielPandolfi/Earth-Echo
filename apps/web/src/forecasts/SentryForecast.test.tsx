import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import type { SentryAssessments, SentryObjectDetail } from "../domain/generated";
import { SentryForecastView, scenarioSentence, sentrySentence } from "./SentryForecast";

const assessments: SentryAssessments = {
  status: "available",
  signature_version: "2.0",
  retrieved_at: "2026-11-14T22:43:40.013421Z",
  checksum_sha256: "a".repeat(64),
  source_url: "https://ssd-api.jpl.nasa.gov/sentry.api",
  objects: [
    { designation: "2011 TO", fullname: "(2011 TO)", catalog_id: "bK11T00O", status: "current", cumulative_probability: 2.937e-6, cumulative_probability_text: "2.937e-06", palermo_cumulative: -6.15, palermo_max: -6.15, torino_max: 0, diameter_km: 0.018, absolute_magnitude_h: 26.32, v_inf_km_s: 8.55, potential_impacts: 1, year_range: "2064-2064", last_observation: "2013-01-12", removed_at: null },
    { designation: "2010 RF12", fullname: "(2010 RF12)", catalog_id: "bK10R12F", status: "current", cumulative_probability: 0.102637259069, cumulative_probability_text: "0.102637259069", palermo_cumulative: -2.96, palermo_max: -2.96, torino_max: 0, diameter_km: 0.007, absolute_magnitude_h: 28.4, v_inf_km_s: 5, potential_impacts: 70, year_range: "2095-2122", last_observation: "2010-09-12", removed_at: null },
  ],
  removed: [
    { designation: "2026 OA3", fullname: "2026 OA3", catalog_id: null, status: "removed", cumulative_probability: null, cumulative_probability_text: null, palermo_cumulative: null, palermo_max: null, torino_max: null, diameter_km: null, absolute_magnitude_h: null, v_inf_km_s: null, potential_impacts: null, year_range: null, last_observation: null, removed_at: "2026-11-11 15:44:45" },
  ],
  limitation: "No es una alerta de emergencia.",
  meaning: "La probabilidad acumulada es la publicada por Sentry.",
};

const detail: SentryObjectDetail = {
  ...assessments.objects[0],
  scenarios_status: "available",
  scenarios_reason: null,
  scenarios: [{ date_text: "2064-09-27.39", date_utc: "2064-09-27T09:21:36Z", probability: 2.937e-6, probability_text: "2.937e-06", palermo: -6.15, torino: 0, energy_mt: "1.983e-01", method: "IOBS", sigma_kind: "sigma_vi", sigma_text: "2.7919" }],
};

afterEach(() => cleanup());

describe("Sentry", () => {
  it("conserva una probabilidad diminuta y no la muestra como cero", () => {
    render(<SentryForecastView assessments={assessments} detail={detail} />);
    fireEvent.click(screen.getByText("(2011 TO)"));
    expect(screen.getByText(sentrySentence(assessments.objects[0]))).toBeTruthy();
    expect(screen.getByText(scenarioSentence(assessments.objects[0], detail.scenarios[0]))).toBeTruthy();
    expect(screen.getAllByText(/2\.937e-06 · cerca de 1 de cada/).length).toBeGreaterThan(0);
    expect(screen.queryByText(/0 %/)).toBeNull();
  });

  it("explica un retiro sin convertirlo en impacto y no inventa una tabla ausente", () => {
    render(<SentryForecastView assessments={assessments} detail={null} />);
    fireEvent.click(screen.getByRole("button", { name: /Retirados/ }));
    expect(screen.getByText(/no confirma un impacto/)).toBeTruthy();
    cleanup();
    render(<SentryForecastView assessments={{ ...assessments, status: "missing_input", objects: [], removed: [], reason: "No hay una tabla Sentry retenida." }} />);
    expect(screen.getByText("No hay una tabla Sentry retenida.")).toBeTruthy();
    expect(screen.queryByText(/Sentry publica una probabilidad/)).toBeNull();
  });
});
