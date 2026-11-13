import { describe, expect, it } from "vitest";
import { activeGlobeCount, mountGlobe, type GlobeFactory, type GlobeHandle } from "./lifecycle";

function trackFactory(): { factory: GlobeFactory; created: GlobeHandle[] } {
  const created: GlobeHandle[] = [];
  const factory: GlobeFactory = () => {
    let destroyed = false;
    const handle: GlobeHandle = {
      destroy() {
        destroyed = true;
      },
    };
    Object.defineProperty(handle, "destroyed", { get: () => destroyed });
    created.push(handle);
    return handle;
  };
  return { factory, created };
}

function liveCount(created: Array<GlobeHandle & { destroyed?: boolean }>): number {
  return created.filter((handle) => handle.destroyed !== true).length;
}

describe("ciclo de vida del globo", () => {
  it("no crea una segunda instancia si el contenedor sigue activo", () => {
    const { factory, created } = trackFactory();
    const container = document.createElement("div");
    const first = mountGlobe(container, factory);
    expect(activeGlobeCount()).toBe(1);
    expect(() => mountGlobe(container, factory)).toThrow(/ya tiene un globo activo/);
    expect(created).toHaveLength(1);
    expect(activeGlobeCount()).toBe(1);
    first.destroy();
    expect(activeGlobeCount()).toBe(0);
    const second = mountGlobe(container, factory);
    expect(activeGlobeCount()).toBe(1);
    expect(liveCount(created)).toBe(1);
    second.destroy();
    expect(activeGlobeCount()).toBe(0);
  });
});
