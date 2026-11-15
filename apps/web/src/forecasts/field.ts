import type { ScientificGrid } from '../domain/generated';
import type { FieldGrid } from '../demo/explore';
import { paintSstField } from '../real/view';

/** Native centres, no bilinear smoothing. D16's -180° centre straddles the seam.
 * Duplicate each1° value into half-degree pixels only to split its seam cell;
 * these are identical copies, not new probabilities. Clicks use the API grid. */
export function paintForecastField(grid:ScientificGrid, probabilistic:boolean):FieldGrid {
  const dx=grid.longitudes[1]-grid.longitudes[0];
  const dy=grid.latitudes[0]-grid.latitudes[1];
  const west=grid.longitudes[0]-dx/2,east=grid.longitudes.at(-1)!+dx/2;
  const south=Math.max(-90,grid.latitudes.at(-1)!-dy/2),north=Math.min(90,grid.latitudes[0]+dy/2);
  const seam=west < -180 || east>180;
  const polar=north<grid.latitudes[0]+dy/2 || south>grid.latitudes.at(-1)!-dy/2;
  const width=seam ? grid.width*2 : grid.width;
  const height=polar ? Math.round((north-south)/(dy/2)) : grid.height;
  const values=seam || polar ? Array.from({length:width*height},(_,i)=>{
    const lon=(seam ? -180 : west)+(i%width+.5)*(seam ? 360 : east-west)/width;
    const col=((Math.floor((lon-west)/dx)%grid.width)+grid.width)%grid.width;
    const latitude=north-(Math.floor(i/width)+.5)*(north-south)/height;
    const row=polar ? Math.max(0,Math.min(grid.height-1,Math.floor((grid.latitudes[0]+dy/2-latitude)/dy))) : Math.floor(i/width);
    return grid.values[row*grid.width+col];
  }) : grid.values;
  return paintSstField({...grid,width,height,values,west:seam ? -180 : west,east:seam ? 180 : east,south,north,
    minimum:probabilistic ? 0 : grid.minimum,maximum:probabilistic ? 1 : grid.maximum,
    observation_id:'forecast',unit:probabilistic ? '1' : ''});
}
