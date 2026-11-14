import json
from pathlib import Path
from xml.etree import ElementTree as E
import pytest
from earth_echo.science.paths import split_polygon,path_extent
from earth_echo.connectors.gdacs import decode_cap,G

def test_polygon_split_preserves_dateline_parts_and_not_greenwich():
    ring=[[179.,10.],[-179.,10.],[-179.,12.],[179.,12.],[179.,10.]]
    geometry=split_polygon(ring)
    assert len(geometry.coordinates)==2 and path_extent(ring).crosses_antimeridian
    assert all(abs(p[0])>=179 for poly in geometry.coordinates for line in poly for p in line)
    assert all(abs(b[0]-a[0])<=180 for poly in geometry.coordinates for line in poly for a,b in zip(line,line[1:]))
    with pytest.raises(ValueError,match='closed'): split_polygon(ring[:-1])

def test_real_cap_preserves_past_state_and_metadata_cross_check():
    data=json.loads((Path(__file__).resolve().parents[3]/'data/samples/integrations/gdacs-cap-excerpt.json').read_bytes())
    item=E.fromstring(data['rss_item']);raw=data['cap'].encode()
    sample,regions=decode_cap(raw,item)
    assert sample.attributes['urgency']=='Past'
    assert sample.attributes['eventid']=='1001348' and sample.attributes['version']=='24'
    assert sample.attributes['alertlevel']=='Green'
    assert sample.probability is None and sample.valid_to is None
    assert sample.value==1.0 and len(regions)==1
    assert regions[0].extent.west==pytest.approx(-173.269525038236)
    assert regions[0].extent.south==pytest.approx(8.132)
    with pytest.raises((ValueError,E.ParseError)): decode_cap(b'<html>Login</html>',item)
    item.find(G+'version').text='999'
    with pytest.raises(ValueError,match='revision disagrees'): decode_cap(raw,item)
