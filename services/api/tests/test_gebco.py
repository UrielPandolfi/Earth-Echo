from pathlib import Path
import pytest
from earth_echo.connectors.gebco import decode_ascii

def test_original_gebco_ascii_values_axes_and_tid():
    root=Path(__file__).resolve().parents[3]/'data/samples/integrations'
    raw=(root/'gebco-elevation.ascii').read_bytes()
    matrix,lats,lons=decode_ascii(raw,'elevation')
    tid,qlats,qlons=decode_ascii((root/'gebco-tid.ascii').read_bytes(),'tid')
    assert matrix[0][0]==-3987 and tid[0][0]==40
    assert len(matrix)==30 and len(matrix[0])==30
    assert lats[0]==pytest.approx(17.00208333333333)
    assert lons[0]==pytest.approx(-84.99791666666667)
    assert (qlats,qlons)==(lats,lons)
    # A truncated row is not silently filled with zeros.
    with pytest.raises(ValueError,match='Missing DAP row'):
        decode_ascii(raw.replace(b'[29],',b'[99],'),'elevation')
