import {render,screen,within,cleanup} from '@testing-library/react';
import {afterEach,expect,it} from 'vitest';
import type {ScientificProduct} from '../domain/generated';
import phase from '../../../../data/real/products/d48-roni-probabilities/current.json';
import quantiles from '../../../../data/real/products/d48-roni-outlook/current.json';
import {CpcEnsoPanel} from './CpcEnsoPanel';

afterEach(cleanup);

it('conserva fase, ventanas, cero publicado y faltante sin fabricar una probabilidad',()=>{
  const product=structuredClone(phase) as unknown as ScientificProduct;
  product.samples=(product.samples ?? []).filter(s=>!(s.attributes?.season==='FMA 2027' && s.category==='Neutral'));
  render(<CpcEnsoPanel product={product}/>);
  expect(screen.getByRole('columnheader',{name:'La Niña'})).toBeTruthy();
  const row=screen.getByRole('rowheader',{name:'FMA 2027'}).closest('tr')!;
  expect(within(row).getAllByRole('cell').map(c=>c.textContent)).toEqual(['0','—','98']);
  expect(screen.getByText(/0% publicado es aproximado/)).toBeTruthy();
  expect(screen.getByRole('rowheader',{name:'NDJ 2026–2027'})).toBeTruthy();
});

it('muestra percentiles como valores del índice, sin barras de probabilidad',()=>{
  const {container}=render(<CpcEnsoPanel product={quantiles as unknown as ScientificProduct}/>);
  expect(screen.getByRole('columnheader',{name:'p50'})).toBeTruthy();
  const row=screen.getByRole('rowheader',{name:'JJA 2027'}).closest('tr')!;
  expect(within(row).getAllByRole('cell')[3].textContent).toBe('-0,25');
  expect(container.querySelectorAll('.cpc-prob-bar').length).toBe(0);
  expect(screen.getByText(/p50 es la mediana/)).toBeTruthy();
});
