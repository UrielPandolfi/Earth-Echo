import { useCallback, useEffect, useRef, useState } from 'react';
import type { ForecastCatalog,ForecastField,ForecastPoint,ForecastHighlights,PlanetaryForecast,EnsoOutlook,AftershockForecasts,SentryAssessments } from '../domain/generated';

const api=import.meta.env.VITE_API_BASE ?? '/api';
const storageKey='earth-echo-forecast-selection-v1';
type Position={longitude:number;latitude:number};
type Selection={d16:string|null;ifs:string|null;position:Position|null;threshold:number;mode:'d16'|'ifs'|'kp'|'enso'|'oaf'|'sentry';season:string|null;eventId:string|null;oafWindow:string|null;oafMagnitude:number|null};
function saved():Selection {
  const fallback:Selection={d16:null,ifs:null,position:null,threshold:.7,mode:'d16',season:null,eventId:null,oafWindow:null,oafMagnitude:null};
  try {
    const value=JSON.parse(localStorage.getItem(storageKey) ?? 'null') as Partial<Selection>|null;
    if(!value)return fallback;
    return {...fallback,d16:typeof value.d16==='string' ? value.d16 : null,ifs:typeof value.ifs==='string' ? value.ifs : null,
      mode:['d16','ifs','kp','enso','oaf','sentry'].includes(value.mode ?? '') ? value.mode! : 'd16',
      season:typeof value.season==='string' ? value.season : null,
      eventId:typeof value.eventId==='string' ? value.eventId : null,
      oafWindow:typeof value.oafWindow==='string' ? value.oafWindow : null,
      oafMagnitude:typeof value.oafMagnitude==='number' ? value.oafMagnitude : null,
      threshold:typeof value.threshold==='number' && value.threshold>=0 && value.threshold<=1 ? value.threshold : .7,
      position:value.position && Number.isFinite(value.position.longitude) && Number.isFinite(value.position.latitude) && Math.abs(value.position.latitude)<=90 ? value.position : null};
  } catch {return fallback;}
}
async function get<T>(path:string,signal:AbortSignal):Promise<T> {
  const response=await fetch(`${api}${path}`,{signal});
  if(!response.ok)throw new Error(`Consulta no disponible (${response.status}); se conserva REAL.`);
  return await response.json() as T;
}

