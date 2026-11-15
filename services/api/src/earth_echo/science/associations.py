"""Prespecified, contemporaneous associations; no lag search or causal model."""
import math
import random
from dataclasses import dataclass

METHOD='quarterly-seasonal-detrended-paired-block-correlation-v1'
MIN_PAIRS=32
MIN_PER_QUARTER=6
DRAWS=1000
SEED=20261115
BLOCKS=(4,8)


@dataclass(frozen=True)
class QuarterPair:
    year: int
    quarter: int
    x: float | None
    y: float | None


def pearson(x,y,*,floor=1e-12):
    if len(x)!=len(y) or len(x)<2:return None
    mx=math.fsum(x)/len(x);my=math.fsum(y)/len(y)
    dx=[v-mx for v in x];dy=[v-my for v in y]
    xx=math.fsum(v*v for v in dx);yy=math.fsum(v*v for v in dy)
    if xx<=len(x)*floor**2 or yy<=len(y)*floor**2:return None
    value=math.fsum(a*b for a,b in zip(dx,dy,strict=True))/math.sqrt(xx*yy)
    if abs(value)>1+1e-12:raise ArithmeticError('Invalid numerical correlation')
    return min(1.,max(-1.,value))


def seasonal_residuals(rows,values):
    """OLS with four quarter intercepts plus a common time slope (within fit)."""
    times=[r.year-2014+(r.quarter-0.5)/4 for r in rows]
    groups={q:[i for i,r in enumerate(rows) if r.quarter==q] for q in range(1,5)}
    if any(len(indices)<MIN_PER_QUARTER for indices in groups.values()):return None,None
    means={q:(math.fsum(times[i] for i in indices)/len(indices),math.fsum(values[i] for i in indices)/len(indices)) for q,indices in groups.items()}
    dt=[t-means[r.quarter][0] for r,t in zip(rows,times,strict=True)]
    dv=[v-means[r.quarter][1] for r,v in zip(rows,values,strict=True)]
    denominator=math.fsum(t*t for t in dt)
    if not denominator:return None,None
    slope=math.fsum(t*v for t,v in zip(dt,dv,strict=True))/denominator
    residuals=[v-(means[r.quarter][1]+slope*(t-means[r.quarter][0])) for r,t,v in zip(rows,times,values,strict=True)]
    return residuals,slope


def block_interval(dense,block,*,floor):
    """Resample calendar blocks of paired residuals, retaining internal gaps."""
    generator=random.Random(SEED+block)
    correlations=[]
    for _ in range(DRAWS):
        drawn=[]
        while len(drawn)<len(dense):
            start=generator.randrange(len(dense))
            drawn.extend(dense[(start+offset)%len(dense)] for offset in range(block))
        paired=[p for p in drawn[:len(dense)] if p is not None]
        if len(paired)<MIN_PAIRS:continue
        value=pearson([p[0] for p in paired],[p[1] for p in paired],floor=floor)
        if value is not None:correlations.append(value)
    correlations.sort()
    # Very incomplete/degenerate resamples do not yield a fabricated interval.
    if len(correlations)<900:return None,None,len(correlations)
    return correlations[int(.025*(len(correlations)-1))],correlations[int(.975*(len(correlations)-1))],len(correlations)


def analyze_pairs(pairs:list[QuarterPair]):
    keys=[r.year*4+r.quarter-1 for r in pairs]
    if not keys or keys!=list(range(keys[0],keys[-1]+1)) or any(not 1<=r.quarter<=4 for r in pairs):raise ValueError('Association input must retain a dense, ordered calendar axis')
    if any(v is not None and not math.isfinite(v) for r in pairs for v in (r.x,r.y)):raise ValueError('Nonfinite association input must be missing')
    present=[r for r in pairs if r.x is not None and r.y is not None]
    result={'status':'not_evaluable','reason':None,'n_pairs':len(present),'missing_pairs':len(pairs)-len(present),'raw_r':None,'residual_r':None,'slope_x_per_year':None,'slope_y_per_year':None,'residuals':{},'intervals':[]}
    if len(present)<MIN_PAIRS:
        result['reason']=f'At least {MIN_PAIRS} complete, non-overlapping quarters required'
        return result
    x=[r.x for r in present];y=[r.y for r in present]
    rx,sx=seasonal_residuals(present,x);ry,sy=seasonal_residuals(present,y)
    if rx is None or ry is None:
        result['reason']='At least six complete years per calendar quarter required'
        return result
    result.update(raw_r=pearson(x,y),slope_x_per_year=sx,slope_y_per_year=sy,
        residuals={(r.year,r.quarter):(a,b) for r,a,b in zip(present,rx,ry,strict=True)})
    floor=max(1.,max(abs(v) for v in x+y))*1e-12
    value=pearson(rx,ry,floor=floor)
    if value is None:
        result['reason']='Residual variation is zero or below numerical resolution; correlation undefined'
        return result
    dense=[result['residuals'].get((r.year,r.quarter)) for r in pairs]
    intervals=[]
    for block in BLOCKS:
        low,high,valid=block_interval(dense,block,floor=floor)
        intervals.append({'block_quarters':block,'low':low,'high':high,'valid_draws':valid,'draws':DRAWS})
    result.update(status='evaluated',residual_r=value,intervals=intervals)
    return result
