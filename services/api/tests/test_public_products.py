import base64
import hashlib
import json
from datetime import timedelta
import pytest
from earth_echo.paths import repo_root
from earth_echo.connectors.cneos import parse_sentry
from earth_echo.connectors.geology_products import parse_gvp,parse_cap
from earth_echo.connectors.aftershocks import parse_oaf
from earth_echo.connectors.climate_indices import parse_oni

def excerpt(key):
    path=repo_root()/'data/samples/integrations/provider-excerpts.json'
    return json.loads(path.read_bytes())[key]['excerpt']

def test_sentry_original_probabilities_have_definition_and_no_earth_pin():
    samples=parse_sentry(excerpt('d29-sentry'))
    first=next(s for s in samples if s.id=='2011 TO')
    assert first.probability == pytest.approx(2.937e-6)
    assert first.longitude is None and first.latitude is None
    assert '2064' in first.probability_definition
    invalid=excerpt('d29-sentry'); invalid['data'][0]['ip']='1.1'
    with pytest.raises(ValueError): parse_sentry(invalid)

def test_gvp_native_coordinates_and_inventory_are_not_alerts():
    samples=parse_gvp(excerpt('d23-holocene-inventory'))
    assert samples[0].id=='210010'
    assert (samples[0].longitude,samples[0].latitude)==(6.85,50.17)
    assert samples[0].time is None and samples[0].probability is None
    invalid=excerpt('d23-holocene-inventory'); invalid['features'][0]['properties']['Longitude']=0
    with pytest.raises(ValueError): parse_gvp(invalid)

def test_cap_preserves_information_cancel_status_and_expiry_without_epicentre_pin():
    xml=excerpt('d27-tsunami-messages')
    samples,meta=parse_cap(xml.encode())
    assert samples and meta['msgType'] in {'Alert','Update','Cancel'}
    assert all(s.latitude is None and s.value is None for s in samples)
    assert all(s.valid_to is None or s.valid_to>s.time for s in samples)
    original=meta['msgType']
    cancel=xml.replace(f'<msgType>{original}</msgType>','<msgType>Cancel</msgType>')
    rows,_=parse_cap(cancel.encode())
    assert rows[0].attributes['msgType']=='Cancel'

def test_usgs_oaf_matches_provider_manifest_and_keeps_threshold_and_window():
    raw=(repo_root()/'data/samples/integrations/usgs-oaf-us7000txrk.json').read_bytes()
    assert base64.b64encode(hashlib.sha256(raw).digest()).decode()=='J5ZevPV7KuO4GLouiFssfax5EsQsuZEVxkRDUozNO6g='
    rows=parse_oaf(json.loads(raw),'us7000txrk')
    assert len(rows)==20
    assert rows[0].probability==.03126
    assert rows[0].valid_to-rows[0].time==timedelta(days=1)
    assert '≥3.0' in rows[0].probability_definition
    assert all(s.probability is not None and s.longitude is None for s in rows)

def test_oni_windows_cross_year_without_changing_index():
    rows=parse_oni(b'SEAS YR TOTAL ANOM\nDJF 1950 25.01 -1.32\nNDJ 1950 25.00 -1.00\n')
    assert rows[0].time.isoformat()=='1949-12-01T00:00:00+00:00'
    assert rows[0].valid_to.isoformat()=='1950-03-01T00:00:00+00:00'
    assert rows[1].valid_to.isoformat()=='1951-02-01T00:00:00+00:00'
    assert rows[0].value==-1.32
