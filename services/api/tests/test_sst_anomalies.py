import json
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from earth_echo.science.anomalies import seasonal_departures,THRESHOLD,MAD_FACTOR
from earth_echo.science.series import MonthValue
from earth_echo.ingest import sst_anomalies as ingest
from earth_echo.queries import anomalies as query
from earth_echo.storage.products import publish,read_product


def reference():
    return [MonthValue(y,m,20+(y-2014),30,30) for y in range(2014,2022) for m in range(1,13)]


def test_frozen_seasonal_reference_no_leakage_and_exact_threshold():
    base=reference()
    limit=23.5+THRESHOLD*2/MAD_FACTOR  # Median23.5, MAD2.
    rows=seasonal_departures(base+[MonthValue(2022,1,limit,30,30),MonthValue(2022,2,40,30,30)])
    assert all(r.modified_z is None and r.classification=='reference' for r in rows[:96])
    assert rows[-1].median_c==23.5 and rows[-1].mad_c==2
    assert rows[-1].classification=='warm_departure'
    # Boundary is strictly greater; floating arithmetic compared with the formula.
    assert rows[-2].modified_z==pytest.approx(3.5)
    mutated=seasonal_departures(base+[MonthValue(2022,1,100,30,30)])
    assert mutated[-1].median_c==23.5 and mutated[-1].mad_c==2


def test_gaps_short_reference_and_zero_mad_never_become_zero_score():
    base=reference()
    base=[replace(m,value=None) if (m.year,m.month)==(2014,1) else m for m in base]
    base=[replace(m,value=20) if m.month==2 else m for m in base]
    rows=seasonal_departures(base+[MonthValue(2022,1,30,30,30),MonthValue(2022,2,30,30,30),MonthValue(2022,3,30,20,30),MonthValue(2022,4,0,30,30)])
    assert rows[-4].reference_n==7 and rows[-4].modified_z is None
    assert rows[-3].mad_c==0 and rows[-3].modified_z is None
    assert rows[-3].departure_c==10 and rows[-3].classification=='not_evaluable'
    assert rows[-2].sst_c is None and rows[-2].departure_c is None
    assert rows[-1].sst_c==0 and rows[-1].classification=='cold_departure'
    with pytest.raises(ValueError,match='Duplicate'):
        seasonal_departures(reference()+[reference()[0]])


def test_actual_native_history_independent_check_idempotence_and_input_failure(tmp_path,monkeypatch):
    product,raw=ingest.build_sst_anomalies(datetime(2026,11,15,tzinfo=timezone.utc))
    assert len(product.samples)==144 and product.unit=='°C'
    assert sum(s.category=='warm_departure' for s in product.samples)==9
    assert sum(s.category=='cold_departure' for s in product.samples)==0
    assert sum(s.attributes['modified_z'] is not None for s in product.samples)==48
    assert product.extent.north==pytest.approx(17.55,abs=2e-6)
    assert product.extent.east==pytest.approx(-66.45,abs=2e-6)
    assert product.probability is None and not product.validated_for_use
    assert not any(s.map_eligible or s.longitude is not None for s in product.samples)
    root=tmp_path/'products'
    assert publish(product,raw,'.json',root)=='stored'
    assert publish(product.model_copy(update={'ingested_at':product.ingested_at+timedelta(days=1)}),raw,'.json',root)=='unchanged'
    assert len(list((root/product.id/'revisions').iterdir()))==1
    broken=json.loads(raw);broken['months'][0]['value']+=0.01
    with pytest.raises(ValueError,match='independent|Independent'):
        ingest.checked_history(broken)
    assert read_product(product.id,root).checksum_sha256==product.checksum_sha256
    monkeypatch.setattr(query,'read_product',lambda key:read_product(key,root))
    view=query.anomaly_view()
    assert view.status=='evaluated' and view.flagged_months==9 and view.assessed_months==48 and not view.stale_input
    monkeypatch.setattr(query,'series_path',lambda:tmp_path/'missing.json')
    assert query.anomaly_view().stale_input and query.anomaly_view().product is not None


def test_api_unavailable_is_explicit_without_demo_or_fabricated_counts(monkeypatch):
    from earth_echo.api.app import create_app
    monkeypatch.setattr(query,'read_product',lambda key:None)
    response=TestClient(create_app()).get('/v1/analyses/d15-anomalies')
    assert response.status_code==200
    assert response.json()['status']=='unavailable' and response.json()['product'] is None


def test_file_dependency_changes_trigger_analysis_without_waiting(tmp_path,monkeypatch):
    from earth_echo.ops import refresh
    path=tmp_path/'data/real/d15/monthly_series.json';path.parent.mkdir(parents=True);path.write_text('one')
    monkeypatch.setattr(refresh,'repo_root',lambda:tmp_path)
    monkeypatch.setattr(refresh,'DERIVED_FILE_INPUTS',{'analysis':('d15/monthly_series.json',)})
    first=refresh.input_revisions('analysis')
    path.write_text('two')
    assert refresh.input_revisions('analysis')!=first
    path.unlink()
    assert list(refresh.input_revisions('analysis').values())==['unavailable:FileNotFoundError']
