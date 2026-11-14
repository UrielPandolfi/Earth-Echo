"""One registered source; child lock survives parent death, parent owns state."""
import json
import os
import sys
import threading
from contextlib import contextmanager
from datetime import datetime,timezone
from earth_echo.settings import get_settings
from earth_echo.ops.refresh import jobs,execution_lock,state_path,job_timeout


@contextmanager
def child_deadline(seconds):
    # Ends this interpreter even if its parent/reloader/venv launcher dies.
    # The OS releases its source lock; atomic publication preserves old data.
    def expired():
        try:print(json.dumps({'error':'Source child hard deadline exceeded; previous retained'}),flush=True)
        finally:os._exit(124)
    timer=threading.Timer(seconds,expired);timer.daemon=True;timer.start()
    try:yield
    finally:timer.cancel()


def run_registered(name,moment):
    if moment.utcoffset() is None:raise ValueError('Job attempt requires UTC offset')
    # Resolve registered name before building a path; arbitrary CLI input
    # cannot create a lock outside this fixed registry.
    runner=jobs()[name][1]
    with execution_lock(state_path().parent/'job-locks'/(name+'.lock')) as acquired:
        if not acquired:raise RuntimeError('Source child is already running; no overlapping ingestion')
        with child_deadline(job_timeout(name)):
            return runner(moment.astimezone(timezone.utc))


def main():
    try:
        get_settings()
        name, stamp = sys.argv[1:]
        moment = datetime.fromisoformat(stamp)
        result = run_registered(name,moment)
        print(json.dumps({'status': result}))
    except Exception as error:
        print(json.dumps({'error': f'{type(error).__name__}: {error}'}))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
