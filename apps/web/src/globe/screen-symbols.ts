/** Presentation only: visibility never changes records, groups or counts. */
export interface ScreenSymbol {
  id:string; x:number; y:number; facing:boolean; priority:number; width:number; height:number;
}

export function visibleSymbols(symbols:ScreenSymbol[],width:number,height:number,selected:string|null):Set<string> {
  const visible=new Set<string>();
  const cells=new Map<string,Array<{left:number;right:number;top:number;bottom:number}>>();
  const ordered=[...symbols].sort((a,b)=>Number(b.id===selected)-Number(a.id===selected)||b.priority-a.priority||a.id.localeCompare(b.id));
  for(const p of ordered){
    const box={left:p.x-p.width/2-2,right:p.x+p.width/2+2,top:p.y-p.height/2-2,bottom:p.y+p.height/2+2};
    if(!p.facing||!Number.isFinite(p.x)||!Number.isFinite(p.y)||box.left<8||box.right>width-8||box.top<54||box.bottom>height-78) continue;
    const keys:string[]=[];
    for(let x=Math.floor(box.left/64);x<=Math.floor(box.right/64);x++){
      for(let y=Math.floor(box.top/64);y<=Math.floor(box.bottom/64);y++) keys.push(`${x}:${y}`);
    }
    if(keys.some(key=>(cells.get(key)??[]).some(b=>box.left<b.right&&box.right>b.left&&box.top<b.bottom&&box.bottom>b.top))) continue;
    visible.add(p.id);
    for(const key of keys){const items=cells.get(key)??[];items.push(box);cells.set(key,items);}
  }
  return visible;
}
