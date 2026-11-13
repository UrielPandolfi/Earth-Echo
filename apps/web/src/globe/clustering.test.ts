import { expect,test } from 'vitest';
import { groupMarkers } from './clustering';
import type { GlobeMarker } from './lifecycle';
const point=(id:string,longitude:number,symbol:GlobeMarker['symbol']='observation'):GlobeMarker=>({id,longitude,latitude:0,title:id,priority:1,note:'real fixture',symbol});
test('real grouping preserves counts, dateline sides and selected overlapping point',()=>{
  const points=[point('a',179.2),point('b',-179.2),point('c',1),point('d',1),point('e',1,'context')];
  const grouped=groupMarkers(points,10,'c');
  expect(grouped.reduce((sum,p)=>sum+(p.count??1),0)).toBe(5);
  expect(grouped.find(p=>p.id==='c')).toBeDefined();
  expect(grouped.find(p=>p.id==='e')).toBeDefined();
  expect(grouped.some(p=>p.longitude>170)).toBe(true);
  expect(grouped.some(p=>p.longitude< -170)).toBe(true);
});
