from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import URLError
import csv
import io
import json
import zipfile
import pytest
import earth_echo.connectors.cams_fields as module
from earth_echo.storage.products import publish, read_product

FIXTURE = Path(__file__).resolve().parents[3] / 'data/samples/integrations/cams-global-20261114.zip'
NOW = datetime(2026, 11, 14, 18, 10, tzinfo=timezone.utc)


@pytest.fixture(scope='module')
def files():
    with zipfile.ZipFile(FIXTURE) as archive:
        return {name: archive.read(name) for name in json.loads(archive.read('manifest.json'))['assets']}


def altered_first(files, variable, value):
    altered = dict(files); locations = json.loads(files['batch00.json'])
    locations[0]['hourly'][variable][0] = value
    altered['batch00.json'] = json.dumps(locations).encode()
    blocks = files['batch00.csv'].decode('utf8').split('\n\n')
    rows = list(csv.DictReader(io.StringIO(blocks[1])))
    unit = module.VARIABLES[variable][2]
    rows[0][variable + ' (' + unit + ')'] = '' if value is None else str(value)
    output = io.StringIO(); writer = csv.DictWriter(output, fieldnames=list(rows[0]))
    writer.writeheader(); writer.writerows(rows)
    altered['batch00.csv'] = (blocks[0] + '\n\n' + output.getvalue()).encode()
    return altered


def test_real_global_fields_units_native_centers_and_forecast_instant(files):
    products, raw = module.products_from_files(files, NOW)
    pm25, pm10, dust, aod = products
    assert [p.grid.values[0] for p in products] == [1.4, 2.3, 1, .08]
    assert len({p.checksum_sha256 for p in products}) == 1
    assert all(p.kind == 'forecast' and p.representation == 'field' and p.observed_at is None and p.issued_at is None and p.samples == [] and p.probability is None for p in products)
    assert pm25.grid.width == 30 and pm25.grid.height == 15 and len(pm25.grid.values) == 450
    assert pm25.grid.latitudes == list(range(84, -85, -12))
    assert pm25.grid.longitudes == list(range(-174, 175, 12))
    assert pm25.initialized_at.isoformat() == '2026-11-14T00:00:00+00:00'
    assert pm25.valid_from.isoformat() == '2026-11-15T00:00:00+00:00' and pm25.valid_to is None
    assert pm25.unit == 'μg/m³' and aod.unit == '1'
    assert 'aermr06' in dust.variable and '1,223803' in dust.native_unit
    assert 'columna' in aod.title and 'superficial' in pm25.title
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        assert len(json.loads(archive.read('manifest.json'))['assets']) == 12
        assert all(archive.read(name) == content for name, content in files.items())


def test_missing_zero_and_physical_domain_stay_distinct(files):
    products, _ = module.products_from_files(altered_first(files, 'dust', None), NOW)
    assert products[2].grid.values[0] is None and products[2].grid.missing_cells >= 1
    products, _ = module.products_from_files(altered_first(files, 'dust', 0), NOW)
    assert products[2].grid.values[0] == 0
    with pytest.raises(ValueError, match='negative concentration'):
        module.products_from_files(altered_first(files, 'dust', -1), NOW)


def test_formats_units_geography_run_and_incomplete_batch_reject(files):
    altered = dict(files); locations = json.loads(files['batch00.json'])
    locations[0]['hourly']['pm2_5'][0] = 9
    altered['batch00.json'] = json.dumps(locations).encode()
    with pytest.raises(ValueError, match='JSON/CSV value'): module.products_from_files(altered, NOW)
    locations = json.loads(files['batch00.json']); locations[0]['hourly_units']['aerosol_optical_depth'] = 'μg/m³'
    altered = dict(files); altered['batch00.json'] = json.dumps(locations).encode()
    with pytest.raises(ValueError, match='units changed'): module.products_from_files(altered, NOW)
    altered = dict(files)
    for name in ('batch00.json', 'batch00.csv'): altered[name] = altered[name].replace(b'-174.0', b'-173.6', 1)
    with pytest.raises(ValueError, match='native0.4-degree coordinates'): module.products_from_files(altered, NOW)
    altered = dict(files); meta = json.loads(files['meta-after.json']); meta['last_run_modification_time'] += 1
    altered['meta-after.json'] = json.dumps(meta).encode()
    with pytest.raises(ValueError, match='run changed'): module.products_from_files(altered, NOW)
    altered = dict(files); altered['batch00.json'] = json.dumps(json.loads(files['batch00.json'])[:-1]).encode()
    with pytest.raises(ValueError, match='incomplete global subset'): module.products_from_files(altered, NOW)


def test_one_shared_asset_idempotent_metadata_only_refresh_outage_recovery(files, tmp_path, monkeypatch):
    offline = False; requests = []; reservations = []
    init = module.run_metadata(files['meta-before.json'], NOW)[0]
    resources = {module.META: files['meta-before.json']}
    for i, batch in enumerate(module.BATCHES):
        url = module.request_url(init, batch)
        resources[url], resources[url + '&format=csv'] = files[f'batch{i:02}.json'], files[f'batch{i:02}.csv']
    def download(url, **kwargs):
        requests.append(url)
        if offline: raise URLError('controlled outage')
        return resources[url], {}
    monkeypatch.setattr(module, 'download', download)
    monkeypatch.setattr(module, 'reserve_calls', lambda **kwargs: reservations.append(kwargs))
    monkeypatch.setattr(module, 'products_root', lambda: tmp_path)
    monkeypatch.setattr(module, 'publish', lambda p, raw, suffix: publish(p, raw, suffix, tmp_path))
    assert module.fetch_cams(NOW) == 'stored'
    before = read_product('d12-cams-global-pm25', tmp_path)
    assert len(requests) == 12 and len(reservations) == 10
    assert module.fetch_cams(NOW + timedelta(hours=12)) == 'unchanged'
    assert requests[-2:] == [module.META] * 2 and len(requests) == 14 and len(reservations) == 10
    assert len(list(tmp_path.glob('shared/*.zip'))) == 1 and len(list(tmp_path.glob('*/revisions/*.json'))) == 4
    assert read_product(before.id, tmp_path).retrieved_at == before.retrieved_at
    offline = True
    with pytest.raises(URLError): module.fetch_cams(NOW)
    assert read_product(before.id, tmp_path) == before and before.data_mode == 'real'
    offline = False
    assert module.fetch_cams(NOW) == 'unchanged'
