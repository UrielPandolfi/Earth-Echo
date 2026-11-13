import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AssistantDrawer } from "./AssistantDrawer";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("asistente", () => {
  it("muestra la respuesta de herramientas cuando el modelo no está", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (String(url).endsWith("/status")) {
          return new Response(JSON.stringify({ status: "unavailable", model: null, reason: "Modelo no configurado." }), { status: 200 });
        }
        return new Response(
          JSON.stringify({
            provider: "unavailable",
            model: null,
            answer_kind: "tool_template",
            text: "La anomalía mensual sube unos 0.068 °C por año. No es un pronóstico.",
            limitations: ["El modelo no calcula la predicción."],
            actions: [{ type: "open-section", section: "tendencias" }],
            tools: [{ tool: "sst_trend", link: "/v1/analyses/d15-sst" }],
          }),
          { status: 200 },
        );
      }),
    );
    render(
      <AssistantDrawer
        open
        mode="real"
        replayIssue={null}
        replayRevealed={false}
        onClose={() => undefined}
        onOpenSection={() => undefined}
      />,
    );
    expect(await screen.findByText("Modelo no configurado.")).toBeTruthy();
    fireEvent.change(screen.getByRole("textbox", { name: "Pregunta al asistente" }), {
      target: { value: "¿Cuál es la tendencia?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
    expect(await screen.findByText(/0\.068/)).toBeTruthy();
    expect(screen.getByText("Sin modelo. Respuesta de herramientas.")).toBeTruthy();
    expect(screen.queryByText(/Qwen/)).toBeNull();
  });
});
