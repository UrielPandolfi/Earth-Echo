import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { AftershockForecasts } from "../domain/generated";
import { AftershockForecastView, aftershockSentence } from "./AftershockForecast";

const forecasts: AftershockForecasts = {
  status: "available",
  events: [{
    event_id: "us7000txrk",
    magnitude: 4.5,
    latitude: 44.4539,
    longitude: -129.6205,
    depth_km: null,
    origin_time: null,
    model_name: "Reasenberg-Jones",
    region_radius: 10,
    region_radius_unit: null,
    geometry: "epicenter_only",
    geometry_note: "El punto es el centro declarado.",
    issued_at: "2026-11-15T08:17:28.440000Z",
    product_version: "1794731261591",
    retrieved_at: "2026-11-15T08:55:05.594587Z",
    checksum_sha256: "abc",
    original_url: "https://earthquake.usgs.gov/product/oaf/us7000txrk/us/1794731261591/forecast.json",
    windows: [
      { label: "1 Day", valid_from: "2026-11-15T09:00:00Z", valid_to: "2026-11-16T09:00:00Z", temporal_state: "expired", bins: [{ magnitude: 3, probability: 0.01193, median_count: 0, p95_minimum: 0, p95_maximum: 0 }] },
      { label: "1 Year", valid_from: "2026-11-15T09:00:00Z", valid_to: "2027-11-15T09:00:00Z", temporal_state: "in_progress", bins: [{ magnitude: 3, probability: 0.1309, median_count: 0, p95_minimum: 0, p95_maximum: 2 }, { magnitude: 5, probability: 0.00173, median_count: 0, p95_minimum: 0, p95_maximum: 0 }] },
    ],
  }],
  limitation: "No anticipa cualquier terremoto.",
};

afterEach(() => cleanup());

describe("réplicas USGS", () => {
  it("elige un horizonte vigente y conserva la probabilidad publicada", () => {
    const onWindow = vi.fn();
    render(<AftershockForecastView forecasts={forecasts} eventId="us7000txrk" windowLabel={null} magnitude={5} onEvent={() => undefined} onWindow={onWindow} onMagnitude={() => undefined} />);
    const year = forecasts.events[0].windows[1];
    expect(screen.getByText(aftershockSentence(forecasts.events[0], year.label, 5, 0.00173))).toBeTruthy();
    expect(screen.queryByText(/Este horizonte está vencido/)).toBeNull();
    fireEvent.change(screen.getByLabelText("Horizonte de réplicas"), { target: { value: "1 Day" } });
    expect(onWindow).toHaveBeenCalledWith("1 Day");
  });

  it("marca un horizonte vencido y no inventa un pronóstico ausente", () => {
    render(<AftershockForecastView forecasts={forecasts} eventId="us7000txrk" windowLabel="1 Day" magnitude={3} onEvent={() => undefined} onWindow={() => undefined} onMagnitude={() => undefined} />);
    expect(screen.getByText(/Este horizonte está vencido/)).toBeTruthy();
    cleanup();
    render(<AftershockForecastView forecasts={{ ...forecasts, status: "missing_input", events: [], reason: "No se inventaron réplicas." }} eventId={null} windowLabel={null} magnitude={null} onEvent={() => undefined} onWindow={() => undefined} onMagnitude={() => undefined} />);
    expect(screen.getByText("No se inventaron réplicas.")).toBeTruthy();
    expect(screen.queryByText(/el USGS estima/)).toBeNull();
  });
});
