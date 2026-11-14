from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal, localcontext
from pathlib import Path
from urllib.error import URLError
import io
import json
import zipfile
import h5py
import pytest
import earth_echo.connectors.marine_currents as module
from earth_echo.connectors.ranges import ArchivedRangeSource
from earth_echo.science.flow import mean_velocity_norm
from earth_echo.storage.products import publish, read_product

FIXTURE=Path(__file__).resolve().parents[3]/'data/samples/integrations/smoc-native-northwest-20261115.zip'
DAY=datetime(2026,11,14,tzinfo=timezone.utc)
NOW=DAY+timedelta(hours=22)


@pytest.fixture(scope='module')
def ranges():
    with zipfile.ZipFile(FIXTURE) as archive:return archive.read('smoc.ranges.json')


def test_authentic_native_cf_fields_bitwise_scope_depth_masks_and_time(ranges):
    products,raw=module.products_from_ranges(ranges,DAY,NOW,NOW)
    assert len(products)==6 and len({p.checksum_sha256 for p in products})==1
    assert all(p.source_id=='D14' and p.kind=='forecast' and p.representation=='field' and p.unit=='m/s' and p.samples==[] for p in products)
    assert all(p.observed_at is None and p.initialized_at is None and p.issued_at is None and p.valid_to is None and p.probability is None and not p.validated_for_use for p in products)
    assert all(p.valid_from.isoformat()=='2026-11-15T00:30:00+00:00' for p in products)
    assert products[0].grid.width==180 and products[0].grid.height==85 and products[0].grid.missing_cells==4425
    assert products[0].grid.longitudes==[x+.5 for x in range(-180,0)]
    assert products[0].grid.latitudes==[x+.5 for x in range(89,4,-1)]
    assert '0,494025' in products[0].coverage and 'time_bounds' in products[0].issue_time_basis
    source=ArchivedRangeSource(ranges)
    with source.open() as reader,h5py.File(reader,'r') as ds:
        # Original native Caribbean point, retained in the same chunks used
        # for the broad field; no pixels/values from an image or broker.
        assert float(ds['utotal'][0,0,1176,1104])==-.1220703125
        assert float(ds['vtotal'][0,0,1176,1104])==-.0732421875
        assert products[0].grid.values[71*180+93]==float(ds['utotal'][0,0,1182,1122])==-.3271484375
        assert products[0].grid.values[71*180+91] is None
        assert float(ds['utotal'][0,0,1182,1098])==float(ds['utotal'].attrs['_FillValue'][0])
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        manifest=json.loads(archive.read('manifest.json'))
        assert manifest['native_metadata']['native_values_bitwise_checked']==8_812_800
        assert manifest['assets']['smoc.ranges.json']['original_object_bytes']==922_430_398
        assert manifest['assets']['smoc.ranges.json']['retained_range_bytes']==8_858_558
        assert manifest['assets']['smoc.ranges.json']['range_blocks']==68


def test_mean_vector_norm_is_distinct_missing_zero_and_independently_calculated(ranges):
    products,_=module.products_from_ranges(ranges,DAY,NOW,NOW)
    u,v,_,_,speed,_=products
    index=71*180+93
    with localcontext() as context:
        context.prec=50
        a,b=[Decimal(str(p.grid.values[index])) for p in (u,v)]
        assert abs(speed.grid.values[index]-float((a*a+b*b).sqrt()))<1e-15
    assert speed.calculation.formula=='sqrt(mean(u)² + mean(v)²)'
    assert [i.product_id for i in speed.calculation.inputs]==[u.id,v.id]
    assert speed.grid.missing_cells==4425 and 0 in speed.grid.values
    assert mean_velocity_norm(-3,4)==5 and mean_velocity_norm(0,0)==0
    assert mean_velocity_norm(None,4) is None and mean_velocity_norm(float('nan'),4) is None
    assert any(x is not None and x<0 for x in u.grid.values)


