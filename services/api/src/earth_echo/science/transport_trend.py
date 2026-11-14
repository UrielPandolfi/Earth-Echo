"""Descriptive annual transport slope. No significance test or prediction."""
import calendar
import math
from collections import defaultdict


def annual_means(samples, first=2005, last=2023):
    months=defaultdict(dict)
    for sample in samples:
        if sample.time is None: raise ValueError('Monthly transport requires a time coordinate')
        year,month=sample.time.year,sample.time.month
        if not first<=year<=last: continue
        if month in months[year]: raise ValueError('Duplicate transport month')
        months[year][month]=sample.value
    annual=[]
    for year in range(first,last+1):
        values=months[year]
        if set(values)!=set(range(1,13)) or any(v is None for v in values.values()):
            annual.append((year,None));continue
        if any(not math.isfinite(v) for v in values.values()):raise ValueError('Nonfinite monthly transport')
        weights=[calendar.monthrange(year,month)[1] for month in range(1,13)]
        annual.append((year,math.fsum(values[m]*weights[m-1] for m in range(1,13))/sum(weights)))
    return annual


def slope_per_decade(annual, minimum_years=15):
    if minimum_years<2:raise ValueError('At least two years required for a slope')
    present=[(year,value) for year,value in annual if value is not None]
    if len(present)<minimum_years:raise ValueError('Insufficient complete years for descriptive slope')
    if len({year for year,_ in present})!=len(present):raise ValueError('Duplicate annual coordinate')
    if any(not math.isfinite(value) for _,value in present):raise ValueError('Nonfinite annual transport')
    mean_x=math.fsum(year for year,_ in present)/len(present)
    mean_y=math.fsum(value for _,value in present)/len(present)
    return 10*math.fsum((year-mean_x)*(value-mean_y) for year,value in present)/math.fsum((year-mean_x)**2 for year,_ in present)
