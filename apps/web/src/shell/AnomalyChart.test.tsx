import {render} from '@testing-library/react';
import {expect,it} from 'vitest';
import {AnomalyChart} from './AnomalyChart';

it('keeps an explicit gap in the observed line and limits only date labels',()=>{
  const points=Array.from({length:248},(_,i)=>({label:`month-${i}`,kind:'observed' as const,value:i===100?null:i}));
  const {container}=render(<AnomalyChart points={points} caption="test monthly series" domain={{min:0,max:248,ticks:[0,124,248]}}/>);
  const path=container.querySelector('.chart-observed')?.getAttribute('d') ?? '';
  expect((path.match(/M/g) ?? []).length).toBe(2);
  expect(container.querySelectorAll('.chart-labels span').length).toBeLessThanOrEqual(6);
  expect(container.querySelectorAll('circle').length).toBe(247);
  expect(container.querySelectorAll('.chart-gap').length).toBe(1);
});

it('labels calculated aggregates explicitly',()=>{
  const {container}=render(<AnomalyChart points={[{label:'2005',kind:'observed',value:18}]} caption="annual aggregate" observedLabel="Agregado calculado"/>);
  expect(container.querySelector('.chart-key')?.textContent).toContain('Agregado calculado');
  expect(container.querySelector('.chart-key')?.textContent).not.toContain('Observado');
});

it('identifica una serie enteramente pronosticada sin leyenda de observaciones',()=>{
  const {container}=render(<AnomalyChart points={[{label:'2026-11',kind:'forecast',value:108.5},{label:'2026-12',kind:'forecast',value:null},{label:'2027-01',kind:'forecast',value:125.4}]} caption="total mensual SEAS5" domain={{min:0,max:130,ticks:[0,65,130]}}/>);
  expect(container.querySelector('.chart-key')?.textContent).toContain('Pronóstico');
  expect(container.querySelector('.chart-key')?.textContent).not.toContain('Observado');
  expect(container.querySelectorAll('.chart-gap').length).toBe(1);
});
