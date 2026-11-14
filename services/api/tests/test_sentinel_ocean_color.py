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
