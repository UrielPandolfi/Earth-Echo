import { demoScenario } from "../demo/scenario";
import { timelineKind, timelineLabel } from "../demo/queries";
import type { ObservatoryState } from "./observatoryState";
import { Icon } from "./icons";

interface TimelineBarProps {
  state: ObservatoryState;
  onTimeline: (days: number) => void;
  onPlay: () => void;
}

export function TimelineBar({ state, onTimeline, onPlay }: TimelineBarProps) {
  const kind = timelineKind(state.timelineDays);

  return (
    <div className="timeline" aria-label="Línea de tiempo del escenario demo">
      <button type="button" className="play" onClick={onPlay} aria-pressed={state.playing}>
        <Icon name={state.playing ? "pause" : "play"} />
        <span className="sr-only">{state.playing ? "Pausar" : "Reproducir"} el escenario</span>
      </button>
      <div className="modes" role="group" aria-label="Tramo temporal">
        <button type="button" className={kind === "observado" ? "is-current" : undefined} onClick={() => onTimeline(Math.min(0, state.timelineDays))}>
          Observado
        </button>
        <button type="button" className={kind === "pronostico" ? "is-current" : undefined} onClick={() => onTimeline(Math.max(7, state.timelineDays))}>
          Pronóstico
        </button>
        <button type="button" onClick={() => onTimeline(-30)}>
          Replay
        </button>
      </div>
      <div className="track-wrap">
        <div className="track" aria-hidden="true">
          <span className="track-past" />
          <span className="track-future" />
        </div>
        <input
          type="range"
          min={-30}
          max={30}
          step={1}
          value={state.timelineDays}
          aria-valuetext={timelineLabel(state.timelineDays)}
          aria-label="Día del escenario respecto de ahora"
          onChange={(event) => onTimeline(Number(event.target.value))}
        />
        <div className="ticks">
          {demoScenario.timelineStops.map((day) => (
            <button key={day} type="button" className={state.timelineDays === day ? "is-current" : undefined} onClick={() => onTimeline(day)}>
              {timelineLabel(day)}
            </button>
          ))}
        </div>
      </div>
      <p className="timeline-note">Cada fuente conserva su ficha de actualización.</p>
    </div>
  );
}
