import { HERO_ID } from "../demo/catalog";
import { demoScenario } from "../demo/scenario";

export type Section = "explorar" | "tendencias" | "historico";
export type InspectorTab = "resumen" | "datos" | "antecedentes";
export type DataMode = "demo" | "real";

export interface ObservatoryState {
  section: Section;
  enabledCategoryIds: string[];
  enabledInfoTypeIds: string[];
  enabledLayerIds: string[];
  activeLayerId: string | null;
  groupOnZoom: boolean;
  timelineDays: number;
  playing: boolean;
  searchText: string;
  dataMode: DataMode;
  realIndex: number;
  wide: boolean;
  selectedId: string | null;
  tab: InspectorTab;
  analysisOpen: boolean;
  filtersOpen: boolean;
  inspectorOpen: boolean;
}

export type ObservatoryAction =
  | { type: "section"; section: Section }
  | { type: "toggle-category"; id: string }
  | { type: "toggle-info"; id: string }
  | { type: "toggle-layer"; id: string }
  | { type: "group" }
  | { type: "timeline"; days: number }
  | { type: "play" }
  | { type: "tick" }
  | { type: "search"; text: string }
  | { type: "mode"; mode: DataMode }
  | { type: "real-index"; index: number }
  | { type: "real-tick"; count: number }
  | { type: "wide"; wide: boolean }
  | { type: "select"; id: string | null }
  | { type: "tab"; tab: InspectorTab }
  | { type: "analysis"; open: boolean }
  | { type: "panel"; panel: "filters" | "inspector" };

function toggle(ids: string[], id: string): string[] {
  return ids.includes(id) ? ids.filter((item) => item !== id) : [...ids, id];
}

export function initialObservatoryState(): ObservatoryState {
  return {
    section: "explorar",
    enabledCategoryIds: demoScenario.categories.map((item) => item.id),
    enabledInfoTypeIds: demoScenario.informationTypes.map((item) => item.id),
    enabledLayerIds: ["soil"],
    activeLayerId: "soil",
    groupOnZoom: true,
    timelineDays: 0,
    playing: false,
    searchText: "",
    dataMode: "demo",
    realIndex: 0,
    wide: false,
    selectedId: HERO_ID,
    tab: "resumen",
    analysisOpen: false,
    filtersOpen: false,
    inspectorOpen: false,
  };
}

export function reduceObservatory(state: ObservatoryState, action: ObservatoryAction): ObservatoryState {
  switch (action.type) {
    case "section":
      return { ...state, section: action.section, playing: false };
    case "toggle-category":
      return { ...state, enabledCategoryIds: toggle(state.enabledCategoryIds, action.id) };
    case "toggle-info":
      return { ...state, enabledInfoTypeIds: toggle(state.enabledInfoTypeIds, action.id) };
    case "toggle-layer": {
      const enabled = toggle(state.enabledLayerIds, action.id);
      const turningOn = enabled.includes(action.id);
      let activeLayerId = state.activeLayerId;
      if (turningOn) {
        activeLayerId = action.id;
      } else if (state.activeLayerId === action.id) {
        activeLayerId = enabled[0] ?? null;
      }
      return { ...state, enabledLayerIds: enabled, activeLayerId };
    }
    case "group":
      return { ...state, groupOnZoom: !state.groupOnZoom };
    case "timeline":
      return {
        ...state,
        timelineDays: Math.max(-30, Math.min(30, Math.round(action.days))),
        playing: false,
      };
    case "play":
      return { ...state, playing: !state.playing };
    case "tick": {
      if (!state.playing || state.timelineDays >= 30) {
        return { ...state, playing: false };
      }
      return { ...state, timelineDays: state.timelineDays + 1 };
    }
    case "search":
      return { ...state, searchText: action.text };
    case "mode":
      return { ...state, dataMode: action.mode, playing: false, searchText: "" };
    case "real-index":
      return { ...state, realIndex: Math.max(0, action.index), playing: false };
    case "real-tick":
      if (!state.playing || state.realIndex >= action.count - 1) {
        return { ...state, playing: false };
      }
      return { ...state, realIndex: state.realIndex + 1 };
    case "wide":
      return { ...state, wide: action.wide };
    case "select":
      return { ...state, selectedId: action.id, tab: "resumen" };
    case "tab":
      return { ...state, tab: action.tab };
    case "analysis":
      return { ...state, analysisOpen: action.open };
    case "panel":
      if (action.panel === "filters") {
        return { ...state, filtersOpen: !state.filtersOpen };
      }
      return { ...state, inspectorOpen: !state.inspectorOpen };
    default:
      return state;
  }
}
