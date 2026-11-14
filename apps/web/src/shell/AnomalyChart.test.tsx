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
