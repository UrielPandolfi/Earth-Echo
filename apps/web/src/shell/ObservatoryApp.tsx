import { useCallback, useEffect, useMemo, useReducer, useState } from "react";
import { recordsFor } from "../demo/catalog";
import {
  buildField,
  clusterDegreesFor,
  clusterRecords,
  countBy,
  relatedRecords,
  searchDemo,
  visibleRecords,
  type SearchHit,
} from "../demo/explore";
import { demoScenario } from "../demo/scenario";
import type { GeoExtent } from "../globe/geography";
import type { GlobeFactory, GlobeMarker } from "../globe/lifecycle";
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
  const [cameraHeight, setCameraHeight] = useState(13_200_000);
  const [frameRequest, setFrameRequest] = useState<GeoExtent | null>(null);
  const onCameraHeight = useCallback((height: number) => {
    setCameraHeight((current) => (Math.abs(current - height) < 250_000 ? current : height));
  }, []);

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

  const records = recordsFor(state.wide);
  const visible = useMemo(
    () =>
      visibleRecords({
        wide: state.wide,
        categoryIds: state.enabledCategoryIds,
        infoTypeIds: state.enabledInfoTypeIds,
        timelineDays: state.timelineDays,
        clusterDegrees: 0,
      }),
    [state.wide, state.enabledCategoryIds, state.enabledInfoTypeIds, state.timelineDays],
  );
  const grouped = useMemo(() => {
    const selectedVisible = visible.filter((record) => record.id === state.selectedId);
    const rest = visible.filter((record) => record.id !== state.selectedId);
    const groupedRest = clusterRecords(rest, clusterDegreesFor(cameraHeight, state.groupOnZoom));
    return { singles: [...selectedVisible, ...groupedRest.singles], clusters: groupedRest.clusters };
  }, [visible, cameraHeight, state.groupOnZoom, state.selectedId]);
  const markers = useMemo<GlobeMarker[]>(
    () => [
      ...grouped.singles.map((record) => ({
        id: record.id,
        title: record.title,
        longitude: record.longitude,
        latitude: record.latitude,
        priority: 1,
        note: record.unit,
        symbol: record.infoType,
      })),
      ...grouped.clusters.map((cluster) => ({
        id: cluster.id,
        title: `${cluster.count} señales`,
        longitude: cluster.longitude,
        latitude: cluster.latitude,
        priority: cluster.count,
        note: "grupo",
        symbol: "cluster" as const,
        count: cluster.count,
      })),
    ],
    [grouped],
  );
  const activeLayer = demoScenario.layers.find((layer) => layer.id === state.activeLayerId) ?? null;
  const field = useMemo(() => {
    if (!activeLayer || !state.enabledLayerIds.includes(activeLayer.id)) {
      return null;
    }
    if (activeLayer.id === "soil" || activeLayer.id === "temperature" || activeLayer.id === "precipitation") {
      return buildField(activeLayer.id);
    }
    return null;
  }, [activeLayer, state.enabledLayerIds]);
  const selected = records.find((record) => record.id === state.selectedId) ?? null;
  const outsideFilter = Boolean(selected && !visible.some((record) => record.id === selected.id));
  const results = searchDemo(state.searchText, records);
  const onPick = (hit: SearchHit) => {
    if (hit.kind === "signal") {
      dispatch({ type: "select", id: hit.id });
    }
    setFrameRequest({
      west: hit.west,
      south: hit.south,
      east: hit.east,
      north: hit.north,
      crossesAntimeridian: hit.crossesAntimeridian,
    });
  };

  return (
    <div className={`observatory ${state.filtersOpen ? "filters-open" : ""} ${state.inspectorOpen ? "inspector-open" : ""}`}>
      <TopBar
        state={state}
        onSection={(section) => dispatch({ type: "section", section })}
        results={results}
        onSearch={(text) => dispatch({ type: "search", text })}
        onPick={onPick}
        onTimeline={(days) => dispatch({ type: "timeline", days })}
        onPanel={(panel) => dispatch({ type: "panel", panel })}
      />
      <FilterPanel
        state={state}
        onToggleCategory={(id) => dispatch({ type: "toggle-category", id })}
        onToggleInfo={(id) => dispatch({ type: "toggle-info", id })}
        categoryCounts={countBy(visible, "categoryId")}
        infoCounts={countBy(visible, "infoType")}
        onToggleLayer={(id) => dispatch({ type: "toggle-layer", id })}
        onGroup={() => dispatch({ type: "group" })}
        onWide={(wide) => dispatch({ type: "wide", wide })}
      />
      <div className="center">
        <GlobeColumn
          state={state}
          createGlobe={createGlobe}
          catalogTotal={catalogTotal}
          catalogState={catalogState}
          signalCount={visible.length}
          groupCount={grouped.clusters.length}
          markers={markers}
          field={field}
          fieldCredit={activeLayer ? `${activeLayer.legendTitle} · ilustrativo` : "Campo ilustrativo DEMO"}
          frameRequest={frameRequest}
          onSelect={(id) => dispatch({ type: "select", id })}
          onCameraHeight={onCameraHeight}
        />
        <TimelineBar
          state={state}
          onTimeline={(days) => dispatch({ type: "timeline", days })}
          onPlay={() => dispatch({ type: "play" })}
        />
      </div>
      <Inspector
        state={state}
        signal={selected}
        outsideFilter={outsideFilter}
        related={selected ? relatedRecords(selected, records) : []}
        onTab={(tab) => dispatch({ type: "tab", tab })}
        onAnalysis={(open) => dispatch({ type: "analysis", open })}
        onSelect={(id) => dispatch({ type: "select", id })}
      />
    </div>
  );
}
