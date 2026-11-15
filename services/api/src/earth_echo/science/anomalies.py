"""Seasonal descriptive departures against a frozen, earlier reference."""
import math
from dataclasses import dataclass
from statistics import median

from earth_echo.science.series import MonthValue

METHOD='sst-seasonal-median-mad-reference-v1'
REFERENCE_FIRST=2014
REFERENCE_LAST=2021
MIN_REFERENCE_YEARS=8
THRESHOLD=3.5
MAD_FACTOR=0.6745
REFERENCE_URL='https://www.itl.nist.gov/div898/handbook/eda/section3/eda35h.htm'


@dataclass(frozen=True)
class Departure:
    year: int
    month: int
    sst_c: float | None
    reference_n: int
    median_c: float | None
    mad_c: float | None
    departure_c: float | None
    modified_z: float | None
    classification: str


def seasonal_departures(months: list[MonthValue]) -> list[Departure]:
    """No threshold fitting, reference leakage, probability or gap interpolation."""
    keys=[(m.year,m.month) for m in months]
    if len(set(keys))!=len(keys):
        raise ValueError('Duplicate calendar month in SST input')
    if keys!=sorted(keys) or any(not 1<=m.month<=12 for m in months):
        raise ValueError('SST months must be ordered calendar months')
    def present(m):
        if m.expected_days<=0 or not 0<=m.present_days<=m.expected_days:
            raise ValueError('Invalid monthly day support')
        return m.value if m.value is not None and math.isfinite(m.value) and m.present_days/m.expected_days>=0.8 else None
    values=[present(m) for m in months]
    references={}
    for month in range(1,13):
        baseline=[v for m,v in zip(months,values,strict=True) if REFERENCE_FIRST<=m.year<=REFERENCE_LAST and m.month==month and v is not None]
        center=median(baseline) if len(baseline)>=MIN_REFERENCE_YEARS else None
        mad=median([abs(v-center) for v in baseline]) if center is not None else None
        references[month]=(len(baseline),center,mad)
    rows=[]
    for m,value in zip(months,values,strict=True):
        count,center,mad=references[m.month]
        departure=None if value is None or center is None else value-center
        # Reference/pre-reference months are never evaluated as held-out cases.
        assess=m.year>REFERENCE_LAST and departure is not None and mad is not None and mad>0
        score=MAD_FACTOR*departure/mad if assess else None
        classification=('reference' if REFERENCE_FIRST<=m.year<=REFERENCE_LAST else 'before_reference' if m.year<REFERENCE_FIRST
            else 'missing' if value is None else 'not_evaluable' if score is None
            else 'warm_departure' if score>THRESHOLD else 'cold_departure' if score<-THRESHOLD else 'within_threshold')
        rows.append(Departure(m.year,m.month,value,count,center,mad,departure,score,classification))
    return rows
