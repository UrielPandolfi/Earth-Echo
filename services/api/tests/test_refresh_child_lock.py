from datetime import datetime,timedelta,timezone
from pathlib import Path
import os
import subprocess
import sys
import time
import pytest
from earth_echo.tools import refresh_job
from earth_echo.ops import refresh


def test_child_lock_blocks_overlap_even_without_parent_lock_and_releases_on_death(tmp_path,monkeypatch):
    lock=tmp_path/'job-locks/source.lock';ready=tmp_path/'ready'
    script='''from pathlib import Path
import sys
from earth_echo.ops.refresh import execution_lock
with execution_lock(Path(sys.argv[1])) as held:
    if not held:raise RuntimeError('Test failed to acquire child lock')
    Path(sys.argv[2]).write_text('held')
    sys.stdin.read(1)
'''
    child=subprocess.Popen([sys.executable,'-c',script,str(lock),str(ready)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0,start_new_session=os.name!='nt')
    calls=[]
    monkeypatch.setattr(refresh_job,'state_path',lambda:tmp_path/'state.json')
    monkeypatch.setattr(refresh_job,'jobs',lambda:{'source':(3600,lambda stamp:calls.append(stamp) or 'stored')})
    stamp=datetime(2026,11,14,12,tzinfo=timezone(timedelta(hours=-3)))
    try:
        deadline=time.monotonic()+8
        while not ready.exists() and child.poll() is None and time.monotonic()<deadline:time.sleep(.02)
        assert ready.exists(), 'Controlled child did not acquire its lock'
        # Global parent lock is deliberately absent: a restarted parent still
        # cannot overlap the original source child after its parent has died.
        with pytest.raises(RuntimeError,match='already running'):refresh_job.run_registered('source',stamp)
        assert calls==[]
        refresh.terminate_worker(child)
        assert refresh_job.run_registered('source',stamp)=='stored'
        assert calls==[datetime(2026,11,14,15,tzinfo=timezone.utc)]
        with pytest.raises(KeyError):refresh_job.run_registered('../outside',stamp)
        assert not (tmp_path/'outside.lock').exists()
    finally:
        if child.poll() is None:refresh.terminate_worker(child)
        for stream in (child.stdin,child.stdout,child.stderr):stream.close()


def test_scheduler_normalizes_aware_timestamps_to_utc_and_rejects_naive(tmp_path,monkeypatch):
    monkeypatch.setattr(refresh,'state_path',lambda:tmp_path/'state.json')
    monkeypatch.setattr(refresh,'jobs',lambda:{'source':(3600,lambda now:'unchanged')})
    stamp=datetime(2026,11,14,12,tzinfo=timezone(timedelta(hours=-3)))
    state=refresh.run_due(now=stamp,executor=lambda n,r,t:r(t))
    assert state['jobs']['source']['last_attempt_at']=='2026-11-14T15:00:00+00:00'
    with pytest.raises(ValueError,match='aware timestamp'):refresh.run_due(now=stamp.replace(tzinfo=None))


def test_actual_worker_timeout_terminates_redirector_tree_and_releases_lock(tmp_path):
    lock=tmp_path/'deadline.lock'
    script='''from pathlib import Path
import sys,time
from earth_echo.ops.refresh import execution_lock
with execution_lock(Path(sys.argv[1])) as held:
    if not held:raise RuntimeError('Test could not acquire lock')
    time.sleep(20)
'''
    with pytest.raises(TimeoutError,match='worker tree terminated'):
        refresh.run_source_worker([sys.executable,'-c',script,str(lock)],2)
    assert lock.exists()
    with refresh.execution_lock(lock) as held:assert held


def test_orphan_interpreter_self_deadline_releases_source_lock_after_launcher_dies(tmp_path):
    lock=tmp_path/'orphan.lock';ready=tmp_path/'ready'
    script='''from pathlib import Path
import sys,time
from earth_echo.ops.refresh import execution_lock
from earth_echo.tools.refresh_job import child_deadline
with child_deadline(2),execution_lock(Path(sys.argv[1])) as held:
    if not held:raise RuntimeError('Test lock unavailable')
    Path(sys.argv[2]).write_text('held')
    time.sleep(20)
'''
    child=subprocess.Popen([sys.executable,'-c',script,str(lock),str(ready)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0,start_new_session=os.name!='nt')
    try:
        deadline=time.monotonic()+8
        while not ready.exists() and child.poll() is None and time.monotonic()<deadline:time.sleep(.02)
        assert ready.exists()
        child.terminate()  # Intentional launcher-only death, not tree kill.
        child.communicate(timeout=6)  # EOF after orphan's own two-second limit.
        with refresh.execution_lock(lock) as held:assert held
    finally:
        if child.poll() is None:refresh.terminate_worker(child)
        child.stdout.close();child.stderr.close()


def test_source_self_deadline_exits_without_parent_intervention(tmp_path):
    lock=tmp_path/'self-deadline.lock'
    script='''from pathlib import Path
import sys,time
from earth_echo.ops.refresh import execution_lock
from earth_echo.tools.refresh_job import child_deadline
with child_deadline(.2),execution_lock(Path(sys.argv[1])) as held:
    if not held:raise RuntimeError('Test lock unavailable')
    time.sleep(20)
'''
    child=refresh.run_source_worker([sys.executable,'-c',script,str(lock)],5)
    assert child.returncode==124 and 'hard deadline exceeded' in child.stdout
    with refresh.execution_lock(lock) as held:assert held
