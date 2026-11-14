import json
from pathlib import Path
from collections import Counter
import pytest
from earth_echo.connectors.locusts import decode_reports

def fixture():
    return json.loads((Path(__file__).resolve().parents[3]/'data/samples/integrations/locust-surveys.geojson').read_bytes())

def test_real_desert_locust_reports_include_absence_without_inventing_counts():
    reports=decode_reports(fixture())
    assert len(reports)==49
    assert Counter(s.category for s in reports)=={'ADULT':20,'HOPPER':19,'NO LOCUST':10}
    first=reports[0]
    assert first.longitude==pytest.approx(-11.616667) and first.latitude==pytest.approx(25.236389)
    assert first.category=='NO LOCUST' and first.value is None and first.probability is None
    assert first.attributes['Locust_Presence']=='ABSENT'
    assert first.time.isoformat()=='2026-11-11T00:00:00+00:00'
    assert first.attributes['Observation_Time']=='11:43:0'

def test_invalid_survey_geometry_stays_missing_and_empty_query_is_valid():
    data=fixture();data['features'][0]['geometry']['coordinates'][0]=432.87
    report=decode_reports(data)[0]
    assert report.longitude is None and report.latitude is None
    assert 'sin pin' in report.quality
    assert decode_reports({'type':'FeatureCollection','features':[]})==[]
    data=fixture();data['features'][0]['properties']['Latitude']=0
    with pytest.raises(ValueError,match='disagree'):decode_reports(data)
