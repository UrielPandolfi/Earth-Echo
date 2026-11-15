import {act,cleanup,fireEvent,render,renderHook,screen,waitFor,within} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import type {ForecastDescriptor,ForecastField,ForecastPoint,ForecastCatalog,ScientificGrid,ForecastHighlights} from '../domain/generated';
import type {GlobeHandle} from '../globe/lifecycle';
import {ObservatoryApp} from '../shell/ObservatoryApp';
import {paintForecastField} from './field';
import {useForecastExplorer} from './useForecastExplorer';
import evidence from '../../../../data/samples/forecast-map/evidence.json';

const a='a'.repeat(64),b='b'.repeat(64);
function meta(id=a):ForecastDescriptor {
  return {id,product_id:id===a ? 'd16-mhw-month-2':'d16-mhw-month-3',source_id:'D16',phenomenon_id:'F18',title:'Calor marino previsto · mensual',provider:'NOAA PSL / NMME',
    result_type:'imported_probability',spatial_support:'field',queryable:true,availability:'available',temporal_state:'future',variable:'mhw_probability',unit:'1',native_unit:'fracción [0,1]',
    event_definition:'Anomalía SST mensual sobre p90 estacional, con tendencia retenida.',scientific_threshold:'p90 de 1991–2020',reference_period:'1991–2020',trend_treatment:'retained',method:'provider',adapter_version:'v1',provider_version:'cycle=2026-10',identity_basis:'test adapter fixture',
    initialized_at:'2026-10-01T00:00:00Z',issued_at:null,retrieved_at:'2026-11-15T00:02:22Z',processed_at:'2026-11-15T00:02:22Z',first_seen_at:'2026-11-15T00:02:22Z',first_seen_basis:'Primera captura local retenida',
    valid_from:id===a ? '2026-12-01T00:00:00Z':'2027-01-01T00:00:00Z',valid_to:id===a ? '2027-01-01T00:00:00Z':'2027-02-01T00:00:00Z',temporal_semantics:'monthly_interval',
    coverage:'Controlled test grid',resolution:'1°',quality_mask:'NaN native',original_url:evidence.source_url,original_sha256:evidence.original_sha256,original_download:`/v1/forecasts/fields/${id}/original`,metadata_download:`/v1/forecasts/fields/${id}`,reference_url:'https://psl.noaa.gov/marine-heatwaves/',limitation:'Research only',experimental:true,update_pending:false,skill_note:'Habilidad por región/plazo no evaluada en Earth Echo.'};
}
function field(id=a):ForecastField {
  // Small controlled transport fixture; real exact probability from the NOAA
  // probe. Null/zero exercise rendering; this is never production data.
  const probability=id===a ? evidence.probes[1].value! : evidence.probes[2].value!;
  const grid:ScientificGrid={width:2,height:2,west:-67.5,east:-65.5,south:16.5,north:18.5,longitudes:[-67,-66],latitudes:[18,17],values:[null,0,probability,.6],minimum:0,maximum:probability,missing_cells:1,resolution:'Controlled1°',sampling:'test only',quality_mask:'null'};
  return {status:'available',forecast:meta(id),grid};
}
function point(id=a,longitude=-67,latitude=17):ForecastPoint {
  const f=field(id);const r=latitude===18 ? 0:1,c=longitude===-66 ? 1:0;const v=f.grid!.values[r*2+c];
  return {status:v==null ? 'no_coverage':'available',forecast:f.forecast,requested_longitude:longitude,requested_latitude:latitude,probability:v,value:null,unit:'1',reason:v==null ? 'Sin cobertura en esta posición: máscara nativa.':null,
    cell:{id:`r${r}-c${c}`,row:r,column:c,longitude,latitude,extent:{west:longitude-.5,east:longitude+.5,south:latitude-.5,north:latitude+.5,crosses_antimeridian:false},geometry:{type:'MultiPolygon',coordinates:[[[[longitude-.5,latitude-.5],[longitude+.5,latitude-.5],[longitude+.5,latitude+.5],[longitude-.5,latitude+.5],[longitude-.5,latitude-.5]]]]},support_note:'1° native cell'},selection_rule:'Containing cell; no interpolation'};
}
const catalog:ForecastCatalog={data_mode:'real',as_of:'2026-11-15T15:00:00Z',forecasts:[meta(a),meta(b)],default_d16_id:a,future_fields:2,current_fields:0,archived_fields:0,own_experiments:1,note:'Imported, not own predictions'};
function highlights(id=a,threshold=.7):ForecastHighlights {
  const p=point(id),match=p.probability!>=threshold;
  return {status:'available',forecast_id:id,probability_filter:threshold,rule:'four neighbors, native valid representatives',matching_cells:match ? 1:0,total_areas:match ? 1:0,returned_areas:match ? 1:0,limit:20,reason:match ? null:'Sin áreas que cumplan este filtro.',areas:match ? [{id:`${id}:r1-c0`,cell_count:1,probability_min:p.probability!,probability_max:p.probability!,representative:p}]:[]};
}
const json=(body:unknown)=>new Response(JSON.stringify(body),{headers:{'Content-Type':'application/json'}});
function response(input:string):Response {
  const u=new URL(input,'http://localhost');
  if(u.pathname.endsWith('/forecasts/catalog'))return json(catalog);
  if(u.pathname.endsWith('/forecasts/planetary/d28-kp'))return json({status:'missing_input',windows:[],note:'test'});
  if(u.pathname.includes('/forecasts/fields/')){
    const id=u.pathname.split('/fields/')[1].split('/')[0];
    if(u.pathname.endsWith('/highlights'))return json(highlights(id,Number(u.searchParams.get('probability_filter'))));
    if(u.pathname.endsWith('/point'))return json(point(id,Number(u.searchParams.get('longitude')),Number(u.searchParams.get('latitude'))));
    return json(field(id));
  }
  if(u.pathname.endsWith('/catalog/phenomena'))return json({total:31});
  if(u.pathname.endsWith('/v1/products'))return json({data_mode:'real',products:[],connected_sources:33,observation_records:100,calculated_indicator_products:3});
  if(u.pathname.endsWith('/operations/refresh'))return json({jobs:{},recent_scan:true});
  if(u.pathname.endsWith('/layers/d21-events'))return json({features:[]});
  if(u.pathname.endsWith('/layers/d28-kp'))return json({latest_kp:null});
  return json({status:'unavailable',observations:[],reason:'No demo fallback'});
}

