import type { ReactNode } from "react";

export type IconName =
  | "rain"
  | "heat"
  | "fire"
  | "ocean"
  | "land"
  | "space"
  | "leaf"
  | "search"
  | "bell"
  | "help"
  | "settings"
  | "user"
  | "play"
  | "pause"
  | "plus"
  | "minus"
  | "chevron"
  | "layers"
  | "home";

const paths: Record<IconName, ReactNode> = {
  rain: (
    <>
      <path d="M8 2.5v4" />
      <path d="M5 4.5c0 2 1.2 3 3 3s3-1 3-3" />
      <path d="M4.5 11.5c.8 1.4 1.4 2 2 2s1.2-.6 2-2 1.4-2 2-2 1.2.6 2 2" />
    </>
  ),
  heat: (
    <>
      <circle cx="8" cy="8" r="2.2" />
      <path d="M8 1.8v1.6M8 12.6v1.6M1.8 8h1.6M12.6 8h1.6M3.4 3.4l1.1 1.1M11.5 11.5l1.1 1.1M12.6 3.4l-1.1 1.1M4.5 11.5l-1.1 1.1" />
    </>
  ),
  fire: <path d="M8 1.8s2.8 2.4 2.8 4.6c0 1.2-.6 2-1.4 2 .8-2.2-1.4-3.2-1.4-3.2S6 7.2 6 9.2C6 11.6 7.2 14 9.2 14c-3.2 0-5-2.2-5-4.8C4.2 6.2 8 1.8 8 1.8z" />,
  ocean: <path d="M2 6.5c1.2 0 1.6-1.2 2.8-1.2S6.4 6.5 7.6 6.5 9.2 5.3 10.4 5.3 12 6.5 13.2 6.5M2 10.5c1.2 0 1.6-1.2 2.8-1.2s1.6 1.2 2.8 1.2 1.6-1.2 2.8-1.2 1.6 1.2 2.8 1.2" />,
  land: (
    <>
      <path d="M2.5 12.5 6.2 5.2 8.4 8.4 10.2 4.8 13.5 12.5z" />
      <path d="M2 13.2h12" />
    </>
  ),
  space: (
    <>
      <circle cx="8" cy="8" r="2" />
      <path d="M8 2.2v1.4M8 12.4v1.4M2.2 8h1.4M12.4 8h1.4" />
    </>
  ),
  leaf: <path d="M13 3.2S8.2 3.4 5.6 6.2 3.2 12.8 3.2 12.8 8.4 12.4 11 9.6 13 3.2 13 3.2zM5.2 10.8 10.2 5.8" />,
  search: (
    <>
      <circle cx="7" cy="7" r="3.4" />
      <path d="M9.6 9.6 13 13" />
    </>
  ),
  bell: <path d="M8 2.4a3.2 3.2 0 0 1 3.2 3.2v2.1l1.2 1.8H3.6l1.2-1.8V5.6A3.2 3.2 0 0 1 8 2.4zM6.6 12.2a1.4 1.4 0 0 0 2.8 0" />,
  help: (
    <>
      <circle cx="8" cy="8" r="5.2" />
      <path d="M6.4 6.4a1.6 1.6 0 1 1 2.3 1.4c-.5.3-.7.6-.7 1.1V9.4" />
      <path d="M8 11.4h.01" />
    </>
  ),
  settings: (
    <>
      <circle cx="8" cy="8" r="1.8" />
      <path d="M8 2.4v1.4M8 12.2v1.4M2.4 8h1.4M12.2 8h1.4M4 4l1 1M11 11l1 1M12 4l-1 1M5 11l-1 1" />
    </>
  ),
  user: (
    <>
      <circle cx="8" cy="6" r="2.1" />
      <path d="M3.8 13.2c.7-2.2 2.2-3.2 4.2-3.2s3.5 1 4.2 3.2" />
    </>
  ),
  play: <path d="M6 4.2v7.6l6-3.8z" />,
  pause: <path d="M6 4.2h1.6v7.6H6zM9.4 4.2H11v7.6H9.4z" />,
  plus: <path d="M8 3.5v9M3.5 8h9" />,
  minus: <path d="M3.5 8h9" />,
  chevron: <path d="M4.5 6.2 8 9.8l3.5-3.6" />,
  layers: <path d="M2.5 6.2 8 3.4l5.5 2.8L8 9zM3.2 9.2 8 12l4.8-2.8" />,
  home: (
    <>
      <path d="M2.8 7.6 8 3.2l5.2 4.4" />
      <path d="M4.4 7.2V13h7.2V7.2" />
    </>
  ),
};

export function Icon({ name }: { name: IconName }) {
  return (
    <svg className="icon" viewBox="0 0 16 16" aria-hidden="true">
      {paths[name]}
    </svg>
  );
}

export function SymbolMark({ kind }: { kind: "observation" | "risk" | "forecast" | "cluster" }) {
  return (
    <svg className={`symbol symbol-${kind}`} viewBox="0 0 16 16" aria-hidden="true">
      {kind === "observation" ? <circle cx="8" cy="8" r="4.2" /> : null}
      {kind === "risk" ? <path d="M8 2.4 13.4 13H2.6z" /> : null}
      {kind === "forecast" ? <path d="M8 2.2 13.2 8 8 13.8 2.8 8z" /> : null}
      {kind === "cluster" ? (
        <>
          <circle cx="6" cy="6.5" r="2.3" />
          <circle cx="10.2" cy="6.2" r="2" />
          <circle cx="8.2" cy="10.2" r="2.2" />
        </>
      ) : null}
    </svg>
  );
}
