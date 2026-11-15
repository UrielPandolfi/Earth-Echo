import math
import csv
import io
from dataclasses import replace

import numpy as np
import pytest

from earth_echo.science.series import MonthValue
from earth_echo.science.seasonal_trend import estimate_calendar_trend
from earth_echo.queries import trend


def series():
    return [MonthValue(2014+i//12,i%12+1,20+2*math.sin((i%12)*math.pi/6)+.04*(i+.5)/12,30,30) for i in range(144)]


def test_known_common_trend_with_seasonal_cycle_and_calendar_gap_matches_svd():
    months=series()
    for i in (30,31,32):months[i]=replace(months[i],value=None,present_days=0)
    estimate=estimate_calendar_trend(months)
    assert estimate.status=='evaluated' and estimate.slope_per_year==pytest.approx(.04)
    assert estimate.present_months==141 and estimate.missing_months==3
    assert estimate.interval_low==pytest.approx(.04) and estimate.sensitivity_high==pytest.approx(.04)
    present=[m for m in months if m.value is not None]
    design=np.array([[float(m.month==month) for month in range(1,13)]+[m.year-2014+(m.month-.5)/12] for m in present])
    assert estimate.slope_per_year==pytest.approx(np.linalg.lstsq(design,[m.value for m in present],rcond=None)[0][-1],abs=1e-12)


def test_frequent_gaps_do_not_create_contiguous_blocks_or_fabricated_interval():
    months=[replace(m,value=None,present_days=0) if i%10==0 else m for i,m in enumerate(series())]
    estimate=estimate_calendar_trend(months)
    assert estimate.status=='evaluated' and estimate.slope_per_year==pytest.approx(.04)
    assert estimate.interval_low is None and estimate.interval_high is None
    assert estimate.valid_draws==0 and estimate.sensitivity_valid_draws==0
    assert estimate.includes_zero is None and 'calendario' in estimate.reason
    with pytest.raises(ValueError,match='calendar months'):
        estimate_calendar_trend(series()[:3]+series()[4:])


def test_zero_is_a_present_value_and_short_record_has_no_trend():
    constant=[replace(m,value=0) for m in series()]
    estimate=estimate_calendar_trend(constant)
    assert estimate.slope_per_year==0 and estimate.includes_zero
    assert estimate.interval_low==0 and estimate.residual_lag1_r is None
    short=estimate_calendar_trend(constant[:24])
    assert short.slope_per_year is None and short.interval_low is None


def test_real_trend_binds_input_hash_version_sensitivity_and_future_cutoff():
    trend._CACHE.clear()
    view=trend.trend_view()
    assert view.method_version=='2'
    assert view.slope_c_per_year==pytest.approx(.06815495337995334,abs=1e-12)
    assert view.bootstrap_valid_draws==view.sensitivity_valid_draws==1000
    assert view.residual_lag1_r==pytest.approx(.8437038716508659)
    assert view.region_extent.north==pytest.approx(17.55,abs=2e-6)
    assert view.source_series_sha256=='dba09d3d2a7bb9e4ecaf9b3fc99045b43de4e2867bc153125ac719885b258d60'
    assert trend.trend_view() is view
    future=trend.trend_view((2030,12))
    assert future.analysis_end=='2025-12' and future.expected_months==144
    assert future.slope_c_per_year==view.slope_c_per_year
    exported=list(csv.DictReader(io.StringIO(trend.trend_csv((2024,11)))))
    assert exported[-1]['year']=='2024' and exported[-1]['month']=='11'
    assert all(r['unit']=='°C' and r['method_version']=='2' and r['source_series_sha256']==view.source_series_sha256 for r in exported)


def test_wrong_region_has_no_reused_interval_and_corrupt_input_is_unavailable(tmp_path,monkeypatch):
    from earth_echo.api.app import create_app
    from fastapi.testclient import TestClient
    client=TestClient(create_app())
    body=client.get('/v1/analyses/d15-sst?region_id=amazonia').json()
    assert body['status']=='unavailable' and body['region_id']=='amazonia'
    assert body['slope_c_per_year'] is None and body['interval_low_c_per_year'] is None
    assert body['sensitivity_high_c_per_year'] is None and body['residual_lag1_r'] is None
    path=tmp_path/'bad.json';path.write_text('{invalid')
    monkeypatch.setattr(trend,'series_path',lambda:path)
    assert trend.trend_view().status=='unavailable'
