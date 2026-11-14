from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
import hashlib
import pytest
from earth_echo.science.transport_trend import annual_means,slope_per_decade

ROOT=Path(__file__).resolve().parents[3]


def monthly(year,month,value):
    return SimpleNamespace(time=datetime(year,month,15,tzinfo=timezone.utc),value=value)


def test_annual_calendar_weights_leap_year_missing_and_partial_boundaries():
    samples=[monthly(2004,m,100 if m==2 else 0) for m in range(1,13)]
    assert annual_means(samples,2004,2004)[0][1]==pytest.approx(100*29/366)
    assert annual_means(samples[:-1],2004,2004)==[(2004,None)]
    samples[0].value=None
    assert annual_means(samples,2004,2004)==[(2004,None)]
    with pytest.raises(ValueError,match='Duplicate transport month'):
        annual_means(samples+[samples[0]],2004,2004)
    # Partial boundary years are excluded by method design, regardless of values.
    assert annual_means(samples,2005,2005)==[(2005,None)]


def test_slope_known_line_and_insufficient_years():
    annual=[(y,12+.2*(y-2005)) for y in range(2005,2024)]
    assert slope_per_decade(annual)==pytest.approx(2)
    annual[3]=(2008,None)
    assert slope_per_decade(annual)==pytest.approx(2)
    with pytest.raises(ValueError,match='Insufficient complete years'):
        slope_per_decade(annual[:10])


def test_authentic_rapid_analysis_shares_raw_is_idempotent_and_preserves_last_valid(tmp_path,monkeypatch):
    from earth_echo.contracts.products import ScientificProduct
    from earth_echo.storage import products as storage
    from earth_echo.ingest import transport_trend as ingest
    from earth_echo.queries import products as queries
    raw=(ROOT/'data/samples/integrations/rapid-monthly.h5').read_bytes()
    sha=hashlib.sha256(raw).hexdigest()
    source=ScientificProduct.model_validate_json((ROOT/'data/real/products/d34-amoc-monthly/current.json').read_bytes())
    source=source.model_copy(update={'checksum_sha256':sha,'byte_size':len(raw),'raw_file':f'shared/{sha}.nc'})
    monkeypatch.setattr(storage,'products_root',lambda:tmp_path)
    monkeypatch.setattr(ingest,'products_root',lambda:tmp_path)
    storage.publish(source,raw,'.nc')
    now=datetime(2026,11,14,tzinfo=timezone.utc)
    assert ingest.derive_transport_trend(now)=='stored'
    product=storage.read_product('d34-amoc-annual-trend')
    assert len(product.samples)==19 and all(s.probability is None and s.longitude is None for s in product.samples)
    assert product.samples[0].time.year==2005 and product.samples[-1].valid_to.year==2024
    assert product.calculation.result.unit=='Sv/década' and product.validated_for_use is False
    assert product.raw_file==source.raw_file
    assert len(list((tmp_path/'shared').glob('*')))==1
    assert ingest.derive_transport_trend(now)=='unchanged'
    assert len(list((tmp_path/product.id/'revisions').glob('*')))==1
    # Source inconsistency blocks only this calculation; it cannot replace the valid result.
    original_month=source.samples[0].value
    source.samples[0].value=1000
    storage.atomic_json(tmp_path/source.id/'current.json',source.model_dump(mode='json'))
    with pytest.raises(ValueError,match='differs from native'):
        ingest.derive_transport_trend(now)
    assert storage.read_product(product.id)==product
    source.samples[0].value=original_month
    storage.atomic_json(tmp_path/source.id/'current.json',source.model_dump(mode='json'))
    assert ingest.derive_transport_trend(now)=='unchanged'
    monkeypatch.setattr(queries,'all_products',lambda:[source,product])
    monkeypatch.setattr(queries,'quake_layer',lambda:SimpleNamespace(count=0,retrieved_at=False))
    monkeypatch.setattr(queries,'kp_layer',lambda:SimpleNamespace(count=0,retrieved_at=False))
    count=queries.product_list(summaries=True)
    assert count.calculated_indicator_products==1 and count.calculated_field_products==0
    assert count.imported_indicator_records==0 and count.calculated_signals==0 and count.observation_records==0
    assert count.historical_records==248
