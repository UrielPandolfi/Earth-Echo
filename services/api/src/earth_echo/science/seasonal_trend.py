"""Seasonal fixed-effects trend, preserving calendar gaps in residual blocks.

The legacy method stays unchanged for reproducibility of the SST experiment.
"""
import math
import random
from dataclasses import dataclass

from earth_echo.science.series import MonthValue,PRACTICAL_CHANGE_PER_YEAR
from earth_echo.science.associations import pearson

METHOD_ID='sst-seasonal-fixed-effects-calendar-block-v2'
METHOD_VERSION='2'
MIN_MONTHS=96
MIN_PER_MONTH=6
BOOTSTRAP_DRAWS=1000
SEED=20261115
PRIMARY_BLOCK=12
SENSITIVITY_BLOCK=24
MIN_BLOCK_STARTS=8


@dataclass(frozen=True)
class CalendarTrend:
    status: str
    reason: str | None
    slope_per_year: float | None
    interval_low: float | None
    interval_high: float | None
    present_months: int
    missing_months: int
    expected_months: int
    includes_zero: bool | None
    practical_threshold_exceeded: bool | None
    sensitivity_low: float | None=None
    sensitivity_high: float | None=None
    valid_draws: int=0
    sensitivity_valid_draws: int=0
    residual_lag1_r: float | None=None


def _fit(months,values):
    times=[m.year-2014+(m.month-.5)/12 for m in months]
    groups={month:[i for i,m in enumerate(months) if m.month==month and values[i] is not None] for month in range(1,13)}
    if any(len(ids)<MIN_PER_MONTH for ids in groups.values()):return None
    means={month:(math.fsum(times[i] for i in ids)/len(ids),math.fsum(values[i] for i in ids)/len(ids)) for month,ids in groups.items()}
    dt=[times[i]-means[m.month][0] if values[i] is not None else None for i,m in enumerate(months)]
    denominator=math.fsum(t*t for t in dt if t is not None)
    if not denominator:return None
    slope=math.fsum(dt[i]*(values[i]-means[m.month][1]) for i,m in enumerate(months) if values[i] is not None)/denominator
    fitted=[means[m.month][1]+slope*(times[i]-means[m.month][0]) for i,m in enumerate(months)]
    return slope,fitted


def _interval(months,values,fitted,residuals,length):
    starts=[i for i in range(len(months)-length+1) if all(v is not None for v in residuals[i:i+length])]
    if len(starts)<MIN_BLOCK_STARTS:return None,None,0
    generator=random.Random(SEED+length)
    slopes=[]
    for _ in range(BOOTSTRAP_DRAWS):
        drawn=[]
        while len(drawn)<len(months):
            start=generator.choice(starts)
            drawn.extend(residuals[start:start+length])
        # Keep the original mask AND calendar positions. We never concatenate
        # present months before defining blocks or calculating time distances.
        synthetic=[None if value is None else fitted[i]+drawn[i] for i,value in enumerate(values)]
        fit=_fit(months,synthetic)
        if fit is not None:slopes.append(fit[0])
    slopes.sort()
    if len(slopes)<900:return None,None,len(slopes)
    return slopes[int(.025*(len(slopes)-1))],slopes[int(.975*(len(slopes)-1))],len(slopes)


def estimate_calendar_trend(months:list[MonthValue]):
    indices=[m.year*12+m.month-1 for m in months]
    if indices and indices!=list(range(indices[0],indices[-1]+1)):raise ValueError('Trend requires dense ordered calendar months, including gaps')
    values=[]
    for m in months:
        if not 1<=m.month<=12 or m.expected_days<=0 or not 0<=m.present_days<=m.expected_days:raise ValueError('Invalid monthly trend support')
        values.append(m.value if m.value is not None and math.isfinite(m.value) and m.present_days/m.expected_days>=.8 else None)
    present=sum(v is not None for v in values);missing=len(months)-present
    if present<MIN_MONTHS:
        return CalendarTrend('not_evaluable',f'Hay{present}meses válidos; mínimo{MIN_MONTHS}.',None,None,None,present,missing,len(months),None,None)
    fit=_fit(months,values)
    if fit is None:return CalendarTrend('not_evaluable','No hay al menos seis años por mes calendario para el ajuste estacional.',None,None,None,present,missing,len(months),None,None)
    slope,fitted=fit
    residuals=[None if v is None else v-f for v,f in zip(values,fitted,strict=True)]
    low,high,valid=_interval(months,values,fitted,residuals,PRIMARY_BLOCK)
    sensitivity_low,sensitivity_high,sensitivity_valid=_interval(months,values,fitted,residuals,SENSITIVITY_BLOCK)
    adjacent=[(a,b) for a,b in zip(residuals,residuals[1:]) if a is not None and b is not None]
    lag1=pearson([a for a,_ in adjacent],[b for _,b in adjacent]) if adjacent else None
    return CalendarTrend('evaluated',None if low is not None else 'Pendiente evaluada; no hay bloques calendario completos suficientes para intervalo.',slope,low,high,present,missing,len(months),
        None if low is None else low<=0<=high,abs(slope)>=PRACTICAL_CHANGE_PER_YEAR,
        sensitivity_low,sensitivity_high,valid,sensitivity_valid,lag1)


def explain_calendar(estimate):
    if estimate.slope_per_year is None:return estimate.reason or 'Tendencia no evaluable.'
    text=f'Pendiente histórica común a los doce meses: {estimate.slope_per_year:.3f} °C/año, con ciclo estacional ajustado.'
    if estimate.interval_low is not None:
        text+=f' Intervalo condicional del 95 % con bloques de 12 meses: {estimate.interval_low:.3f} a {estimate.interval_high:.3f} °C/año.'
    else:text+=' Intervalo no evaluable por soporte de bloques insuficiente.'
    return text+' No es un pronóstico. No identifica la causa.'
