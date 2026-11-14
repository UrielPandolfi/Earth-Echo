from pathlib import Path
from datetime import datetime,timezone
import io,json,zipfile,hashlib
import h5py
import rasterio
import pytest
from earth_echo.connectors.grace_assimilation import decode_grace,pack,NC,VARIABLES

FIXTURE=Path(__file__).resolve().parents[3]/'data/samples/integrations/grace-global.zip'


def unpack():
    with zipfile.ZipFile(FIXTURE) as z:files={name:z.read(name) for name in z.namelist()}
    return files,json.loads(files.pop('manifest.json'))


def replace(files,manifest,name,data):
    files[name]=data;manifest['assets'][name]['sha256']=hashlib.sha256(data).hexdigest();manifest['assets'][name]['bytes']=len(data)
    return pack(files,manifest)


def test_authentic_percentiles_masks_georeferencing_and_native_reference_date():
    products,stamp,metadata,_=decode_grace(FIXTURE.read_bytes())
    assert stamp==datetime(2026,11,10,tzinfo=timezone.utc)
    assert metadata['version']=='030' and '2019-08' in metadata['input']
    assert set(products)==set(VARIABLES)
    files,_=unpack()
    with h5py.File(io.BytesIO(files[NC])) as nc:
        for variable,(grid,native_missing) in products.items():
            assert (grid.width,grid.height)==(360,150) and grid.south==-60 and grid.north==90
            assert grid.missing_cells==39444 and grid.values.count(None)==39444
            assert grid.minimum==pytest.approx(.21978022158145905) and grid.maximum==100
            assert grid.reverse_colors is True
            # Nearest ties explicitly select native southwest centre.
            assert grid.values[125*360+118]==float(nc[variable][0,97,473])
            assert native_missing==630689


def test_changed_units_or_calendar_are_rejected_before_publication():
    for attribute,value,match in [('units','fraction','units/shape'),('cell_methods','time: mean','units/shape')]:
        files,manifest=unpack();buffer=io.BytesIO(files[NC])
        with h5py.File(buffer,'r+') as nc:nc['gws_inst'].attrs[attribute]=value
        with pytest.raises(ValueError,match=match):decode_grace(replace(files,manifest,NC,buffer.getvalue()))
    files,manifest=unpack();buffer=io.BytesIO(files[NC])
    with h5py.File(buffer,'r+') as nc:nc['time'].attrs['calendar']='noleap'
    with pytest.raises(ValueError,match='calendar'):decode_grace(replace(files,manifest,NC,buffer.getvalue()))


def test_real_zero_is_preserved_and_independent_tiff_disagreement_is_rejected():
    files,manifest=unpack();buffer=io.BytesIO(files[NC])
    with h5py.File(buffer,'r+') as nc:nc['gws_inst'][0,97,473]=0
    # Deliberate test mutation, not invented production observations.
    altered=replace(files,manifest,NC,buffer.getvalue())
    with pytest.raises(ValueError,match='TIFF values/missing mask'):decode_grace(altered)
    tif=VARIABLES['gws_inst'][0]
    with rasterio.open(io.BytesIO(files[tif])) as ds:
        data=ds.read(1);profile=ds.profile
    data[599-97,473]=0
    with rasterio.io.MemoryFile() as memory:
        with memory.open(**profile) as ds:ds.write(data,1)
        raw=memory.read()
    grid=decode_grace(replace(files,manifest,tif,raw))[0]['gws_inst'][0]
    assert grid.values[125*360+118]==0
    assert grid.missing_cells==39444


def test_shared_ingestion_is_idempotent_and_recovers_without_losing_valid_data(tmp_path,monkeypatch):
    from urllib.error import URLError
    import earth_echo.connectors.grace_assimilation as module
    from earth_echo.storage.products import publish,read_product
    files,manifest=unpack();offline=False
    # Only link markup is a test control; every scientific file is authentic.
    listing=' '.join('/globaldata/current/'+name for name in files).encode()
    def download(url,**kwargs):
        if offline:raise URLError('offline verification')
        if url==module.PAGE:return listing,{}
        name=url.removeprefix(module.BASE)
        return files[name],{'Last-Modified':manifest['assets'][name]['last_modified_http']}
    monkeypatch.setattr(module,'download',download)
    monkeypatch.setattr(module,'publish',lambda p,data,suffix:publish(p,data,suffix,tmp_path))
    now=datetime(2026,11,14,tzinfo=timezone.utc)
    assert module.fetch_grace(now)=='stored'
    original=[read_product(item[1],tmp_path) for item in VARIABLES.values()]
    assert len({p.raw_file for p in original})==1 and len(list((tmp_path/'shared').glob('*')))==1
    assert all(p.kind=='indicator' and p.probability is None and not p.samples and p.issued_at is None and p.validated_for_use is False for p in original)
    assert module.fetch_grace(now)=='unchanged'
    offline=True
    with pytest.raises(URLError):module.fetch_grace(now)
    assert [read_product(p.id,tmp_path) for p in original]==original
    offline=False
    assert module.fetch_grace(now)=='unchanged'
    assert len(list(tmp_path.glob('*/revisions/*.json')))==3
