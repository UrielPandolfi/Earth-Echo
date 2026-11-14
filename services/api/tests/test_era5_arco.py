from pathlib import Path
from datetime import datetime,timezone
import io,json,hashlib,zipfile,struct
import numpy as np
import pytest
from numcodecs import Blosc
from earth_echo.connectors.era5_arco import decode_archive,decode_chunk,archive_assets,VARIABLE

FIXTURE=Path(__file__).resolve().parents[3]/'data/samples/integrations/era5-arco.zip'


def unpack():
    with zipfile.ZipFile(FIXTURE) as z:files={name:z.read(name) for name in z.namelist()}
    return files,json.loads(files.pop('manifest.json'))


def replace_asset(files,manifest,name,data):
    files[name]=data
    manifest['assets'][name]['sha256']=hashlib.sha256(data).hexdigest()
    manifest['assets'][name]['bytes']=len(data)
    return archive_assets(files,manifest)


def test_authentic_stable_era5_cf_coordinates_units_and_complete_native_asset():
    grid,stamp,manifest,sha,expected,actual=decode_archive(FIXTURE.read_bytes())
    assert stamp==datetime(2026,6,30,tzinfo=timezone.utc)
    # Metadata validity starts in 1940, but the *coordinate* starts in 1900.
    assert manifest['time_index']==1108824
    assert (grid.width,grid.height)==(360,180) and grid.missing_cells==0
    assert grid.longitudes[:2]==[-179.5,-178.5] and grid.longitudes[-1]==179.5
    assert grid.latitudes[:2]==[89.5,88.5] and grid.latitudes[-1]==-89.5
    assert expected==pytest.approx(actual,abs=1e-12) and len(sha)==64
    assert grid.minimum<0<grid.maximum
    files,meta=unpack();name=f'{VARIABLE}/{manifest["time_index"]}.0.0'
    descriptor=json.loads(files[VARIABLE+'/.zarray'])
    native=decode_chunk(files[name],descriptor)
    assert native.shape==(1,721,1440)
    assert float(native[0,500,1192])==281.419677734375 # -35°, -62°
    broken=bytearray(files[name]);struct.pack_into('<I',broken,4,4_000_000_000)
    with pytest.raises(ValueError,match='size disagrees'):
        decode_chunk(bytes(broken),descriptor)


def test_missing_stays_missing_and_units_or_preliminary_time_are_rejected():
    files,manifest=unpack();name=f'{VARIABLE}/{manifest["time_index"]}.0.0'
    descriptor=json.loads(files[VARIABLE+'/.zarray'])
    data=decode_chunk(files[name],descriptor).copy()
    data[0,2,722]=np.nan # First display cell; no fake provider values are published.
    encoded=Blosc(cname='lz4',clevel=5,shuffle=1).encode(data)
    grid,*_=decode_archive(replace_asset(files,manifest,name,encoded))
    assert grid.values[0] is None and grid.missing_cells==1
    files,manifest=unpack();attrs=json.loads(files[VARIABLE+'/.zattrs']);attrs['units']='degC'
    altered=replace_asset(files,manifest,VARIABLE+'/.zattrs',json.dumps(attrs).encode())
    with pytest.raises(ValueError,match='units/dimensions'):decode_archive(altered)
    files,manifest=unpack();manifest['selected_time']='2026-11-01T00:00:00+00:00'
    with pytest.raises(ValueError,match='outside stable ERA5'):decode_archive(archive_assets(files,manifest))


def test_identity_ignores_other_preliminary_updates_but_keeps_selected_science():
    original=decode_archive(FIXTURE.read_bytes())[3]
    files,manifest=unpack();attrs=json.loads(files['.zattrs'])
    attrs['last_updated']='2026-11-15 00:00:00+00:00';attrs['valid_time_stop_era5t']='2026-11-09'
    assert decode_archive(replace_asset(files,manifest,'.zattrs',json.dumps(attrs).encode()))[3]==original
    files,manifest=unpack();attrs=json.loads(files[VARIABLE+'/.zattrs'])
    attrs['processing_note']='reviewed field metadata'
    assert decode_archive(replace_asset(files,manifest,VARIABLE+'/.zattrs',json.dumps(attrs).encode()))[3]!=original


def test_ingestion_is_idempotent_and_network_failure_preserves_valid_data(tmp_path,monkeypatch):
    from urllib.error import URLError
    import earth_echo.connectors.era5_arco as module
    from earth_echo.storage.products import publish,read_product
    files,manifest=unpack();offline=False
    def download(url,**kwargs):
        if offline:raise URLError('offline verification')
        name=url.removeprefix(module.BASE+'/')
        assert name in files
        return files[name],{'x-goog-generation':manifest['assets'][name]['generation']}
    monkeypatch.setattr(module,'download',download)
    monkeypatch.setattr(module,'publish',lambda p,data,suffix:publish(p,data,suffix,tmp_path))
    now=datetime(2026,11,14,tzinfo=timezone.utc)
    assert module.fetch_era5(now)=='stored'
    p=read_product('d08-era5-air-temperature',tmp_path)
    assert p.kind=='historical' and p.observed_at==datetime(2026,6,30,tzinfo=timezone.utc)
    assert p.issued_at is None and p.probability is None and not p.samples
    assert p.validated_for_use is False
    assert module.fetch_era5(now)=='unchanged'
    offline=True
    with pytest.raises(URLError):module.fetch_era5(now)
    assert read_product(p.id,tmp_path)==p
    offline=False
    assert module.fetch_era5(now)=='unchanged'
    assert len(list((tmp_path/p.id/'revisions').glob('*.json')))==1
