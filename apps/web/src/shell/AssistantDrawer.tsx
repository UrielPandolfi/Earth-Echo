import { useEffect, useRef, useState } from "react";
import type { DataMode } from "./observatoryState";
import type { AssistantReply,AssistantAction } from '../domain/generated';

const apiBase = import.meta.env.VITE_API_BASE ?? "/api";

interface AssistantDrawerProps {
  open: boolean;
  mode: DataMode;
  replayIssue: string | null;
  replayRevealed: boolean;
  onClose: () => void;
  onOpenSection: (section: AssistantAction["section"]) => void;
}

export function AssistantDrawer({ open, mode, replayIssue, replayRevealed, onClose, onOpenSection }: AssistantDrawerProps) {
  const [question, setQuestion] = useState("");
  const [status, setStatus] = useState("El modelo no está configurado. Las respuestas salen de las herramientas.");
  const [reply, setReply] = useState<AssistantReply | null>(null);
  const [phase, setPhase] = useState<"idle" | "sending" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const request = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!open) {
      return;
    }
    const controller = new AbortController();
    async function loadStatus() {
      try {
        const response = await fetch(`${apiBase}/v1/assistant/status`, { signal: controller.signal });
        if (!response.ok) {
          throw new Error("estado");
        }
        const body = (await response.json()) as { status?: string; model?: string | null; reason?: string };
        setStatus(body.reason ?? "El modelo no está disponible.");
        if (body.status === "configured" && body.model) {
          setStatus(`Modelo configurado: ${body.model}. Solo puede parafrasear las herramientas.`);
        }
      } catch (caught) {
        if (caught instanceof DOMException && caught.name === "AbortError") {
          return;
        }
        setStatus("No se pudo consultar el estado del modelo. El mapa sigue disponible.");
      }
    }
    void loadStatus();
    return () => controller.abort();
  }, [open]);

  if (!open) {
    return null;
  }

  async function submit() {
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setPhase("sending");
    setError(null);
    try {
      const response = await fetch(`${apiBase}/v1/assistant/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          question,
          context: {
            data_mode: mode,
            replay_issue: replayIssue,
            replay_revealed: replayRevealed,
          },
        }),
      });
      if (!response.ok) {
        throw new Error("La pregunta no obtuvo una respuesta completa.");
      }
      setReply((await response.json()) as AssistantReply);
      setPhase("idle");
    } catch (caught) {
      if (caught instanceof DOMException && caught.name === "AbortError") {
        setPhase("idle");
        setError("Envío cancelado. No quedó una respuesta parcial.");
        return;
      }
      setPhase("error");
      setError(caught instanceof Error ? caught.message : "El asistente no respondió.");
    }
  }

  const providerLabel = reply
    ? reply.provider === "unavailable"
      ? "Sin modelo. Respuesta de herramientas."
      : reply.provider === 'not_used'
        ? 'Resumen científico de herramientas. El modelo de texto no intervino.'
      : reply.provider === "mock"
        ? "Proveedor de prueba, no es Qwen."
        : `Paráfrasis de ${reply.model ?? "un modelo configurado"}.`
    : null;

  return (
    <aside className="assistant-drawer" aria-label="Asistente">
      <header>
        <h2>Asistente</h2>
        <button type="button" onClick={onClose}>Cerrar</button>
      </header>
      <p className="fine">
        {mode === "real" ? "REAL" : "DEMO"}
        {replayIssue ? ` · replay ${replayIssue}${replayRevealed ? " revelado" : " sin revelar"}` : " · sin corte de replay"}
      </p>
      <p className="fine">{status}</p>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void submit();
        }}
      >
        <label>
          Pregunta
          <textarea
            value={question}
            maxLength={500}
            rows={3}
            aria-label="Pregunta al asistente"
            onChange={(event) => setQuestion(event.target.value)}
          />
        </label>
        <div className="inspector-foot">
          <button type="submit" disabled={phase === "sending" || question.trim().length === 0}>Enviar</button>
          <button
            type="button"
            disabled={phase !== "sending"}
            onClick={() => request.current?.abort()}
          >
            Cancelar
          </button>
        </div>
      </form>
      {error ? <p role="alert">{error}</p> : null}
      {reply ? (
        <div>
          <p>{providerLabel}</p>
          <p>{reply.text}</p>
          {reply.tools.flatMap((item,index)=>typeof item.link==='string' && item.link.startsWith('/v1/') ? [<p key={index}><a href={`${apiBase}${item.link}`} target="_blank" rel="noreferrer">Consultar datos y procedencia</a></p>] : [])}
          {reply.actions.map((action) => (
            <button key={action.section} type="button" onClick={() => onOpenSection(action.section)}>
              Abrir {action.section}
            </button>
          ))}
          <ul>
            {reply.limitations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </aside>
  );
}
