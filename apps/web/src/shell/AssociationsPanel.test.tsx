import { render,screen,cleanup,fireEvent } from '@testing-library/react';
import { afterEach,it,expect,vi } from 'vitest';
import { AssociationsPanel } from './AssociationsPanel';

afterEach(()=>{cleanup();vi.unstubAllGlobals();});

it('compares raw and adjusted association with interval sensitivity, scope and CSV',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>new Response(JSON.stringify({status:'evaluated',method_version:'paired-block-v1',computed_at:'2026-11-15T00:00:00Z',reason:null,pairs:[{
    id:'amoc-sst',title:'AMOC y SST del Caribe',status:'evaluated',n_pairs:40,missing_pairs:1,raw_r:.57,residual_r:.19,x_name:'AMOC',y_name:'SST Caribe',x_unit:'Sv',y_unit:'°C',x_scope:'26,5N',y_scope:'Caribe',warnings:['Asociación no demuestra causalidad.'],inputs:[{product_id:'d34-amoc-monthly',unit:'Sv',checksum_sha256:'abc'}],
    intervals:[{block_quarters:4,low:-.17,high:.54,valid_draws:1000,draws:1000},{block_quarters:8,low:-.21,high:.53,valid_draws:1000,draws:1000}],
    points:[{year:2014,quarter:1,start:'2014-01-01T00:00:00Z',end:'2014-04-01T00:00:00Z',x:14,y:27,residual_x:-1,residual_y:.1},{year:2014,quarter:2,start:'2014-04-01T00:00:00Z',end:'2014-07-01T00:00:00Z',x:null,y:28,residual_x:null,residual_y:null}],
  }]}))));
  render(<AssociationsPanel/>);
  fireEvent.click(await screen.findByText('AMOC y SST del Caribe'));
  expect(screen.getByText('0.570')).toBeTruthy();
  expect(screen.getByText('0.190')).toBeTruthy();
  expect(screen.getByText(/bloques de 8 trimestres/)).toBeTruthy();
  expect(screen.getByRole('img',{name:/Dispersión de residuos/})).toBeTruthy();
  expect(screen.getByRole('link',{name:'Exportar pares CSV'}).getAttribute('href')).toMatch(/amoc-sst.csv$/);
  expect(screen.getByText(/causalidad y predicción siguen sin demostrar/)).toBeTruthy();
});

it('does not invent an association while inputs are unavailable',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>new Response(JSON.stringify({status:'unavailable',reason:'Sin series reales',pairs:[]}))));
  render(<AssociationsPanel/>);
  expect(await screen.findByText('Sin series reales')).toBeTruthy();
  expect(screen.queryByRole('img')).toBeNull();
  expect(screen.queryByText('0.000')).toBeNull();
});
