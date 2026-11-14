from pathlib import Path
import pytest
from earth_echo.connectors.sentinel_ocean_color import decode_sentinel
from earth_echo.contracts.products import ScientificGrid

ROOT=Path(__file__).resolve().parents[3]/'data/samples/integrations'


def test_authentic_olci_values_mask_surface_algorithm_and_log_colour():
    grid,stamp,ds,sha=decode_sentinel((ROOT/'sentinel3-chlorophyll.nc').read_bytes())
    assert (grid.width,grid.height)==(400,200)
    assert grid.missing_cells==72868 and grid.maximum==pytest.approx(315.0909729003906)
    assert grid.minimum==pytest.approx(.009999999776482582)
    assert stamp.isoformat()=='2026-11-10T12:00:00+00:00'
    assert grid.color_scale=='log10' and ds.values('altitude')==[0.]
    assert ds.variables['chlor_a']['attributes']['cw_product_status']=='Experimental'
    assert 'graphics' in grid.quality_mask and len(sha)==64
    # A colour range is not a quality mask: the valid native maximum exceeds it.
    assert grid.maximum>ds.variables['chlor_a']['attributes']['colorBarMaximum']
    payload=grid.model_dump();index=next(i for i,v in enumerate(grid.values) if v is not None)
    payload['values'][index]=0
    with pytest.raises(ValueError,match='zero must not be silently masked'):
        ScientificGrid.model_validate(payload)


def test_idempotence_ignores_request_history_but_keeps_original_processing_history():
    raw=(ROOT/'sentinel3-chlorophyll.nc').read_bytes()
    _,_,ds,original=decode_sentinel(raw)
    import re
    stamp=re.search(rb'2026-11-14T\d{2}:\d{2}:\d{2}Z \(local files\)',raw).group(0)[:20]
    altered=raw.replace(stamp,b'2026-11-15T00:00:00Z')
    assert altered!=raw and decode_sentinel(altered)[3]==original
    processing=raw.replace(b'cwutils 3.6.1.3',b'cwutils 3.6.1.4')
    assert decode_sentinel(processing)[3]!=original


def test_independent_csv_verifies_units_time_and_returned_coordinates():
    from earth_echo.connectors.sentinel_ocean_color import verify_csv
    raw=(ROOT/'sentinel3-check.csv').read_bytes()
    args=('2026-11-10T12:00:00Z',36.65625,-87.28125,315.0909729003906)
    assert verify_csv(raw,*args)==315.09097
    for changed in [raw.replace(b'mg m^-3',b'g m^-3'),raw.replace(b'2026-11-10',b'2026-11-11'),raw.replace(b'36.65625',b'35.65625'),raw.replace(b'315.09097',b'999.00000')]:
        with pytest.raises(ValueError):verify_csv(changed,*args)


def test_full_ingestion_preserves_real_data_through_network_failure_and_recovery(tmp_path,monkeypatch):
    import json
    from datetime import datetime,timezone
    from urllib.error import URLError
    import earth_echo.connectors.sentinel_ocean_color as module
    from earth_echo.storage.products import publish,read_product
    raw=(ROOT/'sentinel3-chlorophyll.nc').read_bytes()
    csv_raw=(ROOT/'sentinel3-check.csv').read_bytes()
    stamp=decode_sentinel(raw)[1]
    # Minimal discovery control response; scientific values and CSV are authentic fixtures.
    info=json.dumps({'table':{'rows':[['attribute','time','actual_range','double',str(stamp.timestamp())]]}}).encode()
    offline=False
    def download(url,**kwargs):
        if offline:raise URLError('offline verification')
        return (info if '/info/' in url else csv_raw if '.csv?' in url else raw),{}
    monkeypatch.setattr(module,'download',download)
    monkeypatch.setattr(module,'publish',lambda p,data,suffix:publish(p,data,suffix,tmp_path))
    now=datetime(2026,11,14,tzinfo=timezone.utc)
    assert module.fetch_sentinel_chlorophyll(now)=='stored'
    product=read_product('d25-s3a-chlorophyll',tmp_path)
    assert module.fetch_sentinel_chlorophyll(now)=='unchanged'
    offline=True
    with pytest.raises(URLError):module.fetch_sentinel_chlorophyll(now)
    assert read_product(product.id,tmp_path)==product
    offline=False
    assert module.fetch_sentinel_chlorophyll(now)=='unchanged'
    assert len(list((tmp_path/product.id/'revisions').glob('*.json')))==1
