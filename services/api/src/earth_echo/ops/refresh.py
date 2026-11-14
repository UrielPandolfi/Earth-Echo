"""Single local scheduler, persistent due times and OS lock released on process death."""
import asyncio
import hashlib
import json
import os
import subprocess
import sys
from contextlib import contextmanager, asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from earth_echo.paths import repo_root
from earth_echo.storage.products import atomic_json, publish, products_root
from earth_echo.connectors.ocean_fields import PRODUCTS, fetch_ocean
from earth_echo.ingest.feeds import refresh_usgs, refresh_kp, refresh_kp_forecast

# Fixed scientific dependencies, in upstream-before-derived order in jobs().
# Fingerprint the committed inputs rather than download times: this also catches
# a parent process dying after publish but before its success state was saved.
DERIVED_INPUTS = {
    'd07-derived-fields': tuple(f'd07-ifs-{p}-24h' for p in ('10u', '10v', '2t', '2d')),
    'd34-amoc-annual-trend': ('d34-amoc-monthly',),
}

def input_revisions(name: str) -> dict[str, str]:
    revisions = {}
    for key in DERIVED_INPUTS.get(name, ()):
        try:
            revisions[key] = hashlib.sha256((products_root()/key/'current.json').read_bytes()).hexdigest()
        except OSError as error:
            revisions[key] = f'unavailable:{type(error).__name__}'
    return revisions

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
    from earth_echo.connectors.gdacs import fetch_gdacs
    from earth_echo.connectors.gebco import fetch_gebco
    from earth_echo.connectors.asis import fetch_asis
    from earth_echo.connectors.locusts import fetch_locusts
    from earth_echo.connectors.hydroatlas import fetch_hydroatlas
    from earth_echo.connectors.firms import fetch_firms
    from earth_echo.connectors.volcano_reports import fetch_volcano_reports
    from earth_echo.connectors.glacier_inventory import fetch_glacier_inventory
    from earth_echo.connectors.rapid_transport import fetch_rapid
    from earth_echo.connectors.sentinel_ocean_color import fetch_sentinel_chlorophyll
    from earth_echo.ingest.derived_fields import derive_ifs_fields
    from earth_echo.ingest.transport_trend import derive_transport_trend
    from earth_echo.connectors.era5_arco import fetch_era5
    from earth_echo.connectors.grace_assimilation import fetch_grace
    from earth_echo.connectors.imerg_climatology import fetch_imerg_climatology
    from earth_echo.connectors.glacier_outlines import fetch_glacier_outlines
    from earth_echo.connectors.glacier_global import fetch_glacier_global
    from earth_echo.connectors.sentinel_vegetation import fetch_sentinel_vegetation
    from earth_echo.connectors.nasa_ocean_color import fetch_nasa_chlorophyll
    from earth_echo.connectors.enso_outlook import fetch_enso_outlook
    from earth_echo.connectors.seasonal_monthly import fetch_seasonal_monthly
    from earth_echo.connectors.glofas_discharge import fetch_glofas
    from earth_echo.connectors.cams_fields import fetch_cams
    from earth_echo.connectors.marine_currents import fetch_marine_currents
    from earth_echo.connectors.marine_temperature import fetch_marine_temperature
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
        'd35-cyclone-cap-areas':(21600,fetch_gdacs),
        'd31-gebco-caribe':(2592000,fetch_gebco),
        'd20-asi-s1':(86400,fetch_asis),
        'd19-desert-locust-surveys':(86400,fetch_locusts),
        'd07-derived-fields':(43200,derive_ifs_fields),
        'd32-basins-south-america':(2592000,fetch_hydroatlas),
        'd06-viirs-noaa20-sa':(10800,fetch_firms),
        'd23-weekly-activity-reports':(86400,fetch_volcano_reports),
        'd26-rgi7-alaska-attributes':(2592000,fetch_glacier_inventory),
        'd34-rapid-monthly':(604800,fetch_rapid),
        'd25-s3a-chlorophyll':(86400,fetch_sentinel_chlorophyll),
        'd34-amoc-annual-trend':(604800,derive_transport_trend),
        'd08-era5-air-temperature':(604800,fetch_era5),
        'd33-grace-global':(86400,fetch_grace),
        'd01-imerg-grand-climatology':(2592000,fetch_imerg_climatology),
        'd26-rgi60-patagonia-outlines':(2592000,fetch_glacier_outlines),
        'd26-rgi7-global-large-glaciers':(2592000,fetch_glacier_global),
        'd25-s2-pampa':(86400,fetch_sentinel_vegetation),
        'd17-aqua-chlorophyll-archive':(2592000,fetch_nasa_chlorophyll),
        'd48-roni-outlook-tables':(86400,fetch_enso_outlook),
        'd09-seas5-monthly':(86400,fetch_seasonal_monthly),
        'd10-glofas-discharge':(86400,fetch_glofas),
        'd12-cams-global':(43200,fetch_cams),
        'd14-smoc-native':(86400,fetch_marine_currents),
        'd14-thetao-native':(86400,fetch_marine_temperature),
    }

