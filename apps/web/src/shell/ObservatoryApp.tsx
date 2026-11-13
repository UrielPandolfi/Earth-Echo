import { useEffect, useReducer, useState } from "react";
import type { GlobeFactory } from "../globe/lifecycle";
import { TopBar } from "./TopBar";
import { FilterPanel } from "./FilterPanel";
import { GlobeColumn } from "./GlobeColumn";
import { Inspector } from "./Inspector";
import { TimelineBar } from "./TimelineBar";
import { initialObservatoryState, reduceObservatory } from "./observatoryState";

const apiBase = import.meta.env.VITE_API_BASE ?? "/api";

interface ObservatoryAppProps {
  createGlobe: GlobeFactory;
}

export function ObservatoryApp({ createGlobe }: ObservatoryAppProps) {
  const [state, dispatch] = useReducer(reduceObservatory, undefined, initialObservatoryState);
  const [catalogTotal, setCatalogTotal] = useState<number | null>(null);
  const [catalogState, setCatalogState] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    const controller = new AbortController();
    async function loadCatalogCount() {
      if (typeof fetch !== "function") {
        setCatalogState("error");
        return;
      }
      try {
        const response = await fetch(`${apiBase}/catalog/phenomena?limit=1`, { signal: controller.signal });
        if (!response.ok) {
          throw new Error("catálogo");
        }
        const body = (await response.json()) as { total?: number };
        if (typeof body.total !== "number") {
          throw new Error("total");
        }
        setCatalogTotal(body.total);
        setCatalogState("ready");
      } catch (caught) {
        if (caught instanceof DOMException && caught.name === "AbortError") {
          return;
        }
        setCatalogTotal(null);
        setCatalogState("error");
      }
    }
    void loadCatalogCount();
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!state.playing) {
      return;
    }
    const timer = window.setInterval(() => dispatch({ type: "tick" }), 700);
    return () => window.clearInterval(timer);
  }, [state.playing]);

  return (
    <div className={`observatory ${state.filtersOpen ? "filters-open" : ""} ${state.inspectorOpen ? "inspector-open" : ""}`}>
      <TopBar
        state={state}
        onSection={(section) => dispatch({ type: "section", section })}
        onSearch={(text) => dispatch({ type: "search", text })}
        onTimeline={(days) => dispatch({ type: "timeline", days })}
        onPanel={(panel) => dispatch({ type: "panel", panel })}
      />
      <FilterPanel
        state={state}
        onToggleCategory={(id) => dispatch({ type: "toggle-category", id })}
        onToggleInfo={(id) => dispatch({ type: "toggle-info", id })}
        onToggleLayer={(id) => dispatch({ type: "toggle-layer", id })}
        onGroup={() => dispatch({ type: "group" })}
      />
      <div className="center">
        <GlobeColumn state={state} createGlobe={createGlobe} catalogTotal={catalogTotal} catalogState={catalogState} />
        <TimelineBar
          state={state}
          onTimeline={(days) => dispatch({ type: "timeline", days })}
          onPlay={() => dispatch({ type: "play" })}
        />
      </div>
      <Inspector
        state={state}
        onTab={(tab) => dispatch({ type: "tab", tab })}
        onAnalysis={(open) => dispatch({ type: "analysis", open })}
      />
    </div>
  );
}
