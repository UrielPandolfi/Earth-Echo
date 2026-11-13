import { useEffect, useState } from "react";

const apiBase = import.meta.env.VITE_API_BASE ?? "/api";

interface OutputState {
  kind: string;
  status: string;
  detail: string;
}

interface PhenomenonCapability {
  id: string;
  name: string;
  family: string;
  outputs: OutputState[];
}

const labels: Record<string, string> = {
  observation: "Observación",
  indicator: "Indicador",
  trend: "Tendencia",
  forecast: "Pronóstico",
  experimental_model: "Modelo propio",
};

export function CapabilitiesPanel() {
  const [rows, setRows] = useState<PhenomenonCapability[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      try {
        const response = await fetch(`${apiBase}/v1/capabilities`, { signal: controller.signal });
        if (!response.ok) {
          throw new Error("La matriz no respondió.");
        }
        const body = (await response.json()) as { phenomena?: PhenomenonCapability[] };
        if (!Array.isArray(body.phenomena)) {
          throw new Error("La matriz no tiene el contrato esperado.");
        }
        setRows(body.phenomena);
      } catch (caught) {
        if (caught instanceof DOMException && caught.name === "AbortError") {
          return;
        }
        setError(caught instanceof Error ? caught.message : "No se pudo leer la matriz.");
      }
    }
    void load();
    return () => controller.abort();
  }, []);

  return (
    <aside className="inspector" aria-label="Capacidades">
      <header className="inspector-head">
        <p className="kicker">Catálogo</p>
        <h2>Capacidades</h2>
        <p className="region">{rows ? `${rows.length} fenómenos` : "Cargando"}</p>
      </header>
      <div className="inspector-body">
        {error ? <p>{error}</p> : null}
        <p className="fine">Un fenómeno puede tener una observación y seguir sin pronóstico. Ningún estado verde inventa un predictor.</p>
        <ul className="capability-list">
          {(rows ?? []).map((item) => (
            <li key={item.id}>
              <strong>{item.id} {item.name}</strong>
              <small>{item.family}</small>
              <div>
                {item.outputs.map((output) => (
                  <span key={output.kind} className={`cap cap-${output.status}`} title={output.detail}>
                    {labels[output.kind] ?? output.kind}: {output.status}
                  </span>
                ))}
              </div>
            </li>
          ))}
        </ul>
      </div>
    </aside>
  );
}
