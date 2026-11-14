from pathlib import Path
from datetime import datetime,timezone
from urllib.error import URLError
from shapely.geometry import shape,Polygon
import io,zipfile
import pytest
import earth_echo.connectors.glacier_outlines as module
from earth_echo.science.static_geometry import prepare_static_polygon
from earth_echo.storage.products import publish,read_product

FIXTURE=Path(__file__).resolve().parents[3]/'data/samples/integrations/rgi60-southern-andes.zip'


def test_authentic_rgi6_outlines_preserve_native_ids_areas_epochs_and_holes():
    samples,regions,vertices,normalized=module.decode_outlines(FIXTURE.read_bytes())
    assert len(samples)==len(regions)==38 and vertices==23488 and normalized==6
    perito=next(s for s in samples if s.id=='RGI60-17.00312')
    assert perito.value==263.322 and perito.time is None and perito.probability is None
    assert perito.attributes['BgnDate']=='20009999' and perito.attributes['EndDate']=='20030531'
    assert perito.longitude is None and perito.latitude is None  # Polygon, no invented pin.
    assert all(shape(r.geometry.model_dump()).is_valid for r in regions)
    assert sum(len(poly)-1 for r in regions for poly in r.geometry.coordinates)>0
    assert all(-74.5<=float(s.attributes['CenLon'])<=-72 and -51<=float(s.attributes['CenLat'])<=-48 and s.value>=50 for s in samples)
    assert all(s.id.startswith('RGI60-17.') for s in samples)


def test_csv_disagreement_or_bad_crs_rejects_before_publication():
    with zipfile.ZipFile(FIXTURE) as z:members={n:z.read(n) for n in z.namelist()}
    def packed(files):
        buffer=io.BytesIO()
        with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for n,b in files.items():z.writestr(n,b)
        return buffer.getvalue()
    changed=dict(members);name=module.NAME+'_hypso.csv'
    changed[name]=changed[name].replace(b'         0.888',b'         0.889',1)
    with pytest.raises(ValueError,match='published count/area'):module.decode_outlines(packed(changed))
    changed=dict(members);changed[module.NAME+'.prj']=b'LOCAL_CS["unqualified local coordinates",UNIT["metre",1]]'
    with pytest.raises(ValueError,match='not WGS84'):module.decode_outlines(packed(changed))


def test_static_topology_cannot_hide_a_material_area_change():
    # Deliberate geometry stress case, not production data. A bow-tie changes
    # zero signed area into two triangles and must remain unavailable to draw.
    geometry=Polygon([(0,0),(2,2),(0,2),(2,0),(0,0)])
    result,valid,quality=prepare_static_polygon(geometry)
    assert not valid and result.equals_exact(geometry,0) and 'no dibujada' in quality


def test_rgi_ingestion_idempotence_network_failure_and_recovery(tmp_path,monkeypatch):
    raw=FIXTURE.read_bytes();offline=False
    def download(url,**kwargs):
        if offline:raise URLError('offline verification')
        return ((module.NAME+'.zip').encode() if url==module.LISTING else raw),{}
    monkeypatch.setattr(module,'download',download)
    monkeypatch.setattr(module,'publish',lambda p,data,suffix:publish(p,data,suffix,tmp_path))
    now=datetime(2026,11,14,tzinfo=timezone.utc)
    assert module.fetch_glacier_outlines(now)=='stored'
    p=read_product(module.KEY,tmp_path)
    assert p.kind=='static_context' and p.representation=='regions' and len(p.regions)==38
    assert p.observed_at is None and p.issued_at is None and p.validated_for_use is False
    assert module.fetch_glacier_outlines(now)=='unchanged'
    offline=True
    with pytest.raises(URLError):module.fetch_glacier_outlines(now)
    assert read_product(module.KEY,tmp_path)==p
    offline=False
    assert module.fetch_glacier_outlines(now)=='unchanged'
    assert len(list(tmp_path.glob('*/revisions/*.json')))==1