export function useForecastExplorer(enabled:boolean) {
  const [selection,setSelection]=useState<Selection>(saved);
  const [catalog,setCatalog]=useState<ForecastCatalog|null>(null);
  const [field,setField]=useState<ForecastField|null>(null);
  const [point,setPoint]=useState<{key:string;longitude:number;latitude:number;result:ForecastPoint}|null>(null);
  const [highlights,setHighlights]=useState<ForecastHighlights|null>(null);
  const [kp,setKp]=useState<PlanetaryForecast|null>(null);
  const [error,setError]=useState<string|null>(null);
  const [pointError,setPointError]=useState<string|null>(null);
  const [highlightError,setHighlightError]=useState<string|null>(null);
  const [kpError,setKpError]=useState<string|null>(null);
  const [enso,setEnso]=useState<EnsoOutlook|null>(null);
  const [ensoError,setEnsoError]=useState<string|null>(null);
  const [oaf,setOaf]=useState<AftershockForecasts|null>(null);
  const [oafError,setOafError]=useState<string|null>(null);
  const [sentry,setSentry]=useState<SentryAssessments|null>(null);
  const [sentryError,setSentryError]=useState<string|null>(null);
  const revision=useRef(0);
  useEffect(()=>{try{localStorage.setItem(storageKey,JSON.stringify(selection));}catch{/* Private storage may be disabled. */}},[selection]);
  useEffect(()=>{
    if(!enabled)return;
    const controller=new AbortController();
    async function load(){
      try{
        const body=await get<ForecastCatalog>('/v1/forecasts/catalog',controller.signal);
        if(controller.signal.aborted)return;
        if(body.data_mode!=='real' || !Array.isArray(body.forecasts))throw new Error('Contrato de pronósticos inválido.');
        setCatalog(body);setError(null);
        setSelection(s=>({...s,d16:s.d16 ?? body.default_d16_id,ifs:s.ifs ?? [...body.forecasts].filter(f=>f.source_id==='D07' && f.variable==='2t' && f.queryable).sort((a,b)=>(b.valid_from ?? '').localeCompare(a.valid_from ?? ''))[0]?.id ?? null}));
      }catch(e){if(!controller.signal.aborted)setError(e instanceof Error ? e.message : 'Catálogo no disponible.');}
    }
    void load();const timer=window.setInterval(()=>void load(),60_000);
    return ()=>{controller.abort();window.clearInterval(timer);};
  },[enabled]);
  useEffect(()=>{
    if(!enabled)return;
    const controller=new AbortController();
    async function load(){try{
      const body=await get<EnsoOutlook>('/v1/forecasts/enso/d48',controller.signal);
      if(!controller.signal.aborted){setEnso(body);setEnsoError(null);}
    }catch(e){if(!controller.signal.aborted)setEnsoError(e instanceof Error ? e.message : 'ENSO no disponible.');}}
    void load();const timer=window.setInterval(()=>void load(),60_000);
    return ()=>{controller.abort();window.clearInterval(timer);};
  },[enabled]);
  const key=selection.mode==='d16' ? selection.d16 : selection.mode==='ifs' ? selection.ifs : null;
  useEffect(()=>{
    if(!enabled || !key)return;
    const controller=new AbortController();
    void get<ForecastField>(`/v1/forecasts/fields/${key}`,controller.signal).then(body=>{
      if(!controller.signal.aborted){setField(body);setError(body.status==='missing_input' || body.status==='not_implemented' ? body.reason ?? 'Entrada no disponible.' : null);}
    }).catch(e=>{if(!controller.signal.aborted)setError(e.message);});
    return ()=>controller.abort();
  },[enabled,key,catalog?.as_of]);
  useEffect(()=>{
    if(!enabled || !key || selection.mode!=='d16')return;
    const controller=new AbortController();setHighlightError(null);
    void get<ForecastHighlights>(`/v1/forecasts/fields/${key}/highlights?probability_filter=${selection.threshold}`,controller.signal).then(body=>{
      if(!controller.signal.aborted)setHighlights(body);
    }).catch(e=>{if(!controller.signal.aborted)setHighlightError(e.message);});
    return ()=>controller.abort();
  },[enabled,key,selection.mode,selection.threshold,catalog?.as_of]);
  const longitude=selection.position?.longitude,latitude=selection.position?.latitude;
  useEffect(()=>{
    const sequence=++revision.current;
    if(!enabled || !key || longitude==null || latitude==null)return;
    const controller=new AbortController();setPointError(null);
    void get<ForecastPoint>(`/v1/forecasts/fields/${key}/point?longitude=${longitude}&latitude=${latitude}`,controller.signal).then(body=>{
      if(!controller.signal.aborted && revision.current===sequence){setPoint({key,longitude,latitude,result:body});if(!body.forecast)setPointError(body.reason ?? 'Entrada no disponible.');}
    }).catch(e=>{if(!controller.signal.aborted && revision.current===sequence)setPointError(e.message);});
    return ()=>controller.abort();
  },[enabled,key,longitude,latitude,catalog?.as_of]);
  useEffect(()=>{
    if(!enabled)return;
    const controller=new AbortController();
    async function load(){try{
      const body=await get<PlanetaryForecast>('/v1/forecasts/planetary/d28-kp',controller.signal);
      if(!controller.signal.aborted){setKp(body);setKpError(null);}
    }catch(e){if(!controller.signal.aborted)setKpError(e instanceof Error ? e.message : 'Kp no disponible.');}}
    void load();const timer=window.setInterval(()=>void load(),60_000);
    return ()=>{controller.abort();window.clearInterval(timer);};
  },[enabled]);
  useEffect(()=>{
    if(!enabled)return;
    const controller=new AbortController();
    async function load(){try{
      const body=await get<EnsoOutlook>('/v1/forecasts/enso/d48',controller.signal);
      if(!controller.signal.aborted){setEnso(body);setEnsoError(null);}
    }catch(e){if(!controller.signal.aborted)setEnsoError(e instanceof Error ? e.message : 'ENSO no disponible.');}}
    void load();const timer=window.setInterval(()=>void load(),60_000);
    return ()=>{controller.abort();window.clearInterval(timer);};
  },[enabled]);
  useEffect(()=>{
    if(!enabled)return;
    const controller=new AbortController();
    async function load(){try{
      const body=await get<AftershockForecasts>('/v1/forecasts/aftershocks/d22',controller.signal);
      if(!controller.signal.aborted && Array.isArray(body.events)){setOaf(body);setOafError(null);}
    }catch(e){if(!controller.signal.aborted)setOafError(e instanceof Error ? e.message : 'Réplicas no disponibles.');}}
    void load();const timer=window.setInterval(()=>void load(),60_000);
    return ()=>{controller.abort();window.clearInterval(timer);};
  },[enabled]);
  useEffect(()=>{
    if(!enabled)return;
    const controller=new AbortController();
    async function load(){try{
      const body=await get<SentryAssessments>('/v1/forecasts/impacts/d29',controller.signal);
      if(!controller.signal.aborted && Array.isArray(body.objects) && Array.isArray(body.removed)){setSentry(body);setSentryError(null);}
    }catch(e){if(!controller.signal.aborted)setSentryError(e instanceof Error ? e.message : 'Sentry no disponible.');}}
    void load();const timer=window.setInterval(()=>void load(),60_000);
    return ()=>{controller.abort();window.clearInterval(timer);};
  },[enabled]);
  const selectPosition=useCallback((position:Position)=>setSelection(s=>({...s,position})),[]);
  const activeField=field?.forecast?.id===key ? field : null;
  // Match the request identity, not independently normalized floating degrees:
  // JS/Python modulo paths can differ by1ULP for an actual Cesium click. A
  // returned canonical longitude is scientific metadata, not a request token.
  const activePoint=point?.key===key && point.result.forecast?.id===key && point.longitude===longitude && point.latitude===latitude ? point.result : null;
  const activeHighlights=highlights?.forecast_id===key && highlights.probability_filter===selection.threshold ? highlights : null;
  return {selection,catalog,key,field:activeField,point:activePoint,highlights:activeHighlights,kp,enso,oaf,sentry,error,pointError,highlightError,kpError,ensoError,oafError,sentryError,
    selectPosition,setMode:(mode:Selection['mode'])=>setSelection(s=>({...s,mode})),
    setSeason:(season:string)=>setSelection(s=>({...s,season})),
    setEvent:(eventId:string)=>setSelection(s=>({...s,eventId})),
    setOafWindow:(oafWindow:string)=>setSelection(s=>({...s,oafWindow})),
    setOafMagnitude:(oafMagnitude:number)=>setSelection(s=>({...s,oafMagnitude})),
    setPeriod:(id:string)=>setSelection(s=>({...s,[s.mode==='d16'?'d16':'ifs']:id})),setThreshold:(threshold:number)=>setSelection(s=>({...s,threshold}))};
}
export type ForecastExplorer=ReturnType<typeof useForecastExplorer>;
