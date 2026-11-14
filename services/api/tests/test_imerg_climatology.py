from datetime import datetime,timezone
from pathlib import Path
from urllib.error import URLError
import io,zipfile
import h5py
import pytest
import earth_echo.connectors.imerg_climatology as module
from earth_echo.storage.products import publish,read_product

ROOT=Path(__file__).resolve().parents[3]/'data/samples/integrations'


@pytest.fixture(scope='module')
def originals():
    return tuple((ROOT/f'imerg-grand-climatology-{ext}.zip').read_bytes() for ext in ('nc4','tif'))


def altered_nc(raw,change):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        files={name:z.read(name) for name in z.namelist()}
    name=module.STEM+'.nc4';buffer=io.BytesIO(files[name])
    with h5py.File(buffer,'r+') as nc:change(nc)
    files[name]=buffer.getvalue();out=io.BytesIO()
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in files.items():z.writestr(name,data)
    return out.getvalue()


def test_authentic_climatology_all_native_nodes_quality_and_worldfile(originals):
    grid,metadata,check=module.decode_climatology(*originals)
    assert (grid.width,grid.height)==(360,180)
    assert grid.missing_cells==360 and check['native_missing']==24418
    assert grid.minimum==0 and 0 in grid.values  # Genuine zero, not filled absence.
    assert grid.maximum==7645.33984375
    assert grid.values[125*360+118]==1020.9791870117188
    assert check['latitude']==pytest.approx(-35.55,abs=1e-5)
    assert check['longitude']==pytest.approx(-61.55,abs=1e-5)
    assert '***' in metadata['worldfile_status'] and 'excluido' in metadata['worldfile_status']
    assert metadata['version']=='V07B' and 'runname[run]' in metadata['title']


def test_unit_change_and_native_disagreement_fail_before_publication(originals):
    changed=altered_nc(originals[0],lambda nc:nc['precipitation'].attrs.__setitem__('units','mm / day'))
    with pytest.raises(ValueError,match='dimensions/units'):module.decode_climatology(changed,originals[1])
    def corrupt(nc):nc['precipitation'][0,0]=0
    changed=altered_nc(originals[0],corrupt)
    with pytest.raises(ValueError,match='TIFF values/missing mask'):module.decode_climatology(changed,originals[1])


def test_real_climatology_ingestion_idempotent_offline_and_recovery(originals,tmp_path,monkeypatch):
    offline=False;calls=[]
    urls={module.BASE+module.STEM+'.'+ext+'.zip':raw for ext,raw in zip(('nc4','tif'),originals)}
    listing=' '.join(u.removeprefix('https://gpm.nasa.gov') for u in urls).encode()
    def download(url,**kwargs):
        calls.append(url)
        if offline:raise URLError('offline verification')
        return (listing if url==module.PAGE else urls[url]),{}
    monkeypatch.setattr(module,'download',download)
    monkeypatch.setattr(module,'publish',lambda p,raw,suffix:publish(p,raw,suffix,tmp_path))
    now=datetime(2026,11,14,tzinfo=timezone.utc)
    assert module.fetch_imerg_climatology(now)=='stored'
    p=read_product(module.KEY,tmp_path)
    assert p.kind=='historical' and p.probability is None and p.samples==[]
    assert p.observed_at==datetime(2000,6,1,tzinfo=timezone.utc)
    assert p.observation_end==datetime(2023,6,1,tzinfo=timezone.utc)
    assert p.issued_at is None and p.validated_for_use is False
    assert calls==[module.PAGE,*urls]  # Once per original, not per phenomenon.
    assert module.fetch_imerg_climatology(now)=='unchanged'
    offline=True
    with pytest.raises(URLError):module.fetch_imerg_climatology(now)
    assert read_product(module.KEY,tmp_path)==p
    offline=False
    assert module.fetch_imerg_climatology(now)=='unchanged'
    assert len(list(tmp_path.glob('*/revisions/*.json')))==1
    assert len(list((tmp_path/'shared').glob('*')))==1
