from contextlib import contextmanager
from datetime import datetime,timedelta,timezone
from pathlib import Path
from urllib.error import URLError
import io
import json
import zipfile
import h5py
import pytest
import earth_echo.connectors.marine_salinity as module
from earth_echo.connectors.ranges import ArchivedRangeSource
from earth_echo.storage.products import publish,read_product

FIXTURE=Path(__file__).resolve().parents[3]/'data/samples/integrations/marine-so-20261115.zip'
DAY=datetime(2026,11,14,tzinfo=timezone.utc)
NOW=DAY+timedelta(hours=23)


@pytest.fixture(scope='module')
def ranges():
    with zipfile.ZipFile(FIXTURE) as archive:return archive.read('so.ranges.json')


def test_authentic_practical_salinity_native_unit_no_rescale_depth_time_and_mask(ranges):
    p,raw=module.product_from_ranges(ranges,DAY,NOW,NOW)
    assert raw==FIXTURE.read_bytes()
    assert p.source_id=='D14' and p.kind=='forecast' and p.representation=='field' and p.samples==[]
    assert p.unit=='1e-3' and 'Practical Salinity Unit' in p.native_unit and p.variable=='so / sea_water_salinity'
    assert all(getattr(p,k) is None for k in ('observed_at','initialized_at','issued_at','valid_to','probability'))
    assert p.valid_from==datetime(2026,11,15,tzinfo=timezone.utc) and not p.validated_for_use
    assert (p.grid.width,p.grid.height,p.grid.missing_cells)==(45,22,173)
    assert p.grid.minimum==13.31876277923584 and p.grid.maximum==37.74216842651367
    source=ArchivedRangeSource(ranges)
    with source.open() as reader,h5py.File(reader,'r') as ds:
        assert float(ds['so'][0,0,1176,1104])==29.603078842163086
        assert p.grid.values[8*45+3]==float(ds['so'][0,0,1182,1122])
        assert p.grid.latitudes[8]==float(ds['latitude'][1182])
        assert p.grid.longitudes[3]==float(ds['longitude'][1122])
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:m=json.loads(archive.read('manifest.json'))
    assert m['native_metadata']['native_values_bitwise_checked']==829440
    assert m['native_metadata']['native_valid_range']==[0,50]
    assert m['native_metadata']['native_unit_long']=='Practical Salinity Unit'
    assert m['assets']['so.ranges.json']['original_object_bytes']==682_017_165
    assert m['assets']['so.ranges.json']['range_blocks']==20


@pytest.mark.parametrize(('key','bad'),[('units',b'kg kg-1'),('unit_long',b'Absolute Salinity Unit'),('scale_factor',.001),('valid_min',.01)])
def test_changed_unit_definition_scale_or_zero_domain_rejected(ranges,monkeypatch,key,bad):
    original=h5py.File
    class Dataset:
        def __init__(self,raw):self.raw=raw;self.attrs={**dict(raw.attrs),key:bad}
        def __getattr__(self,name):return getattr(self.raw,name)
    class Group:
        def __init__(self,raw):self.raw=raw;self.attrs=raw.attrs
        def __getitem__(self,name):return Dataset(self.raw[name]) if name=='so' else self.raw[name]
    @contextmanager
    def altered(*args,**kwargs):
        with original(*args,**kwargs) as ds:yield Group(ds)
    monkeypatch.setattr(h5py,'File',altered)
    with pytest.raises(ValueError,match='changed'):module.product_from_ranges(ranges,DAY,NOW,NOW)


def test_salinity_cache_idempotence_strong_head_identity_outage_and_recovery(ranges,tmp_path,monkeypatch):
    offline=False;heads=[]
    def source(url,**kwargs):
        heads.append((url,kwargs))
        if offline:raise URLError('controlled salinity outage')
        assert url==module.scientific_url(DAY)
        return ArchivedRangeSource(ranges)
    monkeypatch.setattr(module,'RangeSource',source)
    monkeypatch.setattr(module,'products_root',lambda:tmp_path)
    monkeypatch.setattr(module,'publish',lambda p,raw,suffix:publish(p,raw,suffix,tmp_path))
    assert module.fetch_marine_salinity(NOW)=='stored'
    before=read_product(module.ID,tmp_path)
    assert module.fetch_marine_salinity(NOW+timedelta(minutes=1))=='unchanged'
    assert len(list(tmp_path.glob('shared/*.zip')))==1 and len(list(tmp_path.glob('*/revisions/*.json')))==1
    assert read_product(before.id,tmp_path).retrieved_at==before.retrieved_at
    assert heads[0][1]=={'max_bytes':8_388_608,'max_requests':64,'deadline_seconds':120}
    offline=True
    with pytest.raises(URLError):module.fetch_marine_salinity(NOW)
    assert read_product(before.id,tmp_path)==before and before.data_mode=='real'
    offline=False
    assert module.fetch_marine_salinity(NOW)=='unchanged'
