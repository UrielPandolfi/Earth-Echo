import type { GlobeMarker } from './lifecycle';

/** Presentation-only grouping: dateline sides and symbol classes never share a bucket. */
export function groupMarkers(points: GlobeMarker[], degrees: number, selected: string | null): GlobeMarker[] {
  if (degrees <= 0) return points;
  const buckets = new Map<string, GlobeMarker[]>();
  const singles: GlobeMarker[] = [];
  for (const p of points) {
    if (p.id === selected) { singles.push(p); continue; }
    const key = `${p.symbol}:${Math.floor((p.longitude + 180) / degrees)}:${Math.floor((p.latitude + 90) / degrees)}`;
    const items = buckets.get(key) ?? []; items.push(p); buckets.set(key,items);
  }
  for (const [key,items] of buckets) {
    if (items.length === 1) { singles.push(items[0]); continue; }
    singles.push({id:`cluster:real:${key}`,title:`${items.length} registros`,longitude:items.reduce((s,p)=>s+p.longitude,0)/items.length,
      latitude:items.reduce((s,p)=>s+p.latitude,0)/items.length,priority:items.length,note:'Agrupación visual de registros reales',symbol:'cluster',count:items.length});
  }
  return singles;
}

/** Bound GPU symbols, preserving every record in counts and the selected point. */
export function realMarkersForView(points: GlobeMarker[], height: number, enabled: boolean, selected: string | null): GlobeMarker[] {
  const budget=1500;
  let degrees=enabled ? height>22_000_000 ? 12 : height>8_000_000 ? 8 : height>2_000_000 ? 3 : 0 : 0;
  if(points.length>budget) degrees=Math.max(degrees,.05);
  let shown=groupMarkers(points,degrees,selected);
  while(shown.length>budget && degrees>0 && degrees<180){
    degrees*=2;
    shown=groupMarkers(points,degrees,selected);
  }
  return shown;
}
