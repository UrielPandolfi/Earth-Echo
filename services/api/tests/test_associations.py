import csv
import io
import json
import math
from dataclasses import replace
from datetime import datetime,timedelta,timezone

import numpy as np
import pytest
from fastapi.testclient import TestClient

from earth_echo.science.associations import QuarterPair,analyze_pairs,pearson
from earth_echo.ingest import associations as ingest
from earth_echo.queries import associations as query


def synthetic(shared_trend=False):
    rows=[]
    for i in range(48):
        q=i%4+1
        x=20+i*.3+q*2+math.sin(i*1.7)
        y=25+i*.6+q*4+(math.cos(i*2.31) if shared_trend else 2*math.sin(i*1.7))
        rows.append(QuarterPair(2014+i//4,q,x,y))
    return rows


def test_shared_seasonal_cycle_and_trend_do_not_become_a_causal_connection():
    result=analyze_pairs(synthetic(shared_trend=True))
    assert result['status']=='evaluated' and result['raw_r']>.98
    assert abs(result['residual_r'])<.2
    assert all(i['low']<=0<=i['high'] for i in result['intervals'])


def test_known_residual_association_and_reproducible_paired_intervals():
    first=analyze_pairs(synthetic())
    assert first['residual_r']==pytest.approx(1)
    assert all(i['low']==pytest.approx(1) and i['high']==pytest.approx(1) for i in first['intervals'])
    assert analyze_pairs(synthetic())==first
    assert pearson([1,1],[2,3]) is None
    # A common exact linear/seasonal signal leaves no residual variation.
    pure=[QuarterPair(2014+i//4,i%4+1,float(i),float(i*2)) for i in range(48)]
    result=analyze_pairs(pure)
    assert result['status']=='not_evaluable' and result['residual_r'] is None


def test_missing_quarters_stay_on_calendar_axis_and_short_series_is_unavailable():
    rows=synthetic()
    rows[7]=replace(rows[7],x=None)
    result=analyze_pairs(rows)
    assert result['n_pairs']==47 and result['missing_pairs']==1
    assert (2015,4) not in result['residuals']
    with pytest.raises(ValueError,match='calendar axis'):
        analyze_pairs(rows[:7]+rows[8:])
    short=analyze_pairs(rows[:20])
    assert short['status']=='not_evaluable' and short['raw_r'] is None


def test_real_native_inputs_svd_persistence_csv_and_failure_preserve_previous(tmp_path,monkeypatch):
    now=datetime(2026,11,15,tzinfo=timezone.utc)
    view=ingest.build_associations(now)
    enso,amoc=view.pairs
    assert enso.n_pairs==48 and amoc.n_pairs==40
    assert enso.residual_r==pytest.approx(.2440726751414497,abs=1e-11)
    assert amoc.raw_r==pytest.approx(.5719222320644041,abs=1e-11)
    assert amoc.residual_r==pytest.approx(.18973352776258728,abs=1e-11)
    assert all(a.end==b.start for a,b in zip(enso.points,enso.points[1:]))
    assert enso.x_unit=='°C (RONI)' and amoc.x_unit=='Sv'
    assert all(i.low<0<i.high for p in view.pairs for i in p.intervals)
    assert 'matemático' in enso.warnings[-1]
    assert view.causal_attribution=='not_identified' and view.predictive_validation=='not_a_forecast'
    folder=tmp_path/'analyses/associations'
    monkeypatch.setattr(ingest,'analysis_dir',lambda:folder)
    monkeypatch.setattr(ingest,'build_associations',lambda moment:view.model_copy(update={'computed_at':moment}))
    assert ingest.derive_associations(now)=='stored'
    assert ingest.derive_associations(now+timedelta(days=1))=='unchanged'
    saved=json.loads((folder/'current.json').read_bytes())
    assert saved['computed_at']==view.model_dump(mode='json')['computed_at']
    assert len(list((folder/'revisions').iterdir()))==1
    monkeypatch.setattr(query,'analysis_dir',lambda:folder)
    assert query.association_view().execution_id==view.execution_id
    output=list(csv.DictReader(io.StringIO(query.association_csv('amoc-sst'))))
    assert len(output)==40 and output[0]['x_unit']=='Sv'
    assert output[0]['execution_id']==view.execution_id
    def failed(moment):raise OSError('Missing scientific input')
    monkeypatch.setattr(ingest,'build_associations',failed)
    with pytest.raises(OSError):ingest.derive_associations(now)
    assert json.loads((folder/'current.json').read_bytes())==saved
    monkeypatch.setattr(query,'read_product',lambda key:None)
    assert len(query.association_view().stale_inputs)==3
    assert query.association_view().pairs[0].n_pairs==48


def test_api_missing_analysis_is_real_unavailable_and_csv_has_no_fallback(tmp_path,monkeypatch):
    from earth_echo.api.app import create_app
    monkeypatch.setattr(query,'analysis_dir',lambda:tmp_path/'none')
    client=TestClient(create_app())
    response=client.get('/v1/analyses/associations')
    assert response.status_code==200 and response.json()['status']=='unavailable'
    assert response.json()['data_mode']=='real' and response.json()['pairs']==[]
    assert client.get('/v1/analyses/associations/amoc-sst.csv').status_code==404
    assert client.get('/v1/analyses/associations/random.csv').status_code==422
