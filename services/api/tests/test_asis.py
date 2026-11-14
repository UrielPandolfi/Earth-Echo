from datetime import datetime,timezone
from pathlib import Path
import pytest
from earth_echo.connectors.asis import decode_export,dekad_window

def test_real_asis_keeps_percent_domain_native_flags_and_georeferencing():
    raw=(Path(__file__).resolve().parents[3]/'data/samples/integrations/asis-native-excerpt.tif').read_bytes()
    values,codes,lons,lats,bounds=decode_export(raw,224,224)
    present=[v for v in values if v is not None]
    assert min(present)==0.0 and max(present)==43.5
    assert values.count(None)==10186
    assert {v for v in codes if v is not None}=={251,253,254}
    assert lons[0]==pytest.approx(-63,abs=1e-6) and lats[0]==pytest.approx(-34,abs=1e-6)
    assert lats[0]>lats[-1] and lons[0]<lons[-1]
    assert bounds.left==pytest.approx(-63.00446398128)

def test_asis_calendar_dekad_is_not_an_instant_or_probabilistic_horizon():
    start,end=dekad_window('ASIS.ASI-D.2026-11-D1.GS1.LC-C')
    assert start==datetime(2026,11,1,tzinfo=timezone.utc)
    assert end==datetime(2026,11,11,tzinfo=timezone.utc)
    assert dekad_window('ASIS.ASI-D.2024-02-D3.GS1.LC-C')[1]==datetime(2024,3,1,tzinfo=timezone.utc)
    with pytest.raises(ValueError):dekad_window('ASIS.ASI-D.2026-11-D1.GS2.LC-C')
