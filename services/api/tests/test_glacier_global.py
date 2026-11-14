from pathlib import Path
from datetime import datetime,timezone
from urllib.error import URLError
import io,zipfile,json
import pytest
import earth_echo.connectors.glacier_global as module
from earth_echo.storage.products import publish,read_product

FIXTURE=Path(__file__).resolve().parents[3]/'data/samples/integrations/rgi7-global-attributes.zip'


@pytest.fixture(scope='module')
def originals():
    with zipfile.ZipFile(FIXTURE) as z:
        manifest=json.loads(z.read('manifest.json'))
        files={name:z.read(name) for name in manifest['assets']}
    return files[module.G_NAME],files['RGI2000-v7.0-G-comparison-rgi6.csv']


def test_authentic_global_points_areas_ids_and_independent_region_metadata(originals):
    samples,statistics=module.decode_global(*originals)
    assert statistics['native_records']==274531 and len(statistics['region_counts'])==19
    assert statistics['native_area_km2']=='706744.049467246904673'
    assert len(samples)==1851 and len(statistics['selected_region_counts'])==16
    assert len({s.id for s in samples})==1851
    first=samples[0]
    assert first.id=='RGI2000-v7.0-G-01-01334' and first.value==132.44631153716037
    assert first.longitude==-152.6572955593789 and first.latitude==60.70034149999999
    assert first.attributes['src_date']=='2010-09-12T00:00:00' and first.time is None
    assert all(s.value>=50 and s.probability is None for s in samples)
    assert min(s.longitude for s in samples)==-159.41876643621055
    assert max(s.longitude for s in samples)==170.17238288055256
    assert all(s.id.startswith('RGI2000-v7.0-G-') for s in samples)


def test_wrong_regional_reference_and_native_coordinates_rejected(originals):
    raw,reference=originals
    altered=reference.replace(b',27509,',b',27508,',1)
    assert altered!=reference
    with pytest.raises(ValueError,match='independent published region'):module.decode_global(raw,altered)
    damaged=raw.replace(b'60.70034149999999',b'160.70034149999999',1)
    assert damaged!=raw
    with pytest.raises(ValueError,match='representative point'):module.decode_global(damaged,reference)


def test_compressed_original_is_lossless_idempotent_and_keeps_valid_on_failure(originals,tmp_path,monkeypatch):
    raw,reference=originals;offline=False
    def download(url,**kwargs):
        if offline:raise URLError('offline verification')
        return (raw if url==module.G_URL else reference if url==module.COMPARISON else module.G_NAME.encode()),{}
    monkeypatch.setattr(module,'download',download)
    monkeypatch.setattr(module,'publish',lambda p,data,suffix:publish(p,data,suffix,tmp_path))
    now=datetime(2026,11,14,tzinfo=timezone.utc)
    assert module.fetch_glacier_global(now)=='stored'
    product=read_product(module.KEY,tmp_path)
    assert product.kind=='static_context' and product.representation=='points'
    assert product.observed_at is None and product.probability is None and not product.validated_for_use
    assert product.extent.crosses_antimeridian is True
    retained=(tmp_path/product.raw_file).read_bytes()
    assert len(retained)<26_000_000
    with zipfile.ZipFile(io.BytesIO(retained)) as archive:
        assert archive.read(module.G_NAME)==raw  # All 274531 records, not only display.
    assert module.fetch_glacier_global(now)=='unchanged'
    offline=True
    with pytest.raises(URLError):module.fetch_glacier_global(now)
    assert read_product(module.KEY,tmp_path)==product
    offline=False
    assert module.fetch_glacier_global(now)=='unchanged'
    assert len(list(tmp_path.glob('*/revisions/*.json')))==1
