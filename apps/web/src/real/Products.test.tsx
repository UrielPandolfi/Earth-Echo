import { cleanup,render,screen,within } from '@testing-library/react';
import { afterEach,expect,it } from 'vitest';
import { ProductInspector,productTimeLabel } from './Products';
import type { ScientificProduct,RefreshStatus } from '../domain/generated';
import native from '../../../../data/real/products/d26-rgi60-patagonia-outlines/current.json';
import roni from '../../../../data/real/products/d48-roni-history/current.json';
import seasonal from '../../../../data/real/products/d09-seas5-pampa-precipitacion/current.json';
import discharge from '../../../../data/real/products/d10-glofas-rosario/current.json';
import smoc from '../../../../data/real/products/d14-smoc-u-total/current.json';
import thetao from '../../../../data/real/products/d14-thetao-surface/current.json';

afterEach(cleanup);

it('muestra el registro seleccionado arriba y conserva sus atributos nativos accesibles',()=>{
  const product=native as unknown as ScientificProduct;
  const {container,rerender}=render(<ProductInspector product={product} selectedId={null}/>);
  const body=container.querySelector<HTMLElement>('.inspector-body')!;
  body.scrollTop=500;
  rerender(<ProductInspector product={product} selectedId="RGI60-17.00312"/>);
  const selected=screen.getByRole('region',{name:'Registro seleccionado'});
  expect(body.firstElementChild).toBe(selected);
  expect(body.scrollTop).toBe(0);
  expect(within(selected).getByRole('heading').textContent).toBe('Perito Moreno');
  expect(selected.textContent).toContain('263.322 km²');
  expect(selected.querySelector('details')?.open).toBe(false);
  expect(selected.querySelector('details')?.textContent).toContain('BgnDate: 20009999');
  expect(selected.textContent).not.toContain('Excluido del mapa');
});

it('mantiene la historia RONI como serie histórica y no la presenta como tabla de pronóstico',()=>{
  render(<ProductInspector product={roni as unknown as ScientificProduct} selectedId={null}/>);
  expect(screen.getByRole('region',{name:'Serie del producto'})).toBeTruthy();
  expect(screen.getByRole('heading',{name:'Serie histórica'})).toBeTruthy();
  expect(screen.queryByRole('region',{name:'Pronóstico oficial ENSO RONI'})).toBeNull();
});

it('presenta SEAS5 como pronóstico mensual, con crédito visible y fechas separadas',()=>{
  const {container}=render(<ProductInspector product={seasonal as unknown as ScientificProduct} selectedId={null}/>);
  expect(screen.getByRole('heading',{name:'Serie del pronóstico'})).toBeTruthy();
  expect(screen.getByRole('link',{name:'Weather data by Open-Meteo.com'}).getAttribute('href')).toBe('https://open-meteo.com/');
  expect(container.querySelector('.chart-key')?.textContent).toBe(' Pronóstico');
  expect(screen.getByText('Inicialización')).toBeTruthy();
  expect(screen.getByText('Emisión')).toBeTruthy();
});

it('mantiene fechas diarias distintas para caudal sin concatenar miembros del ensemble',()=>{
  const {container}=render(<ProductInspector product={discharge as unknown as ScientificProduct} selectedId={null}/>);
  const labels=[...container.querySelectorAll('.chart-labels span')].map(e=>e.textContent);
  expect(labels).toEqual(['2026-11-14','2026-11-16','2026-11-18','2026-11-20']);
  expect(container.querySelectorAll('.chart-dot-forecast').length).toBe(7);
  expect(container.querySelector('.chart-key')?.textContent).toBe(' Pronóstico');
  expect(screen.getByRole('link',{name:'Weather data by Open-Meteo.com'})).toBeTruthy();
});

it('preserva la coordenada temporal de una media horaria sin inventar el inicio del promedio',()=>{
  const product=smoc as unknown as ScientificProduct;
  render(<ProductInspector product={product} selectedId={null}/>);
  expect(productTimeLabel(product)).toBe('Fecha de validez 2026-11-15T00:30:00Z');
  expect(screen.getByText('Fecha de validez 2026-11-15T00:30:00Z UTC')).toBeTruthy();
  expect(screen.queryByText(/Validez desde/)).toBeNull();
});

it('presenta temperatura potencial en su profundidad y separa consulta de recuperación original',()=>{
  const product=thetao as unknown as ScientificProduct;
  const refresh={jobs:{'d14-thetao-native':{status:'unchanged',last_success_at:'2026-11-14T22:10:00Z'}}} as unknown as RefreshStatus;
  render(<ProductInspector product={product} selectedId={null} refreshStatus={refresh}/>);
  expect(screen.getByRole('heading',{name:'Temperatura potencial marina · 0,494025m · Caribe/Atlántico'})).toBeTruthy();
  expect(screen.getByText('Última consulta satisfactoria')).toBeTruthy();
  expect(screen.getByText('2026-11-14T22:10:00Z')).toBeTruthy();
  expect(screen.getByText('Fecha de validez 2026-11-15T00:00:00Z UTC')).toBeTruthy();
});
