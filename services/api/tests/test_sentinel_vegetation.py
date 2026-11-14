from pathlib import Path
from datetime import datetime,timezone
from urllib.error import URLError
import io,json,zipfile
import pytest
import earth_echo.connectors.sentinel_vegetation as module
from earth_echo.connectors.ranges import ArchivedRangeSource
from earth_echo.science.vegetation import ndvi
from earth_echo.storage.products import publish,read_product

FIXTURE=Path(__file__).resolve().parents[3]/'data/samples/integrations/sentinel2-pampa-c1.zip'
NOW=datetime(2026,11,14,tzinfo=timezone.utc)


@pytest.fixture(scope='module')
def files():
    with zipfile.ZipFile(FIXTURE) as z:
        manifest=json.loads(z.read('manifest.json'))
        return {name:z.read(name) for name in manifest['assets']}


def test_authentic_native_boa_offset_qa_utc_and_georeferencing(files):
    products,archive=module.products_from_files(dict(files),NOW)
    red,nir,index=products
    assert red.observed_at.isoformat()=='2026-11-11T14:12:34.012553+00:00'
    assert all(p.issued_at is None and p.probability is None and not p.validated_for_use for p in products)
    assert red.kind=='observation' and index.kind=='indicator'
    assert red.grid.width==80 and red.grid.height==60
    assert red.grid.west==-61.54 and red.grid.south==-35.49
    assert red.grid.longitudes[0]==pytest.approx(-61.5395) and red.grid.latitudes[0]==pytest.approx(-35.4305)
    assert red.grid.missing_cells==nir.grid.missing_cells==720 and index.grid.missing_cells==721
    assert red.grid.minimum<0 and nir.grid.minimum<0  # Native negative retrievals preserved.
    assert all(v is None for v,q in zip(red.grid.values,red.grid.quality_values) if q not in (4,5))
    assert index.grid.values[0]==pytest.approx(.3320825515947467)
    assert index.grid.minimum==pytest.approx(-.5) and index.grid.maximum==pytest.approx(.9581967213114755)
    assert index.calculation.parameters['BOA_ADD_OFFSET_DN']==-1000
    assert {p.checksum_sha256 for p in products}=={index.checksum_sha256}
    assert {i.product_id for i in index.calculation.inputs}=={red.id,nir.id}
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        assert all(z.read(name)==raw for name,raw in files.items())


def test_inconsistent_scaling_crs_and_quality_product_rejected(files):
    damaged=dict(files);item=json.loads(damaged['item.json'])
    item['assets']['nir']['raster:bands'][0]['offset']=0
    damaged['item.json']=module.canonical(item)
    with pytest.raises(ValueError,match='scale or nodata'):module.products_from_files(damaged,NOW)
    damaged=dict(files);damaged['product_metadata.xml']=damaged['product_metadata.xml'].replace(b'>-1000<',b'>0<')
    with pytest.raises(ValueError,match='BOA scale/offset'):module.products_from_files(damaged,NOW)
    damaged=dict(files);damaged['granule_metadata.xml']=damaged['granule_metadata.xml'].replace(b'EPSG:32720',b'EPSG:32721')
    with pytest.raises(ValueError,match='CRS'):module.products_from_files(damaged,NOW)
    damaged=dict(files);item=json.loads(damaged['item.json']);item['properties']['earthsearch:boa_offset_applied']=True
    damaged['item.json']=module.canonical(item)
    with pytest.raises(ValueError,match='original-offset'):module.products_from_files(damaged,NOW)


def test_scene_idempotence_no_redownload_network_failure_and_recovery(files,tmp_path,monkeypatch):
    offline=False;downloads=[];ranges=[]
    def download(url,**kwargs):
        downloads.append(url)
        if offline:raise URLError('offline independent exercise')
        if '/search?' in url:return files['search.json'],{}
        name='granule_metadata.xml' if url.endswith('/metadata.xml') else 'product_metadata.xml'
        return files[name],{}
    monkeypatch.setattr(module,'download',download)
    monkeypatch.setattr(module,'publish',lambda p,raw,suffix:publish(p,raw,suffix,tmp_path))
    monkeypatch.setattr(module,'products_root',lambda:tmp_path)
    monkeypatch.setattr(module,'read_product',lambda key:read_product(key,tmp_path))
    # Captured sources have two block sizes, retain them rather than reblock fixtures.
    class Replay(ArchivedRangeSource):
        def __setattr__(self,name,value):
            if name=='block_size' and hasattr(self,'block_size'):return
            super().__setattr__(name,value)
    def replay(url,**kwargs):
        key='red' if url.endswith('B04.tif') else 'nir' if url.endswith('B08.tif') else 'scl';ranges.append(key)
        return Replay(files[key+'-ranges.json'])
    monkeypatch.setattr(module,'RangeSource',replay)
    assert module.fetch_sentinel_vegetation(NOW)=='stored'
    previous=[read_product(module.KEY+'-'+k,tmp_path) for k in ('red','nir','ndvi')]
    assert len(ranges)==3 and len(list(tmp_path.glob('shared/*.zip')))==1
    assert module.fetch_sentinel_vegetation(NOW)=='unchanged'
    assert len(ranges)==3 and len(downloads)==4  # Second attempt discovers only; no science download.
    offline=True
    with pytest.raises(URLError):module.fetch_sentinel_vegetation(NOW)
    assert [read_product(p.id,tmp_path) for p in previous]==previous
    offline=False
    assert module.fetch_sentinel_vegetation(NOW)=='unchanged'
    assert len(list(tmp_path.glob('*/revisions/*.json')))==3


def test_ndvi_conservative_domain_offset_and_absent_inputs():
    # A common uncorrected-DN ratio gives 1/3; the physical offset yields 3/7.
    assert ndvi((3000-1000)/10000,(6000-1000)/10000)==pytest.approx(.4285714285714286)
    assert ndvi(0,.4)==1 and ndvi(.4,0)==-1
    assert ndvi(None,.4) is None and ndvi(float('nan'),.4) is None
    assert ndvi(-.001,.4) is None and ndvi(0,0) is None
