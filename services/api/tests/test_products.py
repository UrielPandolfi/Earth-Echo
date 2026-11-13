from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import pytest
from earth_echo.connectors.ocean_fields import decode_grid
from earth_echo.ingest.d15_sst import sample_file
from earth_echo.contracts.products import ScientificProduct, Verification
from earth_echo.storage.products import publish, read_product
from earth_echo.ops import refresh

def test_real_netcdf_orientation_units_and_missing():
    # Original archived scientific fixture, independently checked in phase 5.
    from earth_echo.connectors.netcdf_classic import ClassicNetCdf
    ds = ClassicNetCdf(sample_file())
    assert ds.variables['analysed_sst']['attributes']['units'] == 'degree_C'
    assert ds.values('latitude')[0] == pytest.approx(16.525, abs=.0001)
    with pytest.raises(ValueError, match='Unexpected units'):
        decode_grid(sample_file().read_bytes(), 'analysed_sst', 'Kelvin')

def test_idempotent_product_keeps_raw_and_previous_on_failure(tmp_path):
    import hashlib
    raw = b'original science product'
    sha = hashlib.sha256(raw).hexdigest()
    now = datetime.now(timezone.utc)
    p = ScientificProduct(id='test-product', source_id='D15', title='test', collection_id='test', product_version='1',
        variable='sst', unit='degree_C', native_unit='degree_C', kind='observation', representation='table',
        retrieved_at=now, ingested_at=now, original_url='https://example.org/data', license_url='https://example.org',
        attribution='test', checksum_sha256=sha, byte_size=len(raw), raw_file=f'test-product/assets/{sha}.txt',
        coverage='test', cadence_seconds=3600, method_version='test', limitation='fixture only',
        verification=Verification(method='test',original_url='https://example.org',checked_at=now,expected='1',actual='1',passed=True))
    assert publish(p, raw, '.txt', tmp_path) == 'stored'
    assert publish(p, raw, '.txt', tmp_path) == 'unchanged'
    assert len(list(tmp_path.glob('*/revisions/*.json'))) == 1
    with pytest.raises(ValueError):
        publish(p, b'corrupt', '.txt', tmp_path)
    assert read_product(p.id, tmp_path) == p

def test_scheduler_cadence_failure_recovery_and_os_lock(tmp_path, monkeypatch):
    path = tmp_path / 'state.json'
    monkeypatch.setattr(refresh, 'state_path', lambda:path)
    calls = []
    def runner(now):
        calls.append(now)
        if len(calls) == 2: raise TimeoutError('offline')
        return 'unchanged' if len(calls) == 3 else 'stored'
    monkeypatch.setattr(refresh, 'jobs', lambda:{'source':(3600,runner)})
    now = datetime(2026,11,13,tzinfo=timezone.utc)
    first = refresh.run_due(now=now)
    refresh.run_due(now=now+timedelta(minutes=30))
    assert len(calls) == 1
    failed = refresh.run_due(now=now+timedelta(hours=1))['jobs']['source']
    assert failed['last_success_at'] == first['jobs']['source']['last_success_at']
    assert failed['kept_previous'] is True
    refresh.run_due(now=now+timedelta(hours=1,minutes=10))
    assert len(calls) == 2
    recovered = refresh.run_due(now=now+timedelta(hours=1,minutes=16))['jobs']['source']
    assert recovered['status'] == 'unchanged'
    assert recovered['last_success_at'] != recovered['last_change_at']
    with refresh.execution_lock(path.with_suffix('.lock')) as acquired:
        assert acquired
        assert refresh.run_due(force=True)['status'] == 'already_running'
