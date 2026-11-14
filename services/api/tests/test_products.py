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

def test_idempotent_product_keeps_raw_and_previous_on_failure(tmp_path, monkeypatch):
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
    # A corrected datum/method must be published even with identical original bytes.
    corrected=p.model_copy(update={'unit':'m sobre EGM2008','method_version':'datum-corrected'})
    assert publish(corrected,raw,'.txt',tmp_path)=='stored'
    assert read_product(p.id,tmp_path).unit=='m sobre EGM2008'
    # A changed native asset cannot be hidden by an unchanged display subset.
    changed=raw+b' changed native cell outside view'
    changed_sha=hashlib.sha256(changed).hexdigest()
    changed_product=corrected.model_copy(update={'checksum_sha256':changed_sha,'byte_size':len(changed),'raw_file':f'test-product/assets/{changed_sha}.txt'})
    assert publish(changed_product,changed,'.txt',tmp_path)=='stored'
    assert len(list(tmp_path.glob('*/revisions/*.json')))==3
    # Budget exhaustion is checked before publishing either the original or pointer.
    monkeypatch.setenv('EARTH_ECHO_PRODUCT_STORE_MAX_BYTES','32000000')
    with (tmp_path/'reserved.bin').open('wb') as reserved:
        reserved.truncate(32_000_000)
    rejected=changed_product.model_copy(update={'method_version':'not-published'})
    with pytest.raises(OSError,match='last valid products preserved'):
        publish(rejected,changed,'.txt',tmp_path)
    assert read_product(p.id,tmp_path)==changed_product
    assert len(list(tmp_path.glob('*/revisions/*.json')))==3

def test_scheduler_cadence_failure_recovery_and_os_lock(tmp_path, monkeypatch):
    path = tmp_path / 'state.json'
    monkeypatch.setattr(refresh, 'state_path', lambda:path)
    calls = []
    def runner(now):
        calls.append(now)
        if len(calls) == 2: raise TimeoutError('offline')
        return 'unchanged' if len(calls) == 3 else 'stored'
    monkeypatch.setattr(refresh, 'jobs', lambda:{'source':(3600,runner)})
    def run(**kwargs):
        return refresh.run_due(executor=lambda name, function, moment:function(moment), **kwargs)
    now = datetime(2026,11,13,tzinfo=timezone.utc)
    first = run(now=now)
    run(now=now+timedelta(minutes=30))
    assert len(calls) == 1
    failed = run(now=now+timedelta(hours=1))['jobs']['source']
    assert failed['last_success_at'] == first['jobs']['source']['last_success_at']
    assert failed['kept_previous'] is True
    run(now=now+timedelta(hours=1,minutes=10))
    assert len(calls) == 2
    recovered = run(now=now+timedelta(hours=1,minutes=16))['jobs']['source']
    assert recovered['status'] == 'unchanged'
    assert recovered['last_success_at'] != recovered['last_change_at']
    with refresh.execution_lock(path.with_suffix('.lock')) as acquired:
        assert acquired
        assert refresh.run_due(force=True)['status'] == 'already_running'


def test_smoc_two_revision_retention_preserves_assets_referenced_by_other_fields(tmp_path):
    import hashlib
    stamp=datetime(2026,11,14,tzinfo=timezone.utc)
    def edition(key,index):
        raw=f'isolated storage exercise edition{index}'.encode();sha=hashlib.sha256(raw).hexdigest()
        p=ScientificProduct(id=key,source_id='D14',title='Storage test fixture',collection_id='isolated-test',product_version=str(index),
            variable='isolated-test',unit='m/s',native_unit='m/s',kind='forecast',representation='table',retrieved_at=stamp,ingested_at=stamp,
            original_url='https://example.org/isolated-test',license_url='https://example.org',attribution='Test only',checksum_sha256=sha,byte_size=len(raw),raw_file=f'shared/{sha}.txt',
            coverage='Isolated storage test only',cadence_seconds=86400,method_version='test',limitation='Never scientific/app data',
            verification=Verification(method='storage fixture',original_url='https://example.org',checked_at=stamp,expected='fixture',actual='fixture',passed=True))
        publish(p,raw,'.txt',tmp_path)
        return p
    v=edition('d14-smoc-v-total',1)
    for i in range(1,4):u=edition('d14-smoc-u-total',i)
    assert len(list((tmp_path/u.id/'revisions').glob('*.json')))==2
    assert (tmp_path/v.raw_file).exists()  # old u revision pruned; v still needs it
    edition(v.id,2);edition(v.id,3)
    assert not (tmp_path/v.raw_file).exists()
    assert len(list(tmp_path.glob('shared/*.txt')))==2
    assert read_product(u.id,tmp_path).product_version=='3'


