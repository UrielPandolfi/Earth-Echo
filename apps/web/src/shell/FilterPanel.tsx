import { useState } from "react";
import { demoScenario } from "../demo/scenario";
import { formatCount } from "../demo/queries";
import type { RealSourceView } from "../real/view";
import { freshnessLabel } from "../real/view";
import type { ObservatoryState } from "./observatoryState";
import { Icon, SymbolMark } from "./icons";

interface FilterPanelProps {
  state: ObservatoryState;
  categoryCounts: Record<string, number>;
  infoCounts: Record<string, number>;
  onToggleCategory: (id: string) => void;
  onToggleInfo: (id: string) => void;
  onToggleLayer: (id: string) => void;
  onGroup: () => void;
  onWide: (wide: boolean) => void;
  realView: RealSourceView | null;
  realError: string | null;
}

export function FilterPanel({ state, categoryCounts, infoCounts, onToggleCategory, onToggleInfo, onToggleLayer, onGroup, onWide, realView, realError }: FilterPanelProps) {
  if (state.dataMode === "real") {
    return (
      <aside className="sidebar" aria-label="Consulta real">
        <div className="sidebar-head">
          <h2>Consulta real</h2>
        </div>
        {realError ? <p className="hint">{realError} El escenario DEMO no se usó como reemplazo.</p> : null}
        {realView?.status === "unavailable" ? <p className="hint">{realView.reason} El escenario DEMO no se usó como reemplazo.</p> : null}
        {realView?.status === "available" ? (
          <div className="legend">
            <p>
              <strong>SST · CoralTemp {realView.product_version}</strong>
              <span>Temperatura superficial del mar, no anomalía ni blanqueamiento.</span>
            </p>
            <p className="hint">Cadencia {realView.cadence}. {realView.freshness ? freshnessLabel(realView.freshness) : ""}</p>
            <p className="hint">Última observación {realView.latest_observation?.replace(/\.\d+/, "")}. Última ingestión {realView.latest_ingest?.replace(/\.\d+/, "")}.</p>
            <p className="hint">IMERG (D01) sigue bloqueado: hacen falta EARTHDATA_USERNAME y EARTHDATA_PASSWORD en .env.</p>
          </div>
        ) : null}
      </aside>
    );
  }
  const [layersOpen, setLayersOpen] = useState(false);
  const activeLayer = demoScenario.layers.find((layer) => layer.id === state.activeLayerId) ?? null;
  const activeCategories = demoScenario.categories.filter((item) => state.enabledCategoryIds.includes(item.id));

  return (
    <aside className="sidebar" aria-label="Capas y filtros">
      <div className="sidebar-head">
        <h2>Capas y filtros</h2>
        <button type="button" className="menu-button" aria-expanded={layersOpen} onClick={() => setLayersOpen((open) => !open)}>
          <span>Capas activas</span>
          <Icon name="chevron" />
        </button>
        {layersOpen ? (
          <ul className="menu-list">
            {activeCategories.map((item) => (
              <li key={item.id}>{item.label}</li>
            ))}
            {demoScenario.layers
              .filter((layer) => state.enabledLayerIds.includes(layer.id))
              .map((layer) => (
                <li key={layer.id}>{layer.label}</li>
              ))}
            {activeCategories.length + state.enabledLayerIds.length === 0 ? <li>Ninguna capa activa</li> : null}
          </ul>
        ) : null}
      </div>
      <div className="sidebar-body">
        <ul className="rows">
          {demoScenario.categories.map((category) => (
            <li key={category.id}>
              <label className="row">
                <input
                  type="checkbox"
                  checked={state.enabledCategoryIds.includes(category.id)}
                  onChange={() => onToggleCategory(category.id)}
                />
                <Icon name={category.icon} />
                <span>{category.label}</span>
                <b>{formatCount(categoryCounts[category.id] ?? 0)}</b>
              </label>
            </li>
          ))}
        </ul>
        <h3>Tipo de información</h3>
        <ul className="rows">
          {demoScenario.informationTypes.map((item) => (
            <li key={item.id}>
              <label className="row">
                <input
                  type="checkbox"
                  checked={state.enabledInfoTypeIds.includes(item.id)}
                  onChange={() => onToggleInfo(item.id)}
                />
                <SymbolMark kind={item.symbol} />
                <span>{item.label}</span>
                <b>{formatCount(infoCounts[item.id] ?? 0)}</b>
              </label>
            </li>
          ))}
        </ul>
        <h3>Capas ambientales</h3>
        <ul className="rows">
          {demoScenario.layers.map((layer) => (
            <li key={layer.id}>
              <label className="row">
                <input
                  type="checkbox"
                  checked={state.enabledLayerIds.includes(layer.id)}
                  onChange={() => onToggleLayer(layer.id)}
                />
                <span>{layer.label}</span>
              </label>
            </li>
          ))}
        </ul>
        {activeLayer ? (
          <figure className="legend">
            <figcaption>
              <strong>{activeLayer.legendTitle}</strong>
              <span>{activeLayer.legendCaption}</span>
            </figcaption>
            <div className={`legend-bar legend-${activeLayer.id}`} />
            <p className="hint">Se dibuja una capa por vez para no mezclar unidades. Lo transparente no tiene dato.</p>
            <div className="legend-scale">
              <span>{activeLayer.scaleMin}</span>
              <span>0</span>
              <span>{activeLayer.scaleMax}</span>
            </div>
          </figure>
        ) : (
          <p className="empty-note">Ninguna capa ambiental activa. La leyenda queda vacía.</p>
        )}
        <label className="row group-row">
          <input type="checkbox" checked={state.groupOnZoom} onChange={onGroup} />
          <span>Agrupar señales al alejar</span>
        </label>
        <p className="hint">
          {state.groupOnZoom
            ? "Al alejar, las señales cercanas se agrupan. El número es la cantidad de registros."
            : "Agrupación desactivada: cada registro se dibuja por separado."}
        </p>
        <button type="button" className="wide-toggle" aria-pressed={state.wide} onClick={() => onWide(!state.wide)}>
          {state.wide ? "Volver al escenario de apertura" : "Conjunto amplio de rendimiento"}
        </button>
      </div>
    </aside>
  );
}
