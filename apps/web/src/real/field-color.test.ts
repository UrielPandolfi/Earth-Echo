import {expect,it} from 'vitest';
import {paintSstField,type RealField} from './view';

it('uses logarithms only for colour, preserving units, values and transparent missing cells',()=>{
  const field:RealField={observation_id:'test',unit:'mg/m³',width:4,height:1,west:0,east:4,south:0,north:1,minimum:1,maximum:100,values:[1,10,100,null],missing_cells:1,color_scale:'log10'};
  const result=paintSstField(field);
  expect([...result.rgba.slice(4,8)]).toEqual([136,112,121,220]);
  expect([...result.rgba.slice(12,16)]).toEqual([0,0,0,0]);
  expect(field.values).toEqual([1,10,100,null]);
});

it('reverses wetness percentile colours without changing zero, units or missing values',()=>{
  const field:RealField={observation_id:'wetness',unit:'% (percentil)',width:3,height:1,west:0,east:3,south:0,north:1,minimum:0,maximum:100,values:[0,100,null],missing_cells:1,reverse_colors:true};
  const result=paintSstField(field);
  expect([...result.rgba.slice(0,4)]).toEqual([224,92,56,220]);
  expect([...result.rgba.slice(4,8)]).toEqual([48,132,186,220]);
  expect([...result.rgba.slice(8,12)]).toEqual([0,0,0,0]);
  expect(field.values).toEqual([0,100,null]);
});