def test_total_job_deadline_keeps_valid_and_continues_other_source(tmp_path, monkeypatch):
    import subprocess
    from types import SimpleNamespace
    path = tmp_path/'state.json'
    moment = datetime(2026,11,13,tzinfo=timezone.utc)
    previous = (moment-timedelta(days=1)).isoformat()
    path.write_text(json.dumps({'jobs':{'slow':{'last_success_at':previous, 'last_change_at':previous}}}))
    monkeypatch.setattr(refresh, 'state_path', lambda:path)
    monkeypatch.setattr(refresh, 'jobs', lambda:{'slow':(3600,None), 'other':(3600,None)})
    calls = []
    def spawn(args, timeout):
        calls.append((args, {'timeout':timeout}))
        if args[-2] == 'slow':
            raise TimeoutError(f'Source exceeded {timeout} seconds; worker tree terminated, previous retained')
        return SimpleNamespace(returncode=0, stdout='{"status":"unchanged"}')
    monkeypatch.setattr(refresh, 'run_source_worker', spawn)
    state = refresh.run_due(now=moment)
    assert state['jobs']['slow']['status'] == 'failed'
    assert state['jobs']['slow']['kept_previous'] is True
    assert state['jobs']['slow']['last_success_at'] == previous
    assert 'worker tree terminated' in state['jobs']['slow']['error']
    assert state['jobs']['other']['status'] == 'unchanged'
    assert len(calls) == 2 and calls[0][1]['timeout'] == 180
    assert calls[0][0][-2:] == ['slow', moment.isoformat()]


def test_derived_inputs_trigger_without_waiting_and_recover_after_restart(tmp_path, monkeypatch):
    path = tmp_path/'state.json'
    product = tmp_path/'products'/'native'/'current.json'
    product.parent.mkdir(parents=True)
    product.write_bytes(b'first committed revision')
    monkeypatch.setattr(refresh, 'state_path', lambda:path)
    monkeypatch.setattr(refresh, 'products_root', lambda:tmp_path/'products')
    monkeypatch.setattr(refresh, 'DERIVED_INPUTS', {'derived':('native',)})
    calls = []
    def runner(moment):
        calls.append(product.read_bytes())
        return 'stored'
    monkeypatch.setattr(refresh, 'jobs', lambda:{'derived':(43200,runner)})
    def run(moment):
        return refresh.run_due(now=moment, executor=lambda name, fn, now:fn(now))
    now = datetime(2026,11,14,tzinfo=timezone.utc)
    first = run(now)['jobs']['derived']
    run(now+timedelta(minutes=1))
    assert len(calls) == 1
    # Native publish survived, but the upstream worker's success state did not.
    # Every scan reloads the persisted checkpoint; no in-memory invalidation.
    product.write_bytes(b'new committed revision, upstream state still running')
    second = run(now+timedelta(minutes=2))['jobs']['derived']
    assert len(calls) == 2
    assert second['successful_input_revisions'] != first['successful_input_revisions']
    assert second['attempted_input_revisions'] == second['successful_input_revisions']
    run(now+timedelta(minutes=3))
    assert len(calls) == 2  # Unchanged native input does not retrigger.


def test_derived_dependency_failure_respects_retry_and_new_input_invalidates(tmp_path, monkeypatch):
    path = tmp_path/'state.json'
    product = tmp_path/'products'/'native'/'current.json'
    product.parent.mkdir(parents=True)
    product.write_bytes(b'valid revision')
    monkeypatch.setattr(refresh, 'state_path', lambda:path)
    monkeypatch.setattr(refresh, 'products_root', lambda:tmp_path/'products')
    monkeypatch.setattr(refresh, 'DERIVED_INPUTS', {'derived':('native',)})
    calls = []
    def runner(moment):
        calls.append(moment)
        if not product.exists() or product.read_bytes() == b'bad revision':
            raise ValueError('Input absent or inconsistent, keep last valid result')
        return 'stored'
    monkeypatch.setattr(refresh, 'jobs', lambda:{'derived':(43200,runner)})
    def run(minutes):
        return refresh.run_due(now=now+timedelta(minutes=minutes),executor=lambda name, fn, moment:fn(moment))['jobs']['derived']
    now = datetime(2026,11,14,tzinfo=timezone.utc)
    valid = run(0)
    product.write_bytes(b'bad revision')
    failed = run(1)
    assert failed['status'] == 'failed' and failed['kept_previous']
    assert failed['successful_input_revisions'] == valid['successful_input_revisions']
    run(2)
    assert len(calls) == 2  # Same failed input does not retry every minute.
    run(16)
    assert len(calls) == 3  # Normal 15-minute recovery attempt.
    product.unlink()
    assert run(17)['status'] == 'failed'
    run(18)
    assert len(calls) == 4  # Missing input also respects backoff.
    product.write_bytes(b'repaired revision')
    recovered = run(19)
    assert len(calls) == 5 and recovered['status'] == 'stored'
    assert recovered['attempted_input_revisions'] == recovered['successful_input_revisions']


def test_derived_uses_new_upstream_in_same_scan(tmp_path, monkeypatch):
    path = tmp_path/'state.json'
    product = tmp_path/'products'/'native'/'current.json'
    product.parent.mkdir(parents=True)
    monkeypatch.setattr(refresh, 'state_path', lambda:path)
    monkeypatch.setattr(refresh, 'products_root', lambda:tmp_path/'products')
    monkeypatch.setattr(refresh, 'DERIVED_INPUTS', {'derived':('native',)})
    observed = []
    def source(now):
        product.write_bytes(b'new upstream')
        return 'stored'
    def derived(now):
        observed.append(product.read_bytes())
        return 'stored'
    monkeypatch.setattr(refresh, 'jobs', lambda:{'source':(43200,source),'derived':(43200,derived)})
    state = refresh.run_due(now=datetime(2026,11,14,tzinfo=timezone.utc),executor=lambda name, fn, now:fn(now))
    assert observed == [b'new upstream']
    assert state['jobs']['derived']['successful_input_revisions'] == refresh.input_revisions('derived')
