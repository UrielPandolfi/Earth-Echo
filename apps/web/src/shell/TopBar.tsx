import { useState } from "react";
import { demoScenario } from "../demo/scenario";
import { timelineLabel } from "../demo/queries";
import type { SearchHit } from "../demo/explore";
import type { DataMode, ObservatoryState } from "./observatoryState";
import { Icon } from "./icons";

interface TopBarProps {
  state: ObservatoryState;
  results: SearchHit[];
  onSection: (section: ObservatoryState["section"]) => void;
  onSearch: (text: string) => void;
  onPick: (hit: SearchHit) => void;
  onTimeline: (days: number) => void;
  onPanel: (panel: "filters" | "inspector") => void;
  onMode: (mode: DataMode) => void;
  onAssistant: () => void;
  assistantOpen: boolean;
  badge: string;
}

const sections = [
  { id: "explorar", label: "Explorar" },
  { id: "tendencias", label: "Tendencias" },
  { id: "historico", label: "Histórico" },
] as const;

export function TopBar({ state, results, onSection, onSearch, onPick, onTimeline, onPanel, onMode, onAssistant, assistantOpen, badge }: TopBarProps) {
  const [activeIndex, setActiveIndex] = useState(0);
  const searchPending = state.searchText.trim().length >= 2;
  return (
    <header className="topbar">
      <div className="brand">
        <span className="brand-mark" aria-hidden="true" />
        <span className="brand-name">earth echo</span>
      </div>
      <nav className="nav" aria-label="Secciones">
        {sections.map((section) => (
          <button
            key={section.id}
            type="button"
            className={state.section === section.id ? "nav-item is-current" : "nav-item"}
            aria-current={state.section === section.id ? "page" : undefined}
            onClick={() => onSection(section.id)}
          >
            {section.label}
          </button>
        ))}
      </nav>
      <div className="search">
        <Icon name="search" />
        <input
          type="search"
          value={state.searchText}
          placeholder="Buscar región o fenómeno"
          aria-label="Buscar región o fenómeno"
          aria-describedby="search-note"
          aria-controls="search-results"
          aria-activedescendant={results[activeIndex] ? `search-hit-${activeIndex}` : undefined}
          onChange={(event) => {
            setActiveIndex(0);
            onSearch(event.target.value);
          }}
          onKeyDown={(event) => {
            if (event.key === "ArrowDown") {
              event.preventDefault();
              setActiveIndex((index) => Math.min(index + 1, Math.max(results.length - 1, 0)));
            } else if (event.key === "ArrowUp") {
              event.preventDefault();
              setActiveIndex((index) => Math.max(index - 1, 0));
            } else if (event.key === "Enter" && results[activeIndex]) {
              event.preventDefault();
              onPick(results[activeIndex]);
            }
          }}
        />
        {searchPending ? (
          <div id="search-note" className="search-note">
            {results.length === 0 ? (
              <p role="status">{state.dataMode==='real' ? 'Sin coincidencias entre los productos reales.' : 'Sin coincidencias en el escenario demo.'}</p>
            ) : (
              <ul id="search-results" role="listbox" aria-label={state.dataMode === "real" ? "Resultados del subconjunto real" : "Resultados del escenario demo"}>
                {results.map((hit, index) => (
                  <li key={`${hit.kind}-${hit.id}`}>
                    <button
                      id={`search-hit-${index}`}
                      type="button"
                      role="option"
                      aria-selected={index === activeIndex}
                      onMouseDown={(event) => event.preventDefault()}
                      onClick={() => onPick(hit)}
                    >
                      <strong>{hit.label}</strong>
                      <small>{hit.kind === "region" ? "Región" : "Señal"} · {hit.detail}</small>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ) : (
          <span id="search-note" className="sr-only">
            Escribí al menos dos letras para buscar {state.dataMode==='real' ? 'productos reales, fuentes o el archivo del Caribe.' : 'en el escenario demo.'}
          </span>
        )}
      </div>
      {state.dataMode === "demo" ? <label className="time-preset">
        <span>Últimos datos</span>
        <select
          value={state.timelineDays}
          aria-label="Momento del escenario demo"
          onChange={(event) => onTimeline(Number(event.target.value))}
        >
          {demoScenario.timelineStops.map((day) => (
            <option key={day} value={day}>
              {timelineLabel(day)}
            </option>
          ))}
        </select>
      </label> : null}
      <div className="mode-switch" role="group" aria-label="Modo de datos">
        <button type="button" aria-pressed={state.dataMode === "demo"} onClick={() => onMode("demo")}>
          DEMO
        </button>
        <button type="button" aria-pressed={state.dataMode === "real"} onClick={() => onMode("real")}>
          REAL
        </button>
      </div>
      <p className="demo-badge">{badge}</p>
      <div className="top-tools" aria-label="Herramientas de la barra">
        <button type="button" className="icon-button panel-toggle" onClick={() => onPanel("filters")}>
          Filtros
        </button>
        <button type="button" className="icon-button panel-toggle" onClick={() => onPanel("inspector")}>
          Detalle
        </button>
        <button type="button" className="icon-button" disabled title="Sin avisos en esta fase">
          <Icon name="bell" />
          <span className="sr-only">Avisos, no disponibles</span>
        </button>
        <button type="button" className="icon-button" aria-expanded={assistantOpen} title="Asistente" onClick={onAssistant}>
          <Icon name="help" />
          <span className="sr-only">Asistente</span>
        </button>
        <button type="button" className="icon-button" disabled title="No hay ajustes de cuenta">
          <Icon name="settings" />
          <span className="sr-only">Ajustes, no disponibles</span>
        </button>
        <button type="button" className="icon-button" disabled title="No hay sesión de usuario">
          <Icon name="user" />
          <span className="sr-only">Usuario, no disponible</span>
        </button>
      </div>
    </header>
  );
}
