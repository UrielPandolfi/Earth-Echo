import { cleanup,render,screen } from '@testing-library/react';
import { afterEach,it,expect,vi } from 'vitest';
import { TrendPanel } from './TrendPanel';

afterEach(()=>{cleanup();vi.unstubAllGlobals();});

it('keeps independent real analyses available when the trend request fails',async()=>{
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>{
    if(url.endsWith('/d15-sst'))return new Response('',{status:503});
    if(url.endsWith('/d15-anomalies'))return new Response(JSON.stringify({status:'unavailable',product:null,reason:'No hay anomalías recalculadas'}));
    return new Response(JSON.stringify({status:'unavailable',pairs:[],reason:'No hay asociaciones recalculadas'}));
  }));
  render(<TrendPanel mode="real" analysisOpen={false} onAnalysis={()=>{}}/>);
  expect(await screen.findByText('La tendencia no respondió.')).toBeTruthy();
  expect(await screen.findByText('No hay anomalías recalculadas')).toBeTruthy();
  expect(await screen.findByText('No hay asociaciones recalculadas')).toBeTruthy();
  expect(screen.queryByText('Sin análisis en DEMO')).toBeNull();
});

it('shows interval sensitivity and residual dependence without presenting a forecast',async()=>{
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>new Response(JSON.stringify(url.endsWith('/d15-sst') ? {
    status:'evaluated',narrative:'Tendencia histórica estacional',reference_start:'2014-01',reference_end:'2021-12',analysis_start:'2014-01',analysis_end:'2025-12',present_months:144,expected_months:144,missing_months:0,slope_c_per_year:.068,interval_low_c_per_year:.027,interval_high_c_per_year:.109,includes_zero:false,method_id:'seasonal-v2',execution_id:'abc',bootstrap_block_months:12,sensitivity_block_months:24,sensitivity_low_c_per_year:.026,sensitivity_high_c_per_year:.111,residual_lag1_r:.844,
  } : {status:'unavailable',product:null,pairs:[],reason:'No disponible en este caso de prueba'}))));
  render(<TrendPanel mode="real" analysisOpen={false} onAnalysis={()=>{}}/>);
  expect(await screen.findByText('0.068 °C/año')).toBeTruthy();
  expect(screen.getByText(/Sensibilidad con 24 meses: 0.026 a 0.111/)).toBeTruthy();
  expect(screen.getByText(/0.844/)).toBeTruthy();
  expect(screen.getByText('No es un pronóstico')).toBeTruthy();
});
