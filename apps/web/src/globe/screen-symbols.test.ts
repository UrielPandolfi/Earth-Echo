import {expect,it} from 'vitest';
import {visibleSymbols,type ScreenSymbol} from './screen-symbols';

it('evita superposición de tarjetas polares y da prioridad al registro seleccionado',()=>{
  const symbols:ScreenSymbol[]=Array.from({length:120},(_,i)=>({id:`polar-${i}`,x:200+(i%12)*6,y:150+Math.floor(i/12)*5,width:48,height:32,priority:i,facing:true}));
  const before=structuredClone(symbols);
  const shown=visibleSymbols(symbols,600,500,'polar-0');
  expect(shown.has('polar-0')).toBe(true);
  expect(shown.size).toBeLessThan(symbols.length);
  const displayed=symbols.filter(s=>shown.has(s.id));
  for(let i=0;i<displayed.length;i++) for(let j=i+1;j<displayed.length;j++){
    const a=displayed[i],b=displayed[j];
    expect(Math.abs(a.x-b.x)>=52||Math.abs(a.y-b.y)>=36).toBe(true);
  }
  expect(symbols).toEqual(before); // No mutation of the scientific/group count inputs.
});

it('no dibuja símbolos ocultos por el globo o encima de los controles',()=>{
  const base={width:48,height:32,priority:1,facing:true};
  const shown=visibleSymbols([{...base,id:'visible',x:200,y:150},{...base,id:'back',x:300,y:150,facing:false},{...base,id:'header',x:200,y:55},{...base,id:'legend',x:200,y:410}],600,450,null);
  expect([...shown]).toEqual(['visible']);
});
