from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import URLError
import io
import json
import zipfile
import h5py
import pytest
import earth_echo.connectors.marine_temperature as module
from earth_echo.connectors.ranges import ArchivedRangeSource
from earth_echo.storage.products import publish, read_product

FIXTURE=Path(__file__).resolve().parents[3]/'data/samples/integrations/marine-thetao-20261115.zip'
DAY=datetime(2026,11,14,tzinfo=timezone.utc)
NOW=DAY+timedelta(hours=22)


@pytest.fixture(scope='module')
def ranges():
    with zipfile.ZipFile(FIXTURE) as archive:return archive.read('thetao.ranges.json')


def test_authentic_temperature_depth_axes_fill_and_instantaneous_cf_time(ranges):
    product,raw=module.product_from_ranges(ranges,DAY,NOW,NOW)
    assert raw==FIXTURE.read_bytes()  # shared decoder preserves archived bytes
    assert product.kind=='forecast' and product.representation=='field' and product.unit=='°C' and product.samples==[]
    assert product.variable=='thetao / sea_water_potential_temperature'
    assert all(getattr(product,k) is None for k in ('initialized_at','issued_at','observed_at','valid_to','probability'))
    assert product.valid_from==datetime(2026,11,15,tzinfo=timezone.utc)
    assert (product.grid.width,product.grid.height,product.grid.missing_cells)==(45,22,173)
    assert product.grid.minimum==25.270755767822266 and product.grid.maximum==32.51515197753906
    source=ArchivedRangeSource(ranges)
    with source.open() as reader,h5py.File(reader,'r') as ds:
        assert float(ds['thetao'][0,0,1176,1104])==29.254053115844727
        assert product.grid.values[8*45+3]==float(ds['thetao'][0,0,1182,1122])
        assert product.grid.longitudes[3]==float(ds['longitude'][1122])
        assert product.grid.latitudes[8]==float(ds['latitude'][1182])
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        m=json.loads(archive.read('manifest.json'))
        assert m['native_metadata']['native_values_bitwise_checked']==829440
        assert len(m['native_metadata']['native_depths_m'])==6
        assert m['native_metadata']['temporal_statistic']=='instantaneous'
        assert m['assets']['thetao.ranges.json']['original_object_bytes']==865_185_403
        assert m['assets']['thetao.ranges.json']['retained_range_bytes']<4_000_000
    assert 'no SST de piel' in product.limitation and not product.validated_for_use


@pytest.mark.parametrize(('key','bad'),[('units',b'K'),('standard_name',b'sea_surface_skin_temperature'),('scale_factor',.01)])
def test_changed_scientific_definition_is_rejected(ranges,monkeypatch,key,bad):
    original=h5py.File
    class Dataset:
        def __init__(self,raw):self.raw=raw;self.attrs={**dict(raw.attrs),key:bad}
        def __getattr__(self,name):return getattr(self.raw,name)
    class Group:
        def __init__(self,raw):self.raw=raw;self.attrs=raw.attrs
        def __getitem__(self,name):return Dataset(self.raw[name]) if name=='thetao' else self.raw[name]
    @contextmanager
    def altered(*args,**kwargs):
        with original(*args,**kwargs) as ds:yield Group(ds)
    monkeypatch.setattr(h5py,'File',altered)
    with pytest.raises(ValueError,match='units/layout/meaning changed'):
        module.product_from_ranges(ranges,DAY,NOW,NOW)


def test_retained_native_asset_no_duplicate_version_check_and_network_recovery(ranges,tmp_path,monkeypatch):
    offline=False;heads=[]
    def source(url,**kwargs):
        heads.append((url,kwargs))
        if offline:raise URLError('controlled temperature HEAD outage')
        assert url==module.scientific_url(DAY)
        return ArchivedRangeSource(ranges)
    monkeypatch.setattr(module,'RangeSource',source)
    monkeypatch.setattr(module,'products_root',lambda:tmp_path)
    monkeypatch.setattr(module,'publish',lambda p,raw,suffix:publish(p,raw,suffix,tmp_path))
    assert module.fetch_marine_temperature(NOW)=='stored'
    before=read_product(module.ID,tmp_path)
    assert module.fetch_marine_temperature(NOW+timedelta(minutes=1))=='unchanged'
    assert len(list(tmp_path.glob('shared/*.zip')))==1 and len(list(tmp_path.glob('*/revisions/*.json')))==1
    assert heads[0][1]=={'max_bytes':8_388_608,'max_requests':64,'deadline_seconds':120}
    assert read_product(before.id,tmp_path).retrieved_at==before.retrieved_at
    offline=True
    with pytest.raises(URLError):module.fetch_marine_temperature(NOW)
    assert read_product(before.id,tmp_path)==before and before.data_mode=='real'
    offline=False
    assert module.fetch_marine_temperature(NOW)=='unchanged'
