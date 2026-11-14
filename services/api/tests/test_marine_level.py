from contextlib import contextmanager
from datetime import datetime,timedelta,timezone
from pathlib import Path
from urllib.error import URLError
import io
import json
import zipfile
import h5py
import numpy as np
import pytest
import earth_echo.connectors.marine_level as module
from earth_echo.connectors.ranges import ArchivedRangeSource
from earth_echo.storage.products import publish,read_product

FIXTURE=Path(__file__).resolve().parents[3]/'data/samples/integrations/marine-mol-20261115.zip'
DAY=datetime(2026,11,14,tzinfo=timezone.utc)
NOW=DAY+timedelta(hours=22)


@pytest.fixture(scope='module')
def ranges():
    with zipfile.ZipFile(FIXTURE) as archive:return archive.read('mol.ranges.json')


def test_authentic_native_datum_components_masks_quantized_axes_and_cf_epoch(ranges):
    products,raw=module.products_from_ranges(ranges,DAY,NOW,NOW)
    assert len(products)==4 and len({p.checksum_sha256 for p in products})==1
    assert all(p.source_id=='D14' and p.kind=='forecast' and p.representation=='field' and p.unit=='m' and p.samples==[] for p in products)
    assert all(all(getattr(p,k) is None for k in ('observed_at','initialized_at','issued_at','valid_to','probability')) for p in products)
    assert all(p.valid_from==datetime(2026,11,15,0,30,tzinfo=timezone.utc) and not p.validated_for_use for p in products)
    assert all(p.grid.missing_cells==4425 and (p.grid.width,p.grid.height)==(180,85) for p in products)
    assert products[0].variable=='total_sea_level / sea_surface_height_above_geoid'
    assert [p.grid.minimum for p in products]==[-3.8349609375,-.28125,-1.1162109375,-3.416015625]
    source=ArchivedRangeSource(ranges)
    with source.open() as reader,h5py.File(reader,'r') as ds:
        assert float(ds['total_sea_level'][0,0,1176,1104])==.1396484375
        assert float(ds['invert_barometer'][0,0,1176,1104])==-.0224609375
        assert products[0].grid.values[71*180+93]==float(ds['total_sea_level'][0,0,1182,1122])
        assert products[0].grid.values[71*180+91] is None
        assert float(ds['longitude'][-1])==179.9169921875
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:m=json.loads(archive.read('manifest.json'))
    native=m['native_metadata'];check=native['component_closure']
    assert native['native_values_bitwise_checked']==13_219_200 and check['joint_centers_checked']==1_565_400
    assert check['maximum_absolute_residual_m']==.0016661137342453003
    assert native['native_auxiliary_depth_m']==.494140625
    # Native coordinate valid_max preceded quantization; preserve discrepancy,
    # do not derive another regular axis from that stale attribute.
    assert native['actual_last_longitude']>native['longitude_valid_max_attribute']
    assert m['assets']['mol.ranges.json']['original_object_bytes']==469_785_711
    assert 'no datum local' in products[0].limitation and 'No es GTSM D41' in products[0].limitation


def test_closure_uses_native_precision_joint_mask_and_valid_zero(ranges):
    source=ArchivedRangeSource(ranges)
    with source.open() as reader,h5py.File(reader,'r') as ds:
        fields={k:ds[k][0,0,1176:1178,1104:1106] for k in (*module.VARIABLES,*module.OFFSETS)}
    assert module.closure(fields)['joint_centers_checked']==4
    fields['total_sea_level'][0,0]+=.01
    with pytest.raises(ValueError,match='quantization budget'):module.closure(fields)
    fields={k:np.zeros((2,2),dtype='f4') for k in fields}
    assert module.closure(fields)['maximum_absolute_residual_m']==0
    fields['ocean_tide'][0,0]=-9999;fields['invert_barometer'][0,1]=np.nan
    assert module.closure(fields)['joint_centers_checked']==2


@pytest.mark.parametrize(('variable','key','bad'),[('total_sea_level','standard_name',b'sea_surface_height_above_sea_level'),('invert_barometer','units',b'cm'),('ocean_tide','least_significant_digit',2)])
def test_changed_datum_unit_or_precision_rejected(ranges,monkeypatch,variable,key,bad):
    original=module.h5py.File
    class Dataset:
        def __init__(self,raw):self.raw=raw;self.attrs={**dict(raw.attrs),key:bad}
        def __getattr__(self,name):return getattr(self.raw,name)
    class Group:
        def __init__(self,raw):self.raw=raw;self.attrs=raw.attrs
        def __getitem__(self,name):return Dataset(self.raw[name]) if name==variable else self.raw[name]
    @contextmanager
    def altered(*args,**kwargs):
        with original(*args,**kwargs) as ds:yield Group(ds)
    monkeypatch.setattr(module.h5py,'File',altered)
    with pytest.raises(ValueError,match='units/precision/mask/meaning changed'):
        module.products_from_ranges(ranges,DAY,NOW,NOW)


def test_shared_native_ingestion_no_duplicates_head_failure_and_recovery(ranges,tmp_path,monkeypatch):
    offline=False;heads=[]
    def source(url,**kwargs):
        heads.append((url,kwargs))
        if offline:raise URLError('controlled MOL HEAD outage')
        assert url==module.scientific_url(DAY)
        return ArchivedRangeSource(ranges)
    monkeypatch.setattr(module,'RangeSource',source)
    monkeypatch.setattr(module,'products_root',lambda:tmp_path)
    monkeypatch.setattr(module,'publish',lambda p,raw,suffix:publish(p,raw,suffix,tmp_path))
    assert module.fetch_marine_level(NOW)=='stored'
    before=read_product('d14-mol-total',tmp_path)
    assert module.fetch_marine_level(NOW+timedelta(minutes=1))=='unchanged'
    assert len(list(tmp_path.glob('shared/*.zip')))==1 and len(list(tmp_path.glob('*/revisions/*.json')))==4
    assert read_product(before.id,tmp_path).retrieved_at==before.retrieved_at
    assert heads[0][1]=={'max_bytes':12_582_912,'max_requests':96,'deadline_seconds':240}
    offline=True
    with pytest.raises(URLError):module.fetch_marine_level(NOW)
    assert read_product(before.id,tmp_path)==before and before.data_mode=='real'
    offline=False
    assert module.fetch_marine_level(NOW)=='unchanged'
