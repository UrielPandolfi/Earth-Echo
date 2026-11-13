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
import { isRealSourceView, paintSstField, searchReal, type RealField, type RealSourceView } from "../real/view";
import type { GeoExtent } from "../globe/geography";
import type { GlobeFactory, GlobeMarker } from "../globe/lifecycle";
import { TopBar } from "./TopBar";
import { FilterPanel } from "./FilterPanel";
import { GlobeColumn } from "./GlobeColumn";
import { Inspector } from "./Inspector";
import { RealInspector } from "./RealInspector";
import { TrendPanel } from "./TrendPanel";
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
  const [realView, setRealView] = useState<RealSourceView | null>(null);
  const [realError, setRealError] = useState<string | null>(null);
  const [realField, setRealField] = useState<RealField | null>(null);
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
    const timer = window.setInterval(
      () => dispatch(state.dataMode === "real" ? { type: "real-tick", count: realView?.observations.length ?? 0 } : { type: "tick" }),
      700,
    );
    return () => window.clearInterval(timer);
  }, [state.playing, state.dataMode, realView?.observations.length]);

  useEffect(() => {
    if (state.dataMode !== "real") {
      return;
    }
    const controller = new AbortController();
    setRealError(null);
    async function loadReal() {
      try {
        const response = await fetch(`${apiBase}/v1/sources/D15`, { signal: controller.signal });
        if (!response.ok) {
          throw new Error("La consulta real no respondió.");
        }
        const body: unknown = await response.json();
        if (!isRealSourceView(body)) {
          throw new Error("La respuesta real no tiene el contrato esperado.");
        }
        setRealView(body);
        if (body.status === "available" && body.coverage) {
          setFrameRequest({
            west: body.coverage.west,
            south: body.coverage.south,
            east: body.coverage.east,
            north: body.coverage.north,
            crossesAntimeridian: Boolean(body.coverage.crosses_antimeridian),
          });
        }
      } catch (caught) {
        if (caught instanceof DOMException && caught.name === "AbortError") {
          return;
        }
        setRealView(null);
        setRealError(caught instanceof Error ? caught.message : "No se pudo leer el subconjunto real.");
      }
    }
    void loadReal();
    return () => controller.abort();
  }, [state.dataMode]);

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
  const realObservation =
    realView?.status === "available"
      ? realView.observations[Math.min(state.realIndex, Math.max(realView.observations.length - 1, 0))]
      : undefined;

  useEffect(() => {
    if (state.dataMode !== "real" || !realObservation) {
      return;
    }
    const controller = new AbortController();
    const observationId = realObservation.id;
    async function loadField() {
      try {
        const response = await fetch(`${apiBase}/v1/sources/D15/observations/${observationId}/field`, {
          signal: controller.signal,
        });
        if (!response.ok) {
          throw new Error("malla");
        }
        setRealField((await response.json()) as RealField);
      } catch (caught) {
        if (caught instanceof DOMException && caught.name === "AbortError") {
          return;
        }
        setRealField(null);
      }
    }
    void loadField();
    return () => controller.abort();
  }, [state.dataMode, realObservation?.id]);

  const demoResults = searchDemo(state.searchText, records);
  const results = state.dataMode === "real" ? searchReal(state.searchText, realView) : demoResults;
  const onPick = (hit: SearchHit) => {
    if (state.dataMode === "real") {
      if (hit.kind === "signal") {
        dispatch({ type: "real-index", index: Number(hit.id) });
      }
    } else if (hit.kind === "signal") {
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
  const shownMarkers: GlobeMarker[] =
    state.dataMode === "real"
      ? realObservation?.spatial.geometry
        ? [
            {
              id: realObservation.id,
              title: "SST del Caribe",
              longitude: realObservation.spatial.geometry.coordinates[0] ?? 0,
              latitude: realObservation.spatial.geometry.coordinates[1] ?? 0,
              priority: 1,
              note: "°C",
              symbol: "observation",
            },
          ]
        : []
      : markers;
  const shownField =
    state.dataMode === "real" ? (realField && realField.observation_id === realObservation?.id ? paintSstField(realField) : null) : field;
  const badge =
    state.dataMode === "real"
      ? realView?.status === "available"
        ? "REAL · CoralTemp v3.1"
        : "REAL · no disponible"
      : demoScenario.badge;

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
        onMode={(mode) => dispatch({ type: "mode", mode })}
        badge={badge}
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
        realView={realView}
        realError={realError}
      />
      <div className="center">
        <GlobeColumn
          state={state}
          createGlobe={createGlobe}
          catalogTotal={catalogTotal}
          catalogState={catalogState}
          signalCount={state.dataMode === "real" ? shownMarkers.length : visible.length}
          groupCount={state.dataMode === "real" ? 0 : grouped.clusters.length}
          markers={shownMarkers}
          field={shownField}
          fieldCredit={
            state.dataMode === "real"
              ? "NOAA Coral Reef Watch · CoralTemp v3.1 · SST"
              : activeLayer
                ? `${activeLayer.legendTitle} · ilustrativo`
                : "Campo ilustrativo DEMO"
          }
          emptyText={
            state.dataMode === "real"
              ? realView?.status === "available"
                ? undefined
                : realError
                  ? `${realError} El escenario DEMO no se usó como reemplazo.`
                  : realView?.status === "unavailable"
                    ? `${realView.reason} El escenario DEMO no se usó como reemplazo.`
                    : "Cargando el subconjunto real."
              : undefined
          }
          frameRequest={frameRequest}
          onSelect={(id) => dispatch({ type: "select", id })}
          onCameraHeight={onCameraHeight}
          trendNote={
            state.section !== "tendencias"
              ? undefined
              : state.dataMode === "real"
                ? "La tendencia de la SST real está en el panel derecho. El globo sigue en el recorte."
                : "El escenario demo no calcula una tendencia climática."
          }
        />
        <TimelineBar
          state={state}
          onTimeline={(days) => dispatch({ type: "timeline", days })}
          onPlay={() => dispatch({ type: "play" })}
          realDates={realView?.observations.map((item) => item.observed.start.slice(0, 10)) ?? []}
          onRealIndex={(index) => dispatch({ type: "real-index", index })}
        />
      </div>
      {state.section === "tendencias" ? (
        <TrendPanel
          mode={state.dataMode}
          analysisOpen={state.analysisOpen}
          onAnalysis={(open) => dispatch({ type: "analysis", open })}
        />
      ) : state.dataMode === "real" ? (
        <RealInspector
          view={realView}
          error={realError}
          index={state.realIndex}
          analysisOpen={state.analysisOpen}
          onAnalysis={(open) => dispatch({ type: "analysis", open })}
        />
      ) : (
        <Inspector
          state={state}
          signal={selected}
          outsideFilter={outsideFilter}
          related={selected ? relatedRecords(selected, records) : []}
          onTab={(tab) => dispatch({ type: "tab", tab })}
          onAnalysis={(open) => dispatch({ type: "analysis", open })}
          onSelect={(id) => dispatch({ type: "select", id })}
        />
      )}
    </div>
  );
}