def test_authentic_global_surface_scope_east_south_and_shared_original():
    with zipfile.ZipFile(FIXTURE.with_name('smoc-native-global-20261115.zip')) as archive:ranges=archive.read('smoc.ranges.json')
    products,raw=module.products_from_ranges(ranges,DAY,NOW,NOW,worldwide=True)
    assert len(products)==6 and all(p.grid.width==360 and p.grid.height==170 and p.grid.missing_cells==18585 for p in products)
    assert all(p.grid.west==-180 and p.grid.east==180 and p.grid.south==-80 and p.grid.north==90 for p in products)
    assert products[0].method_version==module.GLOBAL_METHOD and 'mundial' in products[0].coverage
    assert all(p.kind=='forecast' and not p.validated_for_use and p.probability is None for p in products)
    source=ArchivedRangeSource(ranges)
    with source.open() as reader,h5py.File(reader,'r') as ds:
        assert products[0].grid.values[110*360+260]==float(ds['utotal'][0,0,714,3126])
        assert products[0].grid.values[110*360+39]==float(ds['utotal'][0,0,714,474])
        assert products[0].grid.values[71*360+93]==-.3271484375
    assert products[4].grid.maximum==2.180754151044396
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:m=json.loads(archive.read('manifest.json'))
    assert m['native_metadata']['native_values_bitwise_checked']==35_268_480
    assert m['assets']['smoc.ranges.json']['range_blocks']==234
    assert m['assets']['smoc.ranges.json']['retained_range_bytes']==30_616_510
    assert len({p.checksum_sha256 for p in products})==1


@pytest.mark.parametrize(('variable','key','bad'),[('utotal','units',b'km h-1'),('time','calendar',b'360_day'),('depth','positive',b'Up'),('utotal','scale_factor',.01)])
def test_changed_scientific_metadata_refused_with_authentic_values(ranges,monkeypatch,variable,key,bad):
    original=module.h5py.File
    class Dataset:
        def __init__(self,raw):self.raw=raw;self.attrs={**dict(raw.attrs),key:bad}
        def __getattr__(self,name):return getattr(self.raw,name)
        def __getitem__(self,index):return self.raw[index]
    class Group:
        def __init__(self,raw):self.raw=raw;self.attrs=raw.attrs
        def __getitem__(self,name):return Dataset(self.raw[name]) if name==variable else self.raw[name]
    @contextmanager
    def altered(*args,**kwargs):
        with original(*args,**kwargs) as raw:yield Group(raw)
    monkeypatch.setattr(module.h5py,'File',altered)
    with pytest.raises(ValueError,match='changed|unexpected scale/offset'):
        module.products_from_ranges(ranges,DAY,NOW,NOW)


def test_strong_native_object_identity_and_date_required(ranges):
    changed=json.loads(ranges);changed['etag']=None
    with pytest.raises(ValueError,match='strong object version'):
        module.products_from_ranges(json.dumps(changed).encode(),DAY,NOW,NOW)
    with pytest.raises(ValueError,match='native URL'):
        module.products_from_ranges(ranges,DAY-timedelta(days=1),NOW,NOW)


def test_replayed_ingestion_no_duplicates_version_check_failure_and_recovery(ranges,tmp_path,monkeypatch):
    # Production now covers the global model ocean. The northwest fixture
    # above remains frozen for replay of the earlier qualified scope.
    with zipfile.ZipFile(FIXTURE.with_name('smoc-native-global-20261115.zip')) as archive:ranges=archive.read('smoc.ranges.json')
    offline=False;heads=[]
    def source(url,**kwargs):
        heads.append((url,kwargs))
        if offline:raise URLError('controlled native HEAD outage')
        assert url==module.scientific_url(DAY)
        return ArchivedRangeSource(ranges)
    monkeypatch.setattr(module,'RangeSource',source)
    monkeypatch.setattr(module,'products_root',lambda:tmp_path)
    monkeypatch.setattr(module,'publish',lambda p,raw,suffix:publish(p,raw,suffix,tmp_path))
    assert module.fetch_marine_currents(NOW)=='stored'
    before=read_product('d14-smoc-u-total',tmp_path)
    assert module.fetch_marine_currents(NOW+timedelta(hours=1))=='unchanged'
    assert len(list(tmp_path.glob('shared/*.zip')))==1 and len(list(tmp_path.glob('*/revisions/*.json')))==6
    assert read_product(before.id,tmp_path).retrieved_at==before.retrieved_at
    assert heads[0][1]=={'max_bytes':41_943_040,'max_requests':320,'deadline_seconds':540}
    offline=True
    with pytest.raises(URLError):module.fetch_marine_currents(NOW)
    assert read_product(before.id,tmp_path)==before and before.data_mode=='real'
    offline=False
    assert module.fetch_marine_currents(NOW)=='unchanged'