afterEach(()=>{cleanup();localStorage.clear();vi.unstubAllGlobals();});

it('opens forecast mode, queries a cell through the globe, switches month and preserves the camera',async()=>{
  vi.stubGlobal('fetch',vi.fn(async(input:string)=>response(input)));
  let geo:((p:{longitude:number;latitude:number})=>void)|null=null;
  const focus=vi.fn(),setField=vi.fn(),setSelection=vi.fn();
  const globe:GlobeHandle={destroy(){},setGeographicListener(fn){geo=fn;},focusRegion:focus,setField,setFieldSelection:setSelection};
  render(<ObservatoryApp createGlobe={()=>globe}/>);
  fireEvent.click(screen.getByRole('button',{name:'REAL'}));
  fireEvent.click(screen.getByRole('button',{name:'Pronósticos'}));
  expect(await screen.findByRole('heading',{name:'Calor marino previsto · mensual'})).toBeTruthy();
  await waitFor(()=>expect(geo).toBeTypeOf('function'));
  act(()=>geo?.({longitude:-67,latitude:17}));
  const inspector=screen.getByRole('complementary',{name:'Pronóstico seleccionado'});
  expect(await within(inspector).findByText('94,4 %')).toBeTruthy();
  expect(within(inspector).getByText(/Probabilidad del evento mensual/)).toBeTruthy();
  expect(within(inspector).getByText(/Habilidad por región\/plazo no evaluada/)).toBeTruthy();
  expect(setSelection.mock.calls.at(-1)?.[0]?.cell.id).toBe('r1-c0');
  fireEvent.change(screen.getByLabelText('Período del pronóstico'),{target:{value:b}});
  expect(await within(inspector).findByText('91,1 %')).toBeTruthy();
  expect(focus).not.toHaveBeenCalled();
  fireEvent.click(within(inspector).getByRole('tab',{name:'Datos'}));
  expect(within(inspector).getByText(/0.9112903475761414/)).toBeTruthy();
  expect(within(inspector).getByRole('link',{name:'Descargar celda CSV exacta'}).getAttribute('href')).toContain(b);
  act(()=>geo?.({longitude:-67,latitude:18}));
  fireEvent.click(within(inspector).getByRole('tab',{name:'Resumen'}));
  expect(await within(inspector).findByRole('heading',{name:'Sin cobertura en esta posición'})).toBeTruthy();
  fireEvent.change(screen.getByLabelText('Filtro de probabilidad'),{target:{value:'100'}});
  expect(await screen.findByText('Sin áreas que cumplan este filtro.')).toBeTruthy();
  expect(screen.getByText(/0 áreas con este filtro/)).toBeTruthy();
  expect(setField).toHaveBeenCalled();
});

