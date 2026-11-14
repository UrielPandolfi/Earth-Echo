from pathlib import Path
import csv,io
import pytest
from earth_echo.connectors.glacier_inventory import decode_inventory,verify_complex

ROOT=Path(__file__).resolve().parents[3]/'data/samples/integrations'


def test_authentic_rgi7_area_point_date_and_partial_row():
    samples,rows=decode_inventory((ROOT/'rgi7-glacier-prefix.csv').read_bytes())
    assert len(samples)==5 # trailing partial native row was not made into a record
    first=samples[0]
    assert first.id=='RGI2000-v7.0-G-01-00001'
    assert first.value==pytest.approx(.239199161030735)
    assert first.longitude==-155.90940361036584 and first.latitude==67.4137265
    assert first.time is None and first.probability is None
    assert first.attributes['src_date']=='2008-09-02T00:00:00'
    assert 'no centroide' in first.quality
    glacier,complex_row=verify_complex(rows,(ROOT/'rgi7-complex-prefix.csv').read_bytes())
    assert glacier['rgi_id'].endswith('-00001') and complex_row['rgi_id'].startswith('RGI2000-v7.0-C-')
    assert float(glacier['area_km2'])==pytest.approx(float(complex_row['area_km2']),rel=1e-10)


def test_rgi_missing_area_preserves_coordinates_without_a_fake_zero():
    raw=(ROOT/'rgi7-glacier-prefix.csv').read_bytes()
    samples,_=decode_inventory(raw.replace(b',0.239199161030735,',b',-9999.0,'))
    assert samples[0].value is None and samples[0].map_eligible is False
    assert samples[0].longitude is not None
    with pytest.raises(ValueError,match='native RGI7 attributes'):
        decode_inventory(b'<html>Earthdata Login</html>\n')
    rows=list(csv.DictReader(io.StringIO((ROOT/'rgi7-complex-prefix.csv').read_text())))
    for row in rows:row['area_km2']=str(float(row['area_km2'])+10)
    stream=io.StringIO();writer=csv.DictWriter(stream,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    _,glaciers=decode_inventory(raw)
    with pytest.raises(ValueError,match='No independent'):
        verify_complex(glaciers,stream.getvalue().encode())
