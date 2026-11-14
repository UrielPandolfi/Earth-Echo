import {expect,it} from 'vitest';
import {realMarkersForView} from './clustering';
import type {GlobeMarker} from './lifecycle';

it('bounds a dense point product while preserving counts, selected record and dateline sides',()=>{
  const points:GlobeMarker[]=Array.from({length:20_000},(_,i)=>({id:`record-${i}`,title:'test input',longitude:-179.9+(i%200)*1.8,latitude:-49+(i%100),priority:1,note:'performance input only',symbol:'observation'}));
  const selected=points[0].id;
  for(const enabled of [true,false]){
    const shown=realMarkersForView(points,13_200_000,enabled,selected);
    expect(shown.length).toBeLessThanOrEqual(1500);
    expect(shown.reduce((n,p)=>n+(p.count ?? 1),0)).toBe(points.length);
    expect(shown.find(p=>p.id===selected)).toBe(points[0]);
    expect(shown.some(p=>p.longitude< -170)).toBe(true);
    expect(shown.some(p=>p.longitude>170)).toBe(true);
  }
});
