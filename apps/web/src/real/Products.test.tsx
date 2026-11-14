import { render,screen,within } from '@testing-library/react';
import { expect,it } from 'vitest';
import { ProductInspector } from './Products';
import type { ScientificProduct } from '../domain/generated';
import native from '../../../../data/real/products/d26-rgi60-patagonia-outlines/current.json';
import roni from '../../../../data/real/products/d48-roni-history/current.json';

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
