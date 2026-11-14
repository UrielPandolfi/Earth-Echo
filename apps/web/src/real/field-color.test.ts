import {expect,it} from 'vitest';
import {paintSstField,type RealField} from './view';

it('uses logarithms only for colour, preserving units, values and transparent missing cells',()=>{
  const field:RealField={observation_id:'test',unit:'mg/m³',width:4,height:1,west:0,east:4,south:0,north:1,minimum:1,maximum:100,values:[1,10,100,null],missing_cells:1,color_scale:'log10'};
  const result=paintSstField(field);
  expect([...result.rgba.slice(4,8)]).toEqual([136,112,121,220]);
  expect([...result.rgba.slice(12,16)]).toEqual([0,0,0,0]);
  expect(field.values).toEqual([1,10,100,null]);
});
