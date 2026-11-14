from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import URLError
import csv
import io
import json
import zipfile
import pytest
import earth_echo.connectors.glofas_discharge as module
from earth_echo.storage.products import publish, read_product

FIXTURE = Path(__file__).resolve().parents[3] / 'data/samples/integrations/glofas-two-cells-20261114.zip'
NOW = datetime(2026, 11, 14, 18, tzinfo=timezone.utc)


@pytest.fixture(scope='module')
def files():
    with zipfile.ZipFile(FIXTURE) as archive:
        return {name: archive.read(name) for name in json.loads(archive.read('manifest.json'))['assets']}


def changed_values(files, changes):
    """Deliberately alter both encodings so independent science must also reject."""
    altered = dict(files); locations = json.loads(files['discharge.json'])
    blocks = files['discharge.csv'].decode('utf8').split('\n\n')
    rows = list(csv.DictReader(io.StringIO(blocks[1])))
    for variable, day, value in changes:
        locations[0]['daily'][variable][day] = value
        rows[day][variable + ' (m³/s)'] = '' if value is None else str(value)
    output = io.StringIO(); writer = csv.DictWriter(output, fieldnames=list(rows[0]))
    writer.writeheader(); writer.writerows(rows)
    altered['discharge.json'] = json.dumps(locations).encode()
    altered['discharge.csv'] = (blocks[0] + '\n\n' + output.getvalue()).encode()
    return altered


def test_real_discharge_members_mean_and_end_of_24h_epoch(files):
    products, raw = module.products_from_files(files, NOW)
    rosario, manaus = products
    assert [s.value for s in rosario.samples] == [30973.22, 30198.51, 29187.78, 28223.67, 27388.89, 26694.34, 26140.21]
    assert manaus.samples[0].value == 2.3  # Do not call this the main Amazon river.
    assert rosario.samples[0].time.isoformat() == '2026-11-14T00:00:00+00:00'
    assert rosario.samples[0].valid_to.isoformat() == '2026-11-15T00:00:00+00:00'
    assert rosario.samples[0].attributes['native_valid_time'] == '2026-11-15T00:00:00+00:00'
    assert rosario.valid_to.isoformat() == '2026-11-21T00:00:00+00:00'
    assert rosario.samples[0].attributes['returned_elevation_m'] is None
    assert all(p.kind == 'forecast' and p.unit == 'm³/s' and p.initialized_at is None and p.issued_at is None and p.observed_at is None for p in products)
    assert all(s.latitude is None and s.longitude is None and s.probability is None for p in products for s in p.samples)
    assert len(json.loads(rosario.samples[0].attributes['ensemble_values_m3_s'])) == 51
    assert rosario.samples[0].attributes['member00_control_m3_s'] == '30973.21'
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        assert all(archive.read(name) == content for name, content in files.items())
        assert 'no per-value run ID' in json.loads(archive.read('manifest.json'))['version_scope']


def test_mean_is_independently_checked_with_explicit_precision_bound(files):
    # API control30973.21, mean30973.22: Float32 sum/decimal rounding is real.
    assert module.checked_mean([30973.21] * 51, 30973.22) == 30973.22
    with pytest.raises(ValueError, match='51-member mean disagrees'):
        module.products_from_files(changed_values(files, [(module.MEAN, 0, 30974.22)]), NOW)


def test_partial_ensemble_remains_missing_and_zero_is_valid(files):
    altered = changed_values(files, [(key, 0, 0) for key in [*module.MEMBERS, module.MEAN]] + [('river_discharge_member01', 1, None)])
    products, _ = module.products_from_files(altered, NOW)
    zero, missing = products[0].samples[:2]
    assert zero.value == 0 and zero.attributes['members_present'] == '51'
    assert missing.value is None and missing.attributes['members_present'] == '50'
    assert missing.attributes['provider_mean_m3_s'] == '30198.51'
    assert missing.quality.startswith('missing:')
    assert module.checked_mean([None] * 51, None) is None


def test_units_grid_run_and_independent_csv_disagreement_reject(files):
    altered = dict(files); altered['discharge.json'] = altered['discharge.json'].replace('m³/s'.encode(), b'mm')
    with pytest.raises(ValueError, match='units or 51-member identity'): module.products_from_files(altered, NOW)
    altered = dict(files); altered['discharge.csv'] = altered['discharge.csv'].replace(b'30973.21', b'30973.20', 1)
    with pytest.raises(ValueError, match='values/mask/date disagree'): module.products_from_files(altered, NOW)
    altered = dict(files)
    for name in ('discharge.json', 'discharge.csv'): altered[name] = altered[name].replace(b'-60.674995', b'-60.724995')
    with pytest.raises(ValueError, match='native 0.05-degree cell'): module.products_from_files(altered, NOW)
    altered = dict(files); meta = json.loads(files['meta-after.json']); meta['last_run_modification_time'] += 1
    altered['meta-after.json'] = json.dumps(meta).encode()
    with pytest.raises(ValueError, match='metadata changed during'): module.products_from_files(altered, NOW)


def test_shared_ingestion_idempotence_network_failure_and_recovery(files, tmp_path, monkeypatch):
    offline = False
    def download(url, **kwargs):
        if offline: raise URLError('controlled outage')
        if url == module.META: return files['meta-before.json'], {}
        assert 'models=forecast_v4&' in url and 'ensemble=true' in url and 'cell_selection=nearest' in url
        return files['discharge.csv' if url.endswith('&format=csv') else 'discharge.json'], {}
    monkeypatch.setattr(module, 'download', download)
    monkeypatch.setattr(module, 'publish', lambda p, raw, suffix: publish(p, raw, suffix, tmp_path))
    assert module.fetch_glofas(NOW) == 'stored'
    before = read_product('d10-glofas-rosario', tmp_path)
    assert module.fetch_glofas(NOW + timedelta(days=1)) == 'unchanged'
    assert len(list(tmp_path.glob('shared/*.zip'))) == 1 and len(list(tmp_path.glob('*/revisions/*.json'))) == 2
    offline = True
    with pytest.raises(URLError): module.fetch_glofas(NOW)
    assert read_product(before.id, tmp_path) == before and before.data_mode == 'real'
    offline = False
    assert module.fetch_glofas(NOW) == 'unchanged'