def execute_job(name, runner, moment):
    """A socket timeout is not a total timeout (DNS and slow bodies can hang)."""
    limits = {'d32-basins-south-america': ('EARTH_ECHO_HYDROATLAS_TIMEOUT_SECONDS', '420'),
        'd12-cams-global': ('EARTH_ECHO_CAMS_TIMEOUT_SECONDS', '420'),
        'd14-smoc-native': ('EARTH_ECHO_MARINE_TIMEOUT_SECONDS', '300'),
        'd14-thetao-native': ('EARTH_ECHO_MARINE_TIMEOUT_SECONDS', '300')}
    variable, default = limits.get(name, ('EARTH_ECHO_REFRESH_JOB_TIMEOUT_SECONDS', '180'))
    timeout = int(os.getenv(variable, default))
    if not 30 <= timeout <= 600:
        raise ValueError('Job timeout must be between 30 and 600 seconds')
    try:
        child = subprocess.run([sys.executable, '-m', 'earth_echo.tools.refresh_job', name, moment.isoformat()],
            cwd=repo_root(), capture_output=True, text=True, timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    except subprocess.TimeoutExpired:
        raise TimeoutError(f'Source exceeded {timeout} seconds; child terminated, previous retained') from None
    try:
        result = json.loads(child.stdout)
    except (ValueError, TypeError):
        raise RuntimeError(f'Source worker failed with exit code {child.returncode}; no valid result') from None
    if child.returncode or result.get('error'):
        raise RuntimeError(result.get('error', f'Source worker exited {child.returncode}'))
    if result.get('status') not in {'stored', 'unchanged'}:
        raise ValueError('Source worker returned an invalid status')
    return result['status']


def run_due(*, now: datetime | None = None, force: bool = False, only: set[str] | None = None, executor=None) -> dict:
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
            inputs = input_revisions(name)
            changed_inputs = bool(inputs) and inputs != previous.get('attempted_input_revisions')
            if not force and not changed_inputs and due and datetime.fromisoformat(due) > moment:
                continue
            # Persist BEFORE I/O, so a killed process retries after a bounded delay.
            attempt=now or datetime.now(timezone.utc)
            entry = {**previous, 'last_attempt_at':attempt.isoformat(), 'status':'running', 'next_attempt_at':(attempt+timedelta(minutes=15)).isoformat()}
            if inputs:
                # An unsuccessful attempt on the SAME revision respects the retry
                # delay. A genuinely new input may trigger one earlier attempt.
                entry['attempted_input_revisions'] = inputs
            state['jobs'][name] = entry
            atomic_json(path, state)
            try:
                result = (executor or execute_job)(name, runner, attempt)
                completed=now or datetime.now(timezone.utc)
                entry.update(status=result, last_success_at=completed.isoformat(), error=None,
                    kept_previous=False,
                    next_attempt_at=(completed+timedelta(seconds=seconds)).isoformat())
                if inputs:
                    entry['successful_input_revisions'] = inputs
                if result != 'unchanged':
                    entry['last_change_at'] = completed.isoformat()
            except Exception as error:
                entry.update(status='failed', error=f'{type(error).__name__}: {error}', kept_previous=previous.get('last_success_at') is not None)
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
