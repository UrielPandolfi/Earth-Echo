"""Transport representation helpers, without choosing products or scientific meaning."""
import csv
import io
import math
import time
from datetime import datetime, timezone

LICENSE = 'https://open-meteo.com/en/licence'


def number(value):
    if value is None or value in ('', 'NaN', 'nan'):
        return None
    if isinstance(value, bool):
        raise ValueError('Boolean is not a scientific numeric value')
    result = float(value)
    if not math.isfinite(result):
        raise ValueError('Nonfinite value; explicit missing required')
    return result


def csv_sections(raw):
    blocks = raw.decode('utf-8').strip().replace('\r\n', '\n').split('\n\n')
    if len(blocks) != 2:
        raise ValueError('Independent CSV structure changed')
    return [list(csv.DictReader(io.StringIO(block))) for block in blocks]


def rate_wait(entries, stamp, weight):
    """Conservative weighted free-API budget, including two HTTP attempts.

    Metadata endpoints are exempt. Reserve before I/O and keep reservations if
    a worker dies. Lower local caps leave room for small manual probes/rounding.
    """
    if not math.isfinite(weight) or not 0 < weight <= 500:
        raise ValueError('Split Open-Meteo data requests below500 reserved calls')
    wait = 0.0
    for seconds, limit in ((60, 500), (3600, 4500), (86400, 9000)):
        active = sorted((e for e in entries if e['at'] > stamp - seconds), key=lambda e: e['at'])
        used = sum(e['weight'] for e in active)
        for entry in active:
            if used + weight <= limit:
                break
            wait = max(wait, entry['at'] + seconds - stamp)
            used -= entry['weight']
    return wait


def reserve_calls(*, locations, variables, hours):
    from earth_echo.ops.refresh import execution_lock
    from earth_echo.paths import repo_root
    from earth_echo.storage.products import atomic_json
    import json
    weight = 2 * locations * max(1, variables / 10) * max(1, hours / (14 * 24))
    path = repo_root() / 'data/real/refresh/open-meteo-budget.json'
    while True:
        stamp = time.time()
        with execution_lock(path.with_suffix('.lock')) as acquired:
            if not acquired:
                raise RuntimeError('Open-Meteo budget reservation busy; previous retained')
            entries = json.loads(path.read_bytes())['reservations'] if path.exists() else []
            entries = [e for e in entries if e['at'] > stamp - 86400]
            if any(e['at'] > stamp + 60 for e in entries):
                raise ValueError('Clock moved backwards; Open-Meteo budget preserved')
            delay = rate_wait(entries, stamp, weight)
            if delay == 0:
                atomic_json(path, {'reservations': [*entries, {'at': stamp, 'weight': weight}],
                    'method': 'worst-case2attempts × locations × max(1,variables/10) × max(1,hours/336); caps500/min,4500/h,9000/day'})
                return
        if delay > 60:
            next_time = datetime.fromtimestamp(stamp + delay, timezone.utc).isoformat()
            raise RuntimeError('Open-Meteo hourly/daily local budget exhausted until ' + next_time + '; previous retained')
        time.sleep(min(60, delay + .05))