it('discards a stale cell response even when transport ignores AbortSignal',async()=>{
  let resolveOld:((r:Response)=>void)|null=null;
  vi.stubGlobal('fetch',vi.fn((input:string)=>{
    if(input.includes(`/fields/${a}/point`))return new Promise<Response>(resolve=>{resolveOld=resolve;});
    return Promise.resolve(response(input));
  }));
  const {result,unmount}=renderHook(()=>useForecastExplorer(true));
  await waitFor(()=>expect(result.current.key).toBe(a));
  act(()=>result.current.selectPosition({longitude:-67,latitude:17}));
  await waitFor(()=>expect(resolveOld).toBeTypeOf('function'));
  act(()=>result.current.setPeriod(b));
  await waitFor(()=>expect(result.current.point?.forecast?.id).toBe(b));
  await act(async()=>{resolveOld!(json(point(a)));});
  expect(result.current.point?.forecast?.id).toBe(b);
  expect(result.current.point?.probability).toBe(evidence.probes[2].value);
  unmount();
  const restarted=renderHook(()=>useForecastExplorer(true));
  await waitFor(()=>expect(restarted.result.current.point?.forecast?.id).toBe(b));
  expect(restarted.result.current.selection.position).toEqual({longitude:-67,latitude:17});
});

it('keeps zero visible and null transparent with a fixed probability legend',()=>{
  const g=field().grid!;const painted=paintForecastField(g,true);
  expect(painted.rgba[3]).toBe(0);
  expect(painted.rgba[7]).toBeGreaterThan(0);
  expect(Array.from(painted.rgba.slice(4,7))).toEqual([48,132,186]);
  expect(painted.west).toBe(-67.5);
});

it('accepts fractional Cesium coordinates when canonical longitude differs by a floating point ULP',async()=>{
  const lon=-67.12345678901234,lat=17.12345678901234;
  const canonical=(lon+180)%360-180; // server path for this positive modulo operand
  expect(canonical).not.toBe(((lon+180)%360+360)%360-180);
  vi.stubGlobal('fetch',vi.fn(async(input:string)=>input.includes('/point?') ? json({...point(a),requested_longitude:canonical,requested_latitude:lat}) : response(input)));
  const {result}=renderHook(()=>useForecastExplorer(true));
  await waitFor(()=>expect(result.current.key).toBe(a));
  act(()=>result.current.selectPosition({longitude:lon,latitude:lat}));
  await waitFor(()=>expect(result.current.point?.probability).toBe(evidence.probes[1].value));
});

it('splits a cell centred at -180 across the texture seam without interpolating values',()=>{
  const g:ScientificGrid={...field().grid!,width:4,height:2,longitudes:[-180,-90,0,90],latitudes:[45,-45],values:[0,.25,.5,1,null,.25,.5,.75],west:-180,east:135,south:-90,north:90,missing_cells:1};
  const paint=paintForecastField(g,true);
  expect(paint.west).toBe(-180);expect(paint.east).toBe(180);expect(paint.width).toBe(8);
  expect(Array.from(paint.rgba.slice(0,4))).toEqual(Array.from(paint.rgba.slice(28,32)));
  expect(paint.rgba[8*4+3]).toBe(0);expect(paint.rgba[15*4+3]).toBe(0);
});

it('preserves native polar values in half-height cells without stretching all rows',()=>{
  const g:ScientificGrid={...field().grid!,width:2,height:3,longitudes:[-90,90],latitudes:[90,0,-90],values:[.1,.2,.3,.4,null,null],west:-180,east:180,south:-90,north:90,missing_cells:2};
  const paint=paintForecastField(g,true);
  expect(paint.height).toBe(4);
  expect(paint.rgba[3]).toBeGreaterThan(0); // finite90°N really exists
  expect(Array.from(paint.rgba.slice(8,16))).toEqual(Array.from(paint.rgba.slice(16,24))); // middle native row copied twice
  expect(paint.rgba[27]).toBe(0); // native90°S missing stays transparent
});

