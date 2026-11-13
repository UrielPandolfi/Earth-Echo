import { useState } from "react";
import { demoScenario } from "../demo/scenario";
import { formatCount } from "../demo/queries";
import type { ObservatoryState } from "./observatoryState";
import { Icon, SymbolMark } from "./icons";

interface FilterPanelProps {
  state: ObservatoryState;
  onToggleCategory: (id: string) => void;
  onToggleInfo: (id: string) => void;
  onToggleLayer: (id: string) => void;
  onGroup: () => void;
}

export function FilterPanel({ state, onToggleCategory, onToggleInfo, onToggleLayer, onGroup }: FilterPanelProps) {
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
                <b>{formatCount(category.displayCount)}</b>
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
                <b>{formatCount(item.displayCount)}</b>
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
            <div className="legend-bar" />
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
            ? "Preferencia activa. El globo aún no agrupa: fase 04."
            : "Agrupación desactivada en este escenario."}
        </p>
      </div>
    </aside>
  );
}
