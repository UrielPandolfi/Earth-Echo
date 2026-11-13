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
