from pathlib import Path
from datetime import datetime, timezone
import pytest
from earth_echo.connectors.firms import decode_csv, verify_shape

ROOT=Path(__file__).resolve().parents[3]/'data/samples/integrations'


def test_authentic_viirs_units_quality_utc_and_independent_geometry():
    raw=(ROOT/'firms-noaa20.csv').read_bytes()
    samples,rows=decode_csv(raw)
    assert verify_shape((ROOT/'firms-noaa20.zip').read_bytes(),rows)==2
    first,low=samples
    assert first.value==.73 and first.longitude==-36.0171 and first.latitude==-8.18661
    assert first.time==datetime(2026,11,12,3,6,tzinfo=timezone.utc)
    assert first.map_eligible is True and first.probability is None
    assert low.value==42.69 and low.map_eligible is False
    assert low.longitude is not None and low.attributes['confidence']=='low'
    assert first.attributes['bright_ti4']=='298.32' and first.attributes['bright_ti4_ti5_unidad'].startswith('K,')
    changed=[{**rows[0],'frp':'10'},rows[1]]
    with pytest.raises(ValueError,match='scientific values'):
        verify_shape((ROOT/'firms-noaa20.zip').read_bytes(),changed)
    # Repeated native rows have stable identity; no invented event counter.
    duplicated=raw+raw.splitlines(keepends=True)[1]
    assert len(decode_csv(duplicated)[0])==2


def test_missing_frp_is_not_zero_and_bad_csv_is_not_demo():
    raw=(ROOT/'firms-noaa20.csv').read_bytes()
    samples,_=decode_csv(raw.replace(b',0.73,',b',-999.0,'))
    assert samples[0].value is None and samples[0].map_eligible is False
    assert decode_csv(raw.splitlines(keepends=True)[0])==([],[])
    with pytest.raises(ValueError,match='scientific CSV'):
        decode_csv(b'<html>login</html>')
    with pytest.raises(ValueError,match='native quality'):
        decode_csv(raw.replace(b',nominal,',b',certain,'))


def test_historical_aggregates_and_static_context_do_not_inflate_observation_counter(monkeypatch):
    from types import SimpleNamespace
    from earth_echo.queries import products as queries
    from earth_echo.contracts.products import ScientificProduct
    root=ROOT.parents[1]/'real/products'
    # Actual retained metadata, independent of whether the large raw assets exist.
    products=[ScientificProduct.model_validate_json((root/key/'current.json').read_bytes()) for key in ['d19-desert-locust-surveys','d48-oni-history','d23-holocene-inventory']]
    monkeypatch.setattr(queries,'all_products',lambda:products)
    monkeypatch.setattr(queries,'quake_layer',lambda:SimpleNamespace(count=2,retrieved_at=True))
    monkeypatch.setattr(queries,'kp_layer',lambda:SimpleNamespace(count=1,retrieved_at=True))
    result=queries.product_list(summaries=True)
    assert result.observation_records==3+len(products[0].samples)
    assert result.historical_records==len(products[1].samples)
    assert all(not p.samples for p in result.products)
    assert result.calculated_signals==0 and result.catalog_phenomena==31


def test_firms_ingestion_is_idempotent_and_recovers_without_replacing_valid_data(tmp_path,monkeypatch):
    import json
    from urllib.error import URLError
    import earth_echo.connectors.firms as module
    from earth_echo.storage.products import publish,read_product
    csv_path='/data/active_fire/noaa-20-viirs-c2/csv/J1_VIIRS_C2_South_America_24h.csv'
    shp_path='/data/active_fire/noaa-20-viirs-c2/shapes/zips/J1_VIIRS_C2_South_America_24h.zip'
    index={'csv':{'noaa20':{'South America':[csv_path]}},'shp':{'noaa20':{'South America':[shp_path]}}}
    offline=False
    def download(url,**kwargs):
        if offline:raise URLError('offline verification')
        if url==module.INDEX:return json.dumps(index).encode(),{}
        return (ROOT/('firms-noaa20.csv' if url.endswith('.csv') else 'firms-noaa20.zip')).read_bytes(),{}
    monkeypatch.setattr(module,'download',download)
    monkeypatch.setattr(module,'publish',lambda p,raw,suffix:publish(p,raw,suffix,tmp_path))
    now=datetime(2026,11,14,tzinfo=timezone.utc)
    assert module.fetch_firms(now)=='stored'
    original=read_product('d06-viirs-noaa20-sa',tmp_path)
    assert module.fetch_firms(now)=='unchanged'
    offline=True
    with pytest.raises(URLError):module.fetch_firms(now)
    assert read_product(original.id,tmp_path)==original
    offline=False
    assert module.fetch_firms(now)=='unchanged'
    assert len(list(tmp_path.glob('*/revisions/*.json')))==1
