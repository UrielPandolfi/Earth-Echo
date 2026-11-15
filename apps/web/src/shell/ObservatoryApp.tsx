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
import { AssistantDrawer } from "./AssistantDrawer";
import { TopBar } from "./TopBar";
import { FilterPanel } from "./FilterPanel";
import { GlobeColumn } from "./GlobeColumn";
import { Inspector } from "./Inspector";
import { RealInspector } from "./RealInspector";
import { TrendPanel } from "./TrendPanel";
import { CapabilitiesPanel } from "./CapabilitiesPanel";
import { TimelineBar } from "./TimelineBar";
import { initialObservatoryState, reduceObservatory } from "./observatoryState";
import type { ProductList, ScientificProduct,RefreshStatus } from '../domain/generated';
import { ProductsPanel, ProductInspector,productKindLabel,productTimeLabel } from '../real/Products';
import { realMarkersForView } from '../globe/clustering';
import {useForecastExplorer} from '../forecasts/useForecastExplorer';
import {ForecastPanel,ForecastInspector,ForecastTime} from '../forecasts/ForecastPanels';
import {paintForecastField} from '../forecasts/field';

const apiBase = import.meta.env.VITE_API_BASE ?? "/api";

interface ObservatoryAppProps {
  createGlobe: GlobeFactory;
}

