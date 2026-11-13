from datetime import datetime,timezone
from pathlib import Path
import pytest
from earth_echo.contracts.geometry import GeoMultiLineString
from earth_echo.science.paths import split_dateline,path_extent
from earth_echo.connectors.ibtracs import decode_tracks,check_csv

@pytest.mark.parametrize('points',[[[179.,10.],[-179.,12.]],[[-179.,12.],[179.,10.]],[[180.,5.],[-179.,6.]]])
def test_split_path_has_no_dateline_jump_and_declares_extent(points):
    line=split_dateline(points)
    assert path_extent(points).crosses_antimeridian
    assert all(abs(b[0]-a[0])<=180 for part in line.coordinates for a,b in zip(part,part[1:]))
    with pytest.raises(ValueError): GeoMultiLineString(type='MultiLineString',coordinates=[points])

def test_real_ibtracs_fixture_matches_csv_and_keeps_quality_and_missing():
    root=Path(__file__).resolve().parents[3]/'data/samples/integrations'
    samples,tracks=decode_tracks((root/'ibtracs-excerpt.nc').read_bytes(),datetime(2026,11,13,tzinfo=timezone.utc))
    assert check_csv(samples,(root/'ibtracs-active.csv').read_bytes())==139
    assert len(tracks)==4
    olana=next(t for t in tracks if t.name=='OLANA')
    assert olana.extent.crosses_antimeridian and len(olana.geometry.coordinates)==2
    pena=next(s for s in samples if s.attributes['nombre']=='PENA')
    assert pena.latitude==pytest.approx(7.7,abs=.00001)
    assert pena.longitude==pytest.approx(-129.8,abs=.00001)
    assert pena.value is None and pena.probability is None
    assert pena.attributes['TRACK_TYPE']=='PROVISIONAL'
    assert all(s.time.tzinfo is not None for s in samples)
