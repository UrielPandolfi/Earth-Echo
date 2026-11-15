import { cleanup,render,screen,fireEvent } from '@testing-library/react';
import { afterEach,it,expect,vi } from 'vitest';
import { SSTAnomalies } from './SSTAnomalies';

afterEach(()=>{cleanup();vi.unstubAllGlobals();});

it('offers the distinct current daily field even when historical analysis is missing',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>new Response(JSON.stringify({status:'unavailable',product:null,reason:'Historia ausente',current_daily_anomaly_id:'d13-oisst-anomaly-global',current_daily_anomaly_at:'2026-11-13T12:00:00Z'}))));
  const show=vi.fn();render(<SSTAnomalies onShowProduct={show}/>);
  fireEvent.click(await screen.findByRole('button',{name:'Ver campo diario en el globo'}));
  expect(show).toHaveBeenCalledWith('d13-oisst-anomaly-global');
  expect(screen.getByText(/base 1971–2000/)).toBeTruthy();
  expect(screen.getByText('Historia ausente')).toBeTruthy();
});

it('shows historical candidates and provenance without a probability or map pins',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>new Response(JSON.stringify({status:'evaluated',flagged_months:1,assessed_months:2,warm_months:1,cold_months:0,missing_months:1,assessment_period:'2022–2025 · histórico',reason:null,product:{id:'d15-sst-seasonal-departures',method_version:'test-method',coverage:'Recorte nativo',limitation:'Sin causalidad',attribution:'NOAA',samples:[
    {id:'2022-01',category:'warm_departure',value:1.2,attributes:{modified_z:'4.5'}},
    {id:'2022-02',category:'within_threshold',value:0,attributes:{modified_z:'0'}},
    {id:'2022-03',category:'missing',value:null,attributes:{modified_z:null}},
  ]}}))));
  render(<SSTAnomalies/>);
  expect(await screen.findByText(/1 meses candidatos de 2 evaluados/)).toBeTruthy();
  fireEvent.click(screen.getByText('Ver serie y meses candidatos'));
  expect(screen.getByRole('img',{name:/Desvío mensual/})).toBeTruthy();
  expect(screen.getByText('2022-01')).toBeTruthy();
  expect(screen.queryByText('2022-03')).toBeNull();
  expect(screen.getByRole('link',{name:'Entrada mensual retenida'}).getAttribute('href')).toMatch(/\/original$/);
  expect(screen.queryByText('Recta')).toBeNull();
  expect(screen.getByText(/sin probabilidad de daño/)).toBeTruthy();
});

it('shows unavailable and network failure explicitly',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>new Response(JSON.stringify({status:'unavailable',product:null,reason:'Entrada real ausente'}))));
  const mounted=render(<SSTAnomalies/>);
  expect(await screen.findByText('Entrada real ausente')).toBeTruthy();
  mounted.unmount();
  vi.stubGlobal('fetch',vi.fn(async()=>{throw new Error('Red no disponible');}));
  render(<SSTAnomalies/>);
  expect((await screen.findByRole('status')).textContent).toContain('REAL conserva sus datos');
  expect(screen.queryByText(/0 meses candidatos/)).toBeNull();
});
