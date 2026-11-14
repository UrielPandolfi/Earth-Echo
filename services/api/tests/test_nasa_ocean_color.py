from pathlib import Path
from datetime import datetime,timezone
from urllib.error import URLError
import io,json,zipfile
import pytest
import earth_echo.connectors.nasa_ocean_color as module
from earth_echo.storage.products import publish,read_product

FIXTURE=Path(__file__).resolve().parents[3]/'data/samples/integrations/nasa-aqua-chlorophyll-2022.zip'
NOW=datetime(2026,11,14,tzinfo=timezone.utc)


@pytest.fixture(scope='module')
def files():
    with zipfile.ZipFile(FIXTURE) as z:
        return {n:z.read(n) for n in json.loads(z.read('manifest.json'))['assets']}


def test_authentic_nasa_archive_units_mask_date_and_wrapped_longitude(files):
    grid,stamp,ds,_=module.decode_chlorophyll(files['subset.nc'])
    assert stamp.isoformat()=='2022-05-31T12:00:00+00:00'
    assert ds.attributes['processing_version']=='2018.1QLP'
    assert (grid.width,grid.height,grid.missing_cells)==(360,180,60677)
    assert grid.minimum==pytest.approx(.017408767715096474)
    assert grid.maximum==pytest.approx(37.184226989746094)  # Above colorBarMaximum30 remains valid.
    maximum=grid.values.index(grid.maximum)
    assert grid.latitudes[maximum//360]==54.479164123535156
    assert grid.longitudes[maximum%360]==48.52083969116211
    assert grid.longitudes[0]==pytest.approx(-179.4791717529297)
    assert all(a<b for a,b in zip(grid.longitudes,grid.longitudes[1:]))
    assert grid.color_scale=='log10' and grid.values[0] is None
    module.verify_point(files['finite.csv'],'2022-05-31T12:00:00Z',54.479164123535156,48.52083969116211,grid.maximum)
    module.verify_point(files['missing.csv'],'2022-05-31T12:00:00Z',grid.latitudes[0],grid.longitudes[0]%360,None)


def test_wrong_units_version_csv_coordinates_and_missing_mask_rejected(files):
    with pytest.raises(ValueError,match='units'):module.decode_chlorophyll(files['subset.nc'].replace(b'mg m-3',b'mg m-2'))
    with pytest.raises(ValueError,match='version changed'):module.decode_chlorophyll(files['subset.nc'].replace(b'2018.1QLP',b'2022.1QLP'))
    with pytest.raises(ValueError,match='coordinates'):module.verify_point(files['finite.csv'],'2022-05-31T12:00:00Z',54.48,48.52083969116211,37.184226989746094)
    with pytest.raises(ValueError,match='mask'):module.verify_point(files['missing.csv'].replace(b'NaN',b'0'),'2022-05-31T12:00:00Z',89.47916412353516,180.5208282470703,None)


def test_historical_product_idempotence_failure_recovery_and_provenance(files,tmp_path,monkeypatch):
    offline=False;checks=0
    def download(url,**kwargs):
        nonlocal checks
        if offline:raise URLError('controlled outage')
        if url==module.INFO:return files['discovery.json'],{}
        if '.nc?' in url:return files['subset.nc'],{}
        key='finite.csv' if checks%2==0 else 'missing.csv';checks+=1
        return files[key],{}
    monkeypatch.setattr(module,'download',download)
    monkeypatch.setattr(module,'publish',lambda p,raw,suffix:publish(p,raw,suffix,tmp_path))
    assert module.fetch_nasa_chlorophyll(NOW)=='stored'
    previous=read_product(module.KEY,tmp_path)
    assert previous.source_id=='D17' and previous.kind=='historical'
    assert previous.observed_at.year==2022 and previous.retrieved_at.year==2026
    assert previous.issued_at is None and previous.probability is None and not previous.validated_for_use
    assert 'QLP' in previous.product_version and 'OCI' in previous.title
    with zipfile.ZipFile(tmp_path/previous.raw_file) as z:
        assert z.read('subset.nc')==files['subset.nc'] and z.read('missing.csv')==files['missing.csv']
    assert module.fetch_nasa_chlorophyll(NOW)=='unchanged'
    offline=True
    with pytest.raises(URLError):module.fetch_nasa_chlorophyll(NOW)
    assert read_product(module.KEY,tmp_path)==previous
    offline=False
    assert module.fetch_nasa_chlorophyll(NOW)=='unchanged'
    assert len(list(tmp_path.glob('*/revisions/*.json')))==1
