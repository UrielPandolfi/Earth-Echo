"""Single local scheduler, persistent due times and OS lock released on process death."""
import asyncio
import json
import os
from contextlib import contextmanager, asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from earth_echo.paths import repo_root
from earth_echo.storage.products import atomic_json, publish
from earth_echo.connectors.ocean_fields import PRODUCTS, fetch_ocean
from earth_echo.ingest.feeds import refresh_usgs, refresh_kp, refresh_kp_forecast

def state_path() -> Path:
    return repo_root() / 'data/real/refresh/state.json'

def status() -> dict:
    path = state_path()
    state = json.loads(path.read_bytes()) if path.exists() else {'jobs':{}}
    state['enabled'] = os.getenv('EARTH_ECHO_REFRESH_ENABLED', '1') == '1'
    scanned=state.get('last_scan_at')
    state['recent_scan'] = scanned is not None and datetime.now(timezone.utc)-datetime.fromisoformat(scanned)<timedelta(minutes=3)
    state['note'] = 'Cadencia local mientras la API o refresh:watch estén encendidos; lock del sistema, recuperación al reiniciar. Las fechas del dato no son las fechas de descarga.'
    return state

@contextmanager
def execution_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open('a+b')
    acquired = False
    try:
        if path.stat().st_size == 0:
            handle.write(b'0'); handle.flush()
        handle.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except (OSError, BlockingIOError):
            pass
        yield acquired
    finally:
        if acquired:
            handle.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_UN)
        handle.close()

def _ocean(key, now):
    return publish(*fetch_ocean(key, now))

def jobs() -> dict:
    from earth_echo.connectors.nasa_subsets import fetch_modis
    from earth_echo.connectors.ecmwf_fields import fetch_ecmwf
    from earth_echo.connectors.oisst import fetch_oisst
    from earth_echo.connectors.cneos import fetch_sentry
    from earth_echo.connectors.geology_products import fetch_gvp, fetch_tsunami
    from earth_echo.connectors.climate_indices import fetch_oni
    from earth_echo.connectors.aftershocks import fetch_oaf
    from earth_echo.connectors.terrain import fetch_dem
    from earth_echo.connectors.lhasa import fetch_lhasa
    from earth_echo.connectors.marine_heatwaves import fetch_mhw
    from earth_echo.connectors.ibtracs import fetch_ibtracs
    def modis(product, region, now):
        results = fetch_modis(product,region,now)
        return 'unchanged' if all(r=='unchanged' for r in results) else 'stored'
    return {
        **{key:(86400, lambda now, key=key:_ocean(key, now)) for key in PRODUCTS},
        'd21-events':(3600, refresh_usgs), 'd28-kp':(10800, refresh_kp), 'd28-kp-forecast':(10800, refresh_kp_forecast),
        **{f'{p.lower()}-{r}':(86400, lambda now,p=p,r=r:modis(p,r,now)) for p in ['MOD13Q1','MOD11A2'] for r in ['pampa','amazonia']},
        'd07-ifs-24h':(43200,fetch_ecmwf),
        'd13-oisst-global':(86400,fetch_oisst), 'd23-holocene-inventory':(604800,fetch_gvp),
        'd29-sentry':(86400,fetch_sentry), 'd27-tsunami-messages':(900,fetch_tsunami),
        'd48-oni-history':(604800,fetch_oni), 'd22-oaf-recent':(3600,fetch_oaf),
        'd30-dem-pampa':(2592000,fetch_dem), 'd24-lhasa-bc':(43200,fetch_lhasa), 'd16-mhw-monthly':(86400,fetch_mhw),
        'd47-cyclone-tracks':(86400,fetch_ibtracs),
    }

def run_due(*, now: datetime | None = None, force: bool = False, only: set[str] | None = None) -> dict:
    moment = now or datetime.now(timezone.utc)
    path = state_path()
    with execution_lock(path.with_suffix('.lock')) as acquired:
        if not acquired:
            return {'status':'already_running'}
        state = json.loads(path.read_bytes()) if path.exists() else {'jobs':{}}
        for name, (seconds, runner) in jobs().items():
            if only is not None and name not in only:
                continue
            previous = state['jobs'].get(name, {})
            due = previous.get('next_attempt_at')
            if not force and due and datetime.fromisoformat(due) > moment:
                continue
            # Persist BEFORE I/O, so a killed process retries after a bounded delay.
            entry = {**previous, 'last_attempt_at':moment.isoformat(), 'status':'running', 'next_attempt_at':(moment+timedelta(minutes=15)).isoformat()}
            state['jobs'][name] = entry
            atomic_json(path, state)
            try:
                result = runner(moment)
                entry.update(status=result, last_success_at=moment.isoformat(), error=None,
                    kept_previous=False,
                    next_attempt_at=(moment+timedelta(seconds=seconds)).isoformat())
                if result != 'unchanged':
                    entry['last_change_at'] = moment.isoformat()
            except Exception as error:
                entry.update(status='failed', error=f'{type(error).__name__}: {error}', kept_previous=True)
            state['heartbeat_at'] = datetime.now(timezone.utc).isoformat()
            atomic_json(path, state)
        state['last_scan_at']=(now or datetime.now(timezone.utc)).isoformat()
        state['worker_pid']=os.getpid()
        atomic_json(path,state)
        return state

async def watch(stop: asyncio.Event):
    while not stop.is_set():
        await asyncio.to_thread(run_due)
        try:
            await asyncio.wait_for(stop.wait(), timeout=60)
        except TimeoutError:
            pass

@asynccontextmanager
async def lifespan(app):
    stop = asyncio.Event()
    task = asyncio.create_task(watch(stop)) if os.getenv('EARTH_ECHO_REFRESH_ENABLED', '1') == '1' else None
    try:
        yield
    finally:
        stop.set()
        if task:
            await task