export function ObservatoryApp({ createGlobe }: ObservatoryAppProps) {
  const [state, dispatch] = useReducer(reduceObservatory, undefined, initialObservatoryState);
  const forecasting=state.dataMode==='real' && state.section==='pronosticos';
  const forecasts=useForecastExplorer(forecasting);
  const selectForecastPosition=useCallback((position:{longitude:number;latitude:number})=>{
    forecasts.selectPosition(position);
    if(!state.inspectorOpen)dispatch({type:'panel',panel:'inspector'});
  },[forecasts.selectPosition,state.inspectorOpen]);
  const [catalogTotal, setCatalogTotal] = useState<number | null>(null);
  const [catalogState, setCatalogState] = useState<"loading" | "ready" | "error">("loading");
  const [cameraHeight, setCameraHeight] = useState(13_200_000);
  const [frameRequest, setFrameRequest] = useState<GeoExtent | null>(null);
  const [realView, setRealView] = useState<RealSourceView | null>(null);
  const [realError, setRealError] = useState<string | null>(null);
  const [realField, setRealField] = useState<RealField | null>(null);
  const [products, setProducts] = useState<ProductList | null>(null);
  const [productKey, setProductKey] = useState('d15-sst-global');
  const [productError, setProductError] = useState<string | null>(null);
  const [productDetails, setProductDetails] = useState<ScientificProduct | null>(null);
  const [refreshStatus,setRefreshStatus]=useState<RefreshStatus|null>(null);
  const [layerError,setLayerError]=useState<string|null>(null);
  const activeProduct = productDetails?.id === productKey ? productDetails : products?.products.find(p => p.id === productKey);
  const [quakes, setQuakes] = useState<Array<{ id: string; longitude: number; latitude: number; magnitude: number; place: string; time: string }>>([]);
  const [kpText, setKpText] = useState<string | null>(null);
  const [assistantOpen, setAssistantOpen] = useState(false);
  const [replay, setReplay] = useState<{ issue: string | null; revealed: boolean }>({ issue: null, revealed: false });
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

  useEffect(() => {
    if (state.dataMode !== 'real') return;
    const controller = new AbortController();
    async function load() {
      try {
        const response = await fetch(`${apiBase}/v1/products?summaries=true`, { signal: controller.signal });
        if (!response.ok) throw new Error('No respondió la consulta de productos reales.');
        const body = await response.json() as ProductList;
        if (!Array.isArray(body.products) || body.data_mode !== 'real') throw new Error('Contrato de productos inválido.');
        setProducts(body); setProductError(null);
      } catch (e) { if (!controller.signal.aborted) setProductError(e instanceof Error ? e.message : 'No disponible'); }
      try {
        const response=await fetch(`${apiBase}/v1/operations/refresh`,{signal:controller.signal});
        if (!response.ok) throw new Error('Estado de actualización no disponible');
        const body=await response.json() as RefreshStatus;
        if (!body.jobs || typeof body.recent_scan!=='boolean') throw new Error('Estado inválido');
        setRefreshStatus(body);
      } catch { if (!controller.signal.aborted) setRefreshStatus(null); }
    }
    void load();
    const timer = window.setInterval(() => void load(), 60_000);
    return () => { controller.abort(); window.clearInterval(timer); };
  }, [state.dataMode]);

  useEffect(() => {
    if (state.dataMode !== 'real' || productKey === 'archive' || !products?.products.some(p=>p.id===productKey)) return;
    const controller = new AbortController();
    async function load() {
      try {
        const response = await fetch(`${apiBase}/v1/products/${productKey}`,{signal:controller.signal});
        if (!response.ok) throw new Error('No respondió el producto seleccionado.');
        const body = await response.json() as ScientificProduct;
        if (body.id !== productKey || body.data_mode !== 'real') throw new Error('Contrato de producto inválido.');
        setProductDetails(body); setProductError(null);
      } catch(e) { if (!controller.signal.aborted) setProductError(e instanceof Error ? e.message : 'Producto no disponible'); }
    }
    void load(); return ()=>controller.abort();
  },[state.dataMode,productKey,products]);

  useEffect(() => {
    if (state.dataMode !== "real") {
      return;
    }
    const controller = new AbortController();
    async function loadLayers() {
      try {
        const [quakeResponse, kpResponse] = await Promise.all([
          fetch(`${apiBase}/v1/layers/d21-events`, { signal: controller.signal }),
          fetch(`${apiBase}/v1/layers/d28-kp`, { signal: controller.signal }),
        ]);
        if (quakeResponse.ok) {
          const body = (await quakeResponse.json()) as { features?: typeof quakes };
          setQuakes(Array.isArray(body.features) ? body.features : []);
        }
        if (kpResponse.ok) {
          const body = (await kpResponse.json()) as { latest_kp?: number | null; latest_time?: string | null; note?: string };
          setKpText(
            body.latest_kp === null || body.latest_kp === undefined
              ? body.note ?? "Kp no disponible."
              : `Kp ${body.latest_kp} · ${body.latest_time ?? "sin hora"} · índice planetario, no un aviso local`,
          );
        }
        if (!quakeResponse.ok || !kpResponse.ok) throw new Error('Consulta de capas no disponible');
        setLayerError(null);
      } catch (caught) {
        if (caught instanceof DOMException && caught.name === "AbortError") {
          return;
        }
        setLayerError('No se pudieron actualizar sismos/Kp. Se conserva la última carga disponible.');
      }
    }
    void loadLayers();
    const timer = window.setInterval(() => void loadLayers(), 60_000);
    return () => { controller.abort(); window.clearInterval(timer); };
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
  const productHits: SearchHit[] = state.searchText.trim().length<2 ? [] : (products?.products ?? []).filter(p=>`${p.title} ${p.source_id} ${p.variable}`.toLocaleLowerCase('es').includes(state.searchText.toLocaleLowerCase('es'))).slice(0,6).map(p=>({kind:'signal',id:`product:${p.id}`,label:p.title,detail:`${p.source_id} · ${p.kind}`,longitude:0,latitude:0,west:-180,east:180,north:90,south:-90,crossesAntimeridian:false}));
  const results = state.dataMode === "real" ? [...productHits,...searchReal(state.searchText, realView)].slice(0,8) : demoResults;
  const onPick = (hit: SearchHit) => {
    if (state.dataMode==='real' && hit.id.startsWith('product:')) {
      setProductKey(hit.id.slice(8)); dispatch({type:'search',text:''}); dispatch({type:'real-select',id:null}); return;
    }
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
  const oafEvent=forecasts.oaf?.events?.find(item=>item.event_id===forecasts.selection.eventId) ?? forecasts.oaf?.events?.[0] ?? null;
  const forecastMarkers:GlobeMarker[]=forecasts.selection.mode==='d16' ? (forecasts.highlights?.areas ?? []).map((area,index)=>({
    id:area.id,title:`Zona ${index+1} · celda ${(area.probability_max*100).toFixed(1)} %`,longitude:area.representative.cell!.longitude,
    latitude:area.representative.cell!.latitude,priority:area.cell_count,note:'Área destacada del pronóstico; representante en una celda real',symbol:'forecast',
  })) : forecasts.selection.mode==='oaf' && oafEvent?.longitude!=null && oafEvent.latitude!=null ? [{
    id:oafEvent.event_id,title:oafEvent.magnitude==null ? oafEvent.event_id : `M${oafEvent.magnitude}`,longitude:oafEvent.longitude,latitude:oafEvent.latitude,priority:2,note:'Terremoto principal. No es el lugar de las réplicas.',symbol:'observation',
  }] : [];
  const shownMarkers: GlobeMarker[] = forecasting ? realMarkersForView(forecastMarkers,cameraHeight,state.groupOnZoom,null) :
    state.dataMode === "real"
      ? realMarkersForView([
          ...(productKey === 'archive' && realObservation?.spatial.geometry
            ? [
                {
                  id: realObservation.id,
                  title: "SST del Caribe",
                  longitude: realObservation.spatial.geometry.coordinates[0] ?? 0,
                  latitude: realObservation.spatial.geometry.coordinates[1] ?? 0,
                  priority: 2,
                  note: "°C",
                  symbol: "observation" as const,
                },
              ]
            : []),
          ...(activeProduct?.representation === 'points' || activeProduct?.representation === 'tracks' ? (activeProduct.samples ?? []).filter(s=>s.map_eligible!==false && (activeProduct.representation!=='tracks' || activeProduct.tracks?.some(t=>t.sample_ids[t.sample_ids.length-1]===s.id))).flatMap(s => s.longitude === null || s.longitude === undefined || s.latitude === null || s.latitude === undefined ? [] : [{
            id:`product-point:${s.id}`,title:s.attributes?.nombre ?? s.id,longitude:s.longitude,latitude:s.latitude,priority:1,note:s.quality,symbol:activeProduct.kind === 'static_context' ? 'context' as const : 'observation' as const,
          }]) : []),
          ...(state.realQuakes
            ? quakes.map((quake) => ({
                id: quake.id,
                title: `M${quake.magnitude.toFixed(1)}`,
                longitude: quake.longitude,
                latitude: quake.latitude,
                priority: 1,
                note: quake.place,
                symbol: "observation" as const,
              }))
            : []),
        ],cameraHeight,state.groupOnZoom,state.realSelectedId)
      : markers;
  const forecastField=useMemo(()=>forecasts.selection.mode!=='kp' && forecasts.field?.grid ? paintForecastField(forecasts.field.grid,forecasts.field.forecast?.result_type==='imported_probability') : null,[forecasts.field,forecasts.selection.mode]);
  const shownField = forecasting ? forecastField :
    state.dataMode === "real" ? (activeProduct?.grid ? paintSstField({...activeProduct.grid, observation_id: activeProduct.id, unit: activeProduct.unit}) : productKey === 'archive' && realField && realField.observation_id === realObservation?.id ? paintSstField(realField) : null) : field;
  const badge =
    state.dataMode === "real"
      ? activeProduct ? `REAL · ${activeProduct.source_id}` : realView?.status === "available"
        ? "REAL · archivo CoralTemp"
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
        onAssistant={() => setAssistantOpen((open) => !open)}
        assistantOpen={assistantOpen}
        badge={forecasting ? 'REAL · pronósticos externos' : badge}
      />
      {forecasting ? <ForecastPanel explorer={forecasts} products={products} onTechnical={()=>dispatch({type:'section',section:'explorar'})} onSelectPosition={selectForecastPosition}/> : state.dataMode === 'real' ? <ProductsPanel data={products} selected={productKey} activeProduct={activeProduct} refreshStatus={refreshStatus} onSelect={(key) => {setProductKey(key); dispatch({ type: 'real-select', id: null });}} onFocus={() => {
        const g = activeProduct?.grid;
        if (g) setFrameRequest({west:g.west, east:g.east, north:g.north, south:g.south, crossesAntimeridian:false});
        else if (activeProduct?.extent) {
          const e=activeProduct.extent;
          setFrameRequest({west:e.west,east:e.east,south:e.south,north:e.north,crossesAntimeridian:e.crosses_antimeridian});
        }
      }} quakesOn={state.realQuakes} quakeCount={quakes.length} onQuakes={() => dispatch({type:'toggle-quakes'})} kpText={kpText} error={productError ?? layerError} grouped={state.groupOnZoom} onGroup={()=>dispatch({type:'group'})}/> : <FilterPanel
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
        quakesOn={state.realQuakes}
        quakeCount={quakes.length}
        kpText={kpText}
        onToggleQuakes={() => dispatch({ type: "toggle-quakes" })}
      />}
      <div className="center">
        <GlobeColumn
          state={state}
          createGlobe={createGlobe}
          catalogTotal={catalogTotal}
          catalogState={catalogState}
          signalCount={forecasting ? shownMarkers.length+(shownField ? 1 : 0) : state.dataMode === "real" ? shownMarkers.length + (shownField ? 1 : 0) + (activeProduct?.regions?.length ?? 0) + (activeProduct?.tracks?.length ?? 0) : visible.length}
          groupCount={state.dataMode === "real" ? shownMarkers.filter(m=>m.symbol==='cluster').length : grouped.clusters.length}
          markers={shownMarkers}
          field={shownField}
          tracks={state.dataMode==='real' && !forecasting ? activeProduct?.tracks : undefined}
          regions={forecasting && forecasts.selection.mode==='enso' && forecasts.enso ? [forecasts.enso.region] : state.dataMode==='real' && !forecasting ? activeProduct?.regions : undefined}
          mapNotice={forecasting && forecasts.selection.mode==='enso' ? 'Región Niño 3.4: referencia del índice. Las probabilidades no se pintan en el mapa.' : forecasting && forecasts.selection.mode==='oaf' ? 'El punto es el terremoto principal. No hay zona de réplicas dibujada: el radio del modelo no trae unidad.' : null}
          planetaryKp={forecasting && forecasts.selection.mode==='kp' ? { forecast: forecasts.kp, error: forecasts.kpError } : null}
          onGeographicSelect={forecasting && forecasts.selection.mode!=='kp' ? selectForecastPosition : undefined}
          fieldSelection={forecasting && forecasts.point && forecasts.selection.mode!=='kp' ? {longitude:forecasts.point.requested_longitude,latitude:forecasts.point.requested_latitude,cell:forecasts.point.cell ?? null} : null}
          fieldCredit={
            forecasting ? forecasts.selection.mode==='enso' ? 'NOAA CPC · RONI · Niño 3.4' : forecasts.selection.mode==='oaf' ? 'USGS · pronóstico de réplicas' : `${forecasts.field?.forecast?.provider ?? 'Pronóstico externo'} · ${forecasts.field?.forecast?.variable ?? ''}` : state.dataMode === "real"
              ? activeProduct ? `${activeProduct.attribution} · ${activeProduct.variable}` : "NOAA Coral Reef Watch · CoralTemp v3.1 · SST"
              : activeLayer
                ? `${activeLayer.legendTitle} · ilustrativo`
                : "Campo ilustrativo DEMO"
          }
          emptyText={
            forecasting ? forecasts.selection.mode==='kp' ? 'Índice planetario: consultá la serie y las ventanas UTC en Detalle. Sin intensidades locales en el mapa.' : forecasts.error ?? 'Consultando un campo predictivo retenido; no se usa DEMO.' : state.dataMode === "real"
              ? activeProduct?.representation==='time_series'
                ? 'Serie regional disponible en el inspector; no hay pines ni una malla espacial para este producto.'
                : realView?.status === "available"
                ? undefined
                : realError
                  ? `${realError} El escenario DEMO no se usó como reemplazo.`
                  : realView?.status === "unavailable"
                    ? `${realView.reason} El escenario DEMO no se usó como reemplazo.`
                    : "Cargando el subconjunto real."
              : undefined
          }
          frameRequest={frameRequest}
          onSelect={(id) => {if(forecasting){const area=forecasts.highlights?.areas.find(a=>a.id===id);if(area)selectForecastPosition({longitude:area.representative.cell!.longitude,latitude:area.representative.cell!.latitude});}else dispatch(state.dataMode === "real" ? { type: "real-select", id } : { type: "select", id });}}
          countLabel={forecasting ? forecasts.selection.mode==='enso' ? `${forecasts.enso?.phases.length ?? '—'} trimestres ENSO · índice regional` : forecasts.selection.mode==='oaf' ? `${forecasts.oaf?.events.length ?? '—'} pronósticos de réplicas · no es el catálogo mundial` : forecasts.selection.mode==='kp' ? `${forecasts.kp?.forecast ? forecasts.kp.windows.filter(w=>w.temporal_state!=='expired').length : '—'} ventanas planetarias vigentes/futuras` : `${shownField ? 1 : '—'} campo en el período seleccionado · ${forecasts.selection.mode==='d16' ? forecasts.highlights?.total_areas ?? '—' : 'no aplica'} áreas destacadas` : state.dataMode === "real" ? `${products?.connected_sources ?? '—'} fuentes · ${products?.observation_records ?? '—'} observaciones · ${products?.calculated_indicator_products ?? '—'} indicadores calculados` : undefined}
          onCameraHeight={onCameraHeight}
          trendNote={
            state.section === "tendencias"
              ? state.dataMode === "real"
                ? "La tendencia de la SST real está en el panel derecho. El globo sigue en el recorte."
                : "El escenario demo no calcula una tendencia climática."
              : state.section === "historico"
                ? "La matriz de capacidades está en el panel derecho."
                : undefined
          }
        />
        {forecasting ? <ForecastTime explorer={forecasts}/> : state.dataMode === 'real' && activeProduct ? <div className="product-time" aria-label="Tiempo del producto real"><strong>{productKindLabel(activeProduct)}</strong><span>{activeProduct.observed_at || activeProduct.valid_from || activeProduct.issued_at ? `${productTimeLabel(activeProduct)} UTC` : 'Fechas y época en los registros; sin instante UTC proporcionado.'}{(activeProduct.observation_end ?? activeProduct.valid_to) ? ` → ${activeProduct.observation_end ?? activeProduct.valid_to} UTC` : ''}</span><span className="fine">Inicialización: {activeProduct.initialized_at ?? 'No aplica / no informada'}. Esta fecha pertenece al producto seleccionado.</span></div> : <TimelineBar
          state={state}
          onTimeline={(days) => dispatch({ type: "timeline", days })}
          onPlay={() => dispatch({ type: "play" })}
          realDates={realView?.observations.map((item) => item.observed.start.slice(0, 10)) ?? []}
          onRealIndex={(index) => dispatch({ type: "real-index", index })}
        />}
      </div>
        {forecasting ? <ForecastInspector explorer={forecasts} onFocus={()=>{if(forecasts.selection.mode==='oaf' && oafEvent?.longitude!=null && oafEvent.latitude!=null){setFrameRequest({west:oafEvent.longitude-2,east:oafEvent.longitude+2,south:oafEvent.latitude-2,north:oafEvent.latitude+2,crossesAntimeridian:false});return;} const e=forecasts.selection.mode==='enso' ? forecasts.enso?.region.extent : forecasts.point?.cell?.extent;if(e)setFrameRequest({west:e.west,east:e.east,north:e.north,south:e.south,crossesAntimeridian:e.crosses_antimeridian});}}/> : state.section === "historico" ? (
        <CapabilitiesPanel />
      ) : state.section === "tendencias" ? (
        <TrendPanel
          mode={state.dataMode}
          analysisOpen={state.analysisOpen}
          onAnalysis={(open) => dispatch({ type: "analysis", open })}
          onReplay={(issue, revealed) => setReplay({ issue, revealed })}
          onShowProduct={(key)=>{setProductKey(key);dispatch({type:'real-select',id:null});dispatch({type:'section',section:'explorar'});if(!state.inspectorOpen)dispatch({type:'panel',panel:'inspector'});}}
        />
      ) : state.dataMode === 'real' && activeProduct && !quakes.some(q => q.id === state.realSelectedId) ? <ProductInspector key={activeProduct.id} product={activeProduct} refreshStatus={refreshStatus} selectedId={state.realSelectedId?.replace('product-point:','').split(':area:')[0] ?? null} onSampleSelect={id=>dispatch({type:'real-select',id:`product-point:${id}`})} onRegionFocus={region=>{
        dispatch({type:'real-select',id:`product-point:${region.sample_id}`});
        setFrameRequest({west:region.extent.west,east:region.extent.east,south:region.extent.south,north:region.extent.north,crossesAntimeridian:region.extent.crosses_antimeridian});
      }} onTrackFocus={track=>{
        dispatch({type:'real-select',id:`product-point:${track.sample_ids[track.sample_ids.length-1]}`});
        setFrameRequest({west:track.extent.west,east:track.extent.east,south:track.extent.south,north:track.extent.north,crossesAntimeridian:track.extent.crosses_antimeridian});
      }}/> : state.dataMode === "real" ? (
        <RealInspector
          view={realView}
          error={realError}
          index={state.realIndex}
          analysisOpen={state.analysisOpen}
          onAnalysis={(open) => dispatch({ type: "analysis", open })}
          quake={quakes.find((item) => item.id === state.realSelectedId) ?? null}
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
      <AssistantDrawer
        open={assistantOpen}
        mode={state.dataMode}
        replayIssue={replay.issue}
        replayRevealed={replay.revealed}
        onClose={() => setAssistantOpen(false)}
        onOpenSection={(section) => dispatch({ type: "section", section })}
      />
    </div>
  );
}
