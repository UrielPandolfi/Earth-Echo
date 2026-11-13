export interface GlobeHandle {
  destroy: () => void;
}

export type GlobeFactory = (container: HTMLElement) => GlobeHandle;

const active = new Set<GlobeHandle>();

export function activeGlobeCount(): number {
  return active.size;
}

export function mountGlobe(container: HTMLElement, createGlobe: GlobeFactory): GlobeHandle {
  if (container.dataset.earthEchoGlobe === "live") {
    throw new Error("El contenedor ya tiene un globo activo.");
  }
  const handle = createGlobe(container);
  let closed = false;
  const mounted: GlobeHandle = {
    destroy() {
      if (closed) {
        return;
      }
      closed = true;
      try {
        handle.destroy();
      } finally {
        active.delete(handle);
        delete container.dataset.earthEchoGlobe;
      }
    },
  };
  container.dataset.earthEchoGlobe = "live";
  active.add(handle);
  return mounted;
}
