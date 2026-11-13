import { demoScenario } from "../demo/scenario";
import { timelineLabel } from "../demo/queries";
import type { ObservatoryState } from "./observatoryState";
import { Icon } from "./icons";

interface TopBarProps {
  state: ObservatoryState;
  onSection: (section: ObservatoryState["section"]) => void;
  onSearch: (text: string) => void;
  onTimeline: (days: number) => void;
  onPanel: (panel: "filters" | "inspector") => void;
}

const sections = [
  { id: "explorar", label: "Explorar" },
  { id: "tendencias", label: "Tendencias" },
  { id: "historico", label: "Histórico" },
] as const;

export function TopBar({ state, onSection, onSearch, onTimeline, onPanel }: TopBarProps) {
  const searchPending = state.searchText.trim().length > 0;
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
          onChange={(event) => onSearch(event.target.value)}
        />
        {searchPending ? (
          <p id="search-note" className="search-note" role="status">
            Sin consulta. La búsqueda se conecta en la fase 04.
          </p>
        ) : (
          <span id="search-note" className="sr-only">
            El campo todavía no consulta el catálogo.
          </span>
        )}
      </div>
      <label className="time-preset">
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
      </label>
      <p className="demo-badge">{demoScenario.badge}</p>
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
        <button type="button" className="icon-button" disabled title="La ayuda llega con el asistente">
          <Icon name="help" />
          <span className="sr-only">Ayuda, no disponible</span>
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
