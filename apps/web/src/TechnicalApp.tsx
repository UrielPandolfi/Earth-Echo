import { useEffect, useState } from "react";
import type { HealthResponse, ProviderReport } from "./domain/generated";
import { GlobeStage } from "./globe/GlobeStage";
import type { GlobeFactory } from "./globe/lifecycle";

const apiBase = import.meta.env.VITE_API_BASE ?? "/api";

interface TechnicalAppProps {
  createGlobe: GlobeFactory;
}

export function TechnicalApp({ createGlobe }: TechnicalAppProps) {
  const [session, setSession] = useState(0);
  const [globeCount, setGlobeCount] = useState(0);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [providers, setProviders] = useState<ProviderReport | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      try {
        const [healthResponse, providerResponse] = await Promise.all([
          fetch(`${apiBase}/health`, { signal: controller.signal }),
          fetch(`${apiBase}/providers`, { signal: controller.signal }),
        ]);
        if (!healthResponse.ok || !providerResponse.ok) {
          throw new Error("La API respondió con un error.");
        }
        setHealth((await healthResponse.json()) as HealthResponse);
        setProviders((await providerResponse.json()) as ProviderReport);
        setApiError(null);
      } catch (caught) {
        if (caught instanceof DOMException && caught.name === "AbortError") {
          return;
        }
        setHealth(null);
        setProviders(null);
        setApiError("La API no está disponible. El globo técnico no implica datos ambientales.");
      }
    }
    void load();
    return () => controller.abort();
  }, []);

  return (
    <main className="technical">
      <header>
        <p className="eyebrow">Prueba técnica</p>
        <h1>Earth Echo</h1>
        <p>
          Esta pantalla comprueba que el globo se monta y se destruye. El diseño del observatorio
          llega en la fase 02 y la imagen geográfica definitiva en la fase 03.
        </p>
      </header>
      <section className="status" aria-live="polite">
        <h2>Estado</h2>
        {apiError ? <p>{apiError}</p> : null}
        {health ? <p>Proceso de la API en ejecución. Chequeo: {health.checks.join(", ")}.</p> : null}
        {providers ? (
          <>
            <p>
              Proveedores: {providers.live_probe === "not_performed" ? "sin sondeo en vivo" : providers.live_probe}.
            </p>
            <ul>
              {providers.providers.map((provider) => (
                <li key={provider.source_id}>
                  {provider.source_id} {provider.name}: {provider.integration_status}. {provider.live_status}.
                </li>
              ))}
            </ul>
          </>
        ) : null}
      </section>
      <section>
        <div className="globe-toolbar">
          <button type="button" onClick={() => setSession((value) => value + 1)}>
            Desmontar y volver a montar
          </button>
          <p>Instancias activas: {globeCount}</p>
        </div>
        <GlobeStage key={session} createGlobe={createGlobe} onCount={setGlobeCount} />
        <p className="note">
          La base visual es Natural Earth II, incluida en CesiumJS, con terreno elipsoidal. No usa
          Cesium ion. La atribución queda en el crédito del visor.
        </p>
      </section>
    </main>
  );
}