it('shows Kp as a planetary series, including an ongoing window, without a geographic layer',async()=>{
  const f={...meta(),source_id:'D28',phenomenon_id:'F29',title:'Kp previsto · índice planetario',spatial_support:'planetary',result_type:'imported_value',variable:'Kp',unit:'Kp',native_unit:'Kp',experimental:false,initialized_at:null,issued_at:null,temporal_semantics:'three_hour_windows',event_definition:'Índice Kp planetario previsto; sin ubicación local.'};
  vi.stubGlobal('fetch',vi.fn(async(input:string)=>input.includes('/forecasts/planetary/d28-kp') ? json({status:'available',forecast:f,probability:null,note:'Sin probabilidad local de auroras',windows:[{valid_from:'2026-11-15T12:00:00Z',valid_to:'2026-11-15T15:00:00Z',value:0,provider_type:'predicted',temporal_state:'in_progress'},{valid_from:'2026-11-15T15:00:00Z',valid_to:'2026-11-15T18:00:00Z',value:3,provider_type:'predicted',temporal_state:'future'}]}) : response(input)));
  const setField=vi.fn(),setSignals=vi.fn(),geo=vi.fn();
  const globe:GlobeHandle={destroy(){},setField,setSignals,setGeographicListener:geo};
  render(<ObservatoryApp createGlobe={()=>globe}/>);
  fireEvent.click(screen.getByRole('button',{name:'REAL'}));fireEvent.click(screen.getByRole('button',{name:'Pronósticos'}));
  fireEvent.change(screen.getByLabelText('Producto predictivo'),{target:{value:'kp'}});
  const inspector=screen.getByRole('complementary',{name:'Pronóstico seleccionado'});
  expect(await within(inspector).findByRole('heading',{name:'Alcance planetario'})).toBeTruthy();
  expect(within(inspector).getByRole('table').textContent).toContain('En curso');
  expect(within(inspector).getByRole('table').textContent).toContain('0');
  expect(setField.mock.calls.at(-1)?.[0]).toBeNull();
  expect(setSignals.mock.calls.at(-1)?.[0]).toEqual([]);
  expect(geo.mock.calls.at(-1)?.[0]).toBeNull();
  fireEvent.click(within(inspector).getByRole('tab',{name:'Datos'}));
  const emission=within(inspector).getByText('Emisión').closest('div');
  expect(emission?.textContent).toContain('No informada');
});

it('queries deterministic IFS temperature without assigning a hazard or event probability',async()=>{
  const k='c'.repeat(64);
  const f:ForecastDescriptor={...meta(k),product_id:'d07-ifs-2t-24h',source_id:'D07',phenomenon_id:null,title:'Temperatura prevista · aire a 2 m',provider:'ECMWF IFS',result_type:'imported_value',variable:'2t',unit:'°C',native_unit:'K',experimental:false,valid_from:'2026-11-16T00:00:00Z',valid_to:null,temporal_semantics:'instant',event_definition:'Valor meteorológico sin umbral de desastre.'};
  vi.stubGlobal('fetch',vi.fn(async(input:string)=>{
    if(input.endsWith('/forecasts/catalog'))return json({...catalog,forecasts:[...catalog.forecasts,f]});
    if(input.includes(`/fields/${k}/point`))return json({...point(k),forecast:f,probability:null,value:29.067483520507835,unit:'°C'});
    if(input.endsWith(`/fields/${k}`))return json({...field(k),forecast:f,grid:{...field(k).grid,values:[null,0,29.067483520507835,30],maximum:30}});
    return response(input);
  }));
  let geo:((p:{longitude:number;latitude:number})=>void)|null=null;
  const globe:GlobeHandle={destroy(){},setGeographicListener(fn){geo=fn;}};
  render(<ObservatoryApp createGlobe={()=>globe}/>);
  fireEvent.click(screen.getByRole('button',{name:'REAL'}));fireEvent.click(screen.getByRole('button',{name:'Pronósticos'}));
  await screen.findByRole('heading',{name:'Calor marino previsto · mensual'});
  fireEvent.change(screen.getByLabelText('Producto predictivo'),{target:{value:'ifs'}});
  await screen.findByRole('heading',{name:'Temperatura prevista · aire a 2 m'});
  act(()=>geo?.({longitude:-67,latitude:17}));
  expect(await screen.findByText('29,07 °C')).toBeTruthy();
  const inspector=screen.getByRole('complementary',{name:'Pronóstico seleccionado'});
  expect(within(inspector).queryByText(/Probabilidad del evento mensual/)).toBeNull();
});
