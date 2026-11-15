from datetime import datetime,timedelta,timezone
from pathlib import Path
import math

import netCDF4
import numpy as np
import pytest
from pydantic import ValidationError

from earth_echo.contracts.products import ScientificProduct
from earth_echo.ingest import oisst_anomaly as ingest
from earth_echo.science.field_aggregation import oisst_degree_means
from earth_echo.storage import products as store

FIXTURE=Path(__file__).resolve().parents[3]/'data/samples/integrations'


def original():
    return ScientificProduct.model_validate_json((FIXTURE/'oisst-anomaly-20261113-source.json').read_bytes()),(FIXTURE/'oisst-anomaly-20261113.nc').read_bytes()


def test_actual_full_native_anomaly_mask_axes_scale_and_area_view():
    source,raw=original()
    product=ingest.anomaly_from_source(source,raw,datetime(2026,11,15,tzinfo=timezone.utc))
    grid=product.grid
    assert grid.width==360 and grid.height==180
    assert grid.missing_cells==21333 and len(grid.values)-grid.missing_cells==43467
    assert grid.minimum==pytest.approx(-5.989118855798848,abs=1e-12)
    assert grid.maximum==pytest.approx(7.892959049413712,abs=1e-12)
    assert (grid.west,grid.east,grid.south,grid.north)==(-180,180,-90,90)
    assert grid.longitudes[0]==-179.5 and grid.latitudes[0]==89.5
    assert all((v is None)==(support<8) for v,support in zip(grid.values,grid.quality_values,strict=True))
    assert product.observed_at==source.observed_at and product.retrieved_at==source.retrieved_at
    assert product.raw_file==source.raw_file and product.probability is None
    assert product.kind=='indicator' and product.calculation is None and not product.samples
    with netCDF4.Dataset('native',memory=raw) as native:
        variable=native['anom'];masked=variable[0,0]
        variable.set_auto_maskandscale(False);encoded=variable[0,0]
        assert -1200<int(variable._FillValue)<1200
        assert np.ma.getmaskarray(masked)[encoded==-999].all()
        assert not np.ma.getmaskarray(masked)[encoded==0].any()


def test_area_weighting_zero_and_missing_support_are_explicit():
    native=np.ma.array(np.zeros((720,1440),dtype=np.float32),mask=np.zeros((720,1440),dtype=bool))
    lat=np.arange(720)*.25-89.875
    native[:4,:4]=np.repeat(np.arange(1,5),4).reshape(4,4)
    native.mask[:3,4:8]=True
    means,count=oisst_degree_means(native,lat)
    weights=[math.cos(math.radians(v)) for v in lat[:4]]
    expected=math.fsum((i+1)*w for i,w in enumerate(weights))/math.fsum(weights)
    assert float(means[0,0])==pytest.approx(expected)
    assert float(means[1,1])==0 and count[1,1]==16
    assert count[0,1]==4  # Consumer masks this display cell, never imputes it.


def test_one_shared_original_idempotent_replay_and_input_failure(tmp_path,monkeypatch):
    source,raw=original();now=datetime(2026,11,15,tzinfo=timezone.utc)
    monkeypatch.setattr(store,'products_root',lambda:tmp_path)
    monkeypatch.setattr(ingest,'products_root',lambda:tmp_path)
    assert store.publish(source,raw,'.nc')=='stored'
    assert ingest.derive_oisst_anomaly(now)=='stored'
    assert ingest.derive_oisst_anomaly(now+timedelta(hours=1))=='unchanged'
    assert len(list(tmp_path.rglob('*.nc')))==1
    saved=store.read_product(ingest.PRODUCT_ID)
    assert len(list((tmp_path/ingest.PRODUCT_ID/'revisions').glob('*.json')))==1
    monkeypatch.setattr(ingest,'read_product',lambda key:None)
    with pytest.raises(ValueError,match='unavailable'):ingest.derive_oisst_anomaly(now)
    assert store.read_product(ingest.PRODUCT_ID).checksum_sha256==saved.checksum_sha256
    with pytest.raises(ValueError,match='checksum'):ingest.anomaly_from_source(source,raw+b'corrupt',now)
    with pytest.raises(ValueError,match='Qualified'):ingest.anomaly_from_source(source.model_copy(update={'unit':'K'}),raw,now)


def test_centered_colors_require_a_finite_linear_unreversed_scale():
    source,raw=original();grid=ingest.anomaly_from_source(source,raw,datetime(2026,11,15,tzinfo=timezone.utc)).grid
    assert grid.color_center==0
    for changed in ({'color_center':float('nan')},{'color_scale':'log10'},{'reverse_colors':True}):
        with pytest.raises(ValidationError):type(grid).model_validate({**grid.model_dump(),**changed})
