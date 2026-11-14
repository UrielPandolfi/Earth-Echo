from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import URLError
import io
import json
import zipfile

import pytest
import earth_echo.connectors.seasonal_monthly as module
from earth_echo.storage.products import publish, read_product

FIXTURE = Path(__file__).resolve().parents[3] / 'data/samples/integrations/seas5-monthly-202611.zip'
NOW = datetime(2026, 11, 14, 18, tzinfo=timezone.utc)


@pytest.fixture(scope='module')
def files():
    with zipfile.ZipFile(FIXTURE) as archive:
        return {name: archive.read(name) for name in json.loads(archive.read('manifest.json'))['assets']}


def test_real_monthly_values_calendar_grid_and_forecast_times(files):
    products, raw = module.products_from_files(files, NOW)
    temperature, rain, amazon_temperature, amazon_rain = products
    assert [p.samples[0].value for p in products] == [19.2, 108.5, 28, 227.5]
    assert [s.value for s in rain.samples] == [108.5, 128.7, 125.4, 118.8, 112.3, 90.2, 47.9]
    assert temperature.initialized_at.isoformat() == '2026-11-01T00:00:00+00:00'
    assert temperature.valid_to.isoformat() == '2027-06-01T00:00:00+00:00'
    assert [s.attributes['calendar_days'] for s in rain.samples] == ['30', '31', '31', '28', '31', '30', '31']
    assert all(p.kind == 'forecast' and p.representation == 'time_series' and p.observed_at is None and p.issued_at is None for p in products)
    assert all(s.latitude is None and s.longitude is None and s.probability is None for p in products for s in p.samples)
    assert len({p.checksum_sha256 for p in products}) == 1
    assert temperature.samples[0].attributes['native_latitude'] == '-35.550354'
    assert amazon_rain.samples[0].attributes['native_longitude'] == '-60.576935'
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        assert all(archive.read(name) == content for name, content in files.items())
        manifest = json.loads(archive.read('manifest.json'))
        assert 'actual calendar-month seconds' in manifest['provider_transform']


def test_json_csv_units_masks_coords_and_run_changes_rejected(files):
    for name, key, value, match in [
        ('monthly.json', 'monthly_units', {'time': 'iso8601', 'temperature_2m_mean': 'K', 'precipitation_mean': 'mm'}, 'units changed'),
        ('monthly.json', 'longitude', -61.5, 'coordinates/elevation disagree'),
        ('monthly.json', 'timezone', 'America/Argentina/Buenos_Aires', 'GMT/UTC'),
    ]:
        altered = dict(files); locations = json.loads(altered[name]); locations[0][key] = value
        altered[name] = json.dumps(locations).encode()
        with pytest.raises(ValueError, match=match): module.products_from_files(altered, NOW)
    altered = dict(files); altered['monthly.csv'] = altered['monthly.csv'].replace(b',108.50', b',0.00', 1)
    with pytest.raises(ValueError, match='values/mask/months disagree'): module.products_from_files(altered, NOW)
    altered = dict(files); meta = json.loads(altered['meta-after.json']); meta['last_run_modification_time'] += 60
    altered['meta-after.json'] = json.dumps(meta).encode()
    with pytest.raises(ValueError, match='run changed'): module.products_from_files(altered, NOW)
    # Coordinate tampering in both encodings still fails independent O320 roots.
    altered = dict(files); altered['monthly.json'] = altered['monthly.json'].replace(b'-61.363617', b'-61.500000')
    altered['monthly.csv'] = altered['monthly.csv'].replace(b'-61.363617', b'-61.500000')
    with pytest.raises(ValueError, match='O320 nearest cell'): module.products_from_files(altered, NOW)
    meta = json.loads(files['meta-before.json'])
    too_early = datetime.fromtimestamp(meta['last_run_modification_time'], timezone.utc) + timedelta(minutes=5)
    with pytest.raises(ValueError, match='not yet stable'): module.products_from_files(files, too_early)


def test_zero_and_null_are_distinct_and_no_double_conversion(files):
    altered = dict(files); locations = json.loads(altered['monthly.json'])
    locations[0]['monthly']['precipitation_mean'][:2] = [0, None]
    altered['monthly.json'] = json.dumps(locations).encode()
    altered['monthly.csv'] = altered['monthly.csv'].replace(b',108.50', b',0.00', 1).replace(b',128.70', b',', 1)
    products, _ = module.products_from_files(altered, NOW)
    assert [s.value for s in products[1].samples[:3]] == [0, None, 125.4]
    assert products[0].samples[0].value == 19.2
    assert products[1].samples[1].quality.startswith('missing:')
    leap = datetime(2028, 2, 1, tzinfo=timezone.utc)
    assert (module.month_after(leap, 1) - leap).days == 29


def test_bounded_fetch_shared_asset_idempotence_outage_and_recovery(files, tmp_path, monkeypatch):
    monkeypatch.setattr(module, 'reserve_calls', lambda **kwargs: None)
    offline = False
    requested = []
    def download(url, **kwargs):
        requested.append(url)
        if offline: raise URLError('controlled outage')
        if url == module.META: return files['meta-before.json'], {}
        assert 'models=ecmwf_seas5&' in url and 'elevation=nan%2Cnan' in url
        assert kwargs['max_bytes'] == 200_000
        return files['monthly.csv' if url.endswith('&format=csv') else 'monthly.json'], {}
    monkeypatch.setattr(module, 'download', download)
    monkeypatch.setattr(module, 'publish', lambda p, raw, suffix: publish(p, raw, suffix, tmp_path))
    assert module.fetch_seasonal_monthly(NOW) == 'stored'
    before = read_product('d09-seas5-pampa-precipitacion', tmp_path)
    assert module.fetch_seasonal_monthly(NOW + timedelta(days=1)) == 'unchanged'
    assert len(list(tmp_path.glob('shared/*.zip'))) == 1
    assert len(list(tmp_path.glob('*/revisions/*.json'))) == 4
    assert len(requested) == 8
    offline = True
    with pytest.raises(URLError): module.fetch_seasonal_monthly(NOW)
    assert read_product(before.id, tmp_path) == before and before.data_mode == 'real'
    offline = False
    assert module.fetch_seasonal_monthly(NOW) == 'unchanged'
