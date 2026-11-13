"""Instantáneas de feeds públicos. Un fallo no borra la anterior ni pasa a DEMO."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from earth_echo.catalog.load import file_sha256
from earth_echo.connectors.public_feeds import (
    SWPC_KP_URL,
    USGS_QUERY,
    FeedSchemaError,
    loads_json,
    parse_planetary_kp,
    parse_usgs_events,
    usgs_query,
)
from earth_echo.paths import repo_root

CADENCE = {
    "d21-events": timedelta(hours=1),
    "d28-kp": timedelta(hours=3),
}


def feeds_dir() -> Path:
    path = repo_root() / "data" / "real" / "feeds"
    path.mkdir(parents=True, exist_ok=True)
    return path


def classify_failure(error: Exception) -> str:
    if isinstance(error, FeedSchemaError):
        text = str(error).lower()
        if "esquema" in text or "features" in text or "time_tag" in text:
            return "schema"
        return "format"
    if isinstance(error, HTTPError):
        if error.code in {401, 403}:
            return "authentication"
        if error.code == 429:
            return "quota"
        return "network"
    if isinstance(error, (TimeoutError, URLError)):
        return "network"
    return "network"


def _get(url: str) -> bytes:
    from earth_echo.connectors.http import download
    return download(url, max_bytes=4_000_000)[0]


def _write_snapshot(name: str, payload: dict) -> str:
    target = feeds_dir() / f"{name}.json"
    raw = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if target.is_file() and file_sha256(target) == __import__("hashlib").sha256(raw).hexdigest():
        return "unchanged"
    temporary = target.with_suffix(".tmp")
    temporary.write_bytes(raw)
    temporary.replace(target)
    return "stored"


def publish_parsed(name: str, payload: dict) -> str:
    return _write_snapshot(name, payload)


def seed_archived_feeds(now: datetime | None = None) -> None:
    moment = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")
    root = repo_root()
    usgs = json.loads((root / "data/samples/d21-usgs/recent-m5.geojson").read_text(encoding="utf-8"))
    kp = json.loads((root / "data/samples/d28-swpc/planetary-k-index.json").read_text(encoding="utf-8"))
    publish_parsed(
        "d21-events",
        {
            "source_id": "D21",
            "retrieved_at": moment,
            "query": USGS_QUERY,
            "geometry_kind": "points",
            "note": "Sismos observados de magnitud mayor o igual a 5. No son pronósticos de réplicas.",
            "events": parse_usgs_events(usgs),
        },
    )
    publish_parsed(
        "d28-kp",
        {
            "source_id": "D28",
            "retrieved_at": moment,
            "query": SWPC_KP_URL,
            "geometry_kind": "global_index",
            "unit": "Kp",
            "note": "Índice planetario. No es la intensidad local producida por una fulguración.",
            "rows": parse_planetary_kp(kp),
        },
    )


def refresh_usgs(now: datetime | None = None) -> str:
    moment = now or datetime.now(timezone.utc)
    query = usgs_query(moment)
    raw = _get(query)
    payload = loads_json(raw)
    events = parse_usgs_events(payload)
    return _write_snapshot(
        "d21-events",
        {
            "source_id": "D21",
            "retrieved_at": moment.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "query": query,
            **_archive('d21-events', raw, moment),
            "geometry_kind": "points",
            "note": "Sismos observados de consulta acotada; umbral y ventana en query. No son pronósticos de réplicas. Magnitud y revisión conservadas.",
            "events": events,
        },
    )


def refresh_kp(now: datetime | None = None) -> str:
    moment = now or datetime.now(timezone.utc)
    raw = _get(SWPC_KP_URL)
    rows = parse_planetary_kp(loads_json(raw))
    return _write_snapshot(
        "d28-kp",
        {
            "source_id": "D28",
            "retrieved_at": moment.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "query": SWPC_KP_URL,
            **_archive('d28-kp', raw, moment),
            "geometry_kind": "global_index",
            "unit": "Kp",
            "note": "Índice planetario. No es la intensidad local producida por una fulguración.",
            "rows": rows,
        },
    )

def _archive(name: str, raw: bytes, moment: datetime) -> dict:
    from hashlib import sha256
    checksum = sha256(raw).hexdigest()
    folder = feeds_dir() / 'assets' / name
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f'{checksum}.json'
    if not target.exists():
        target.write_bytes(raw)
    for old in sorted(folder.glob('*.json'), key=lambda p:p.stat().st_mtime, reverse=True)[4:]:
        old.unlink()
    return {'checksum_sha256': checksum, 'byte_size': len(raw), 'raw_file': str(target.relative_to(feeds_dir())),
            'product_version': 'provider-current-schema-v1', 'verification': 'Raw provider JSON retained; normalized count/IDs and values tested independently.'}

def refresh_kp_forecast(now: datetime | None = None) -> str:
    from earth_echo.connectors.swpc_forecast import KP_FORECAST_URL, parse_predicted_kp
    from earth_echo.queries.forecasts import forecast_dir
    from earth_echo.storage.products import atomic_json
    moment = now or datetime.now(timezone.utc)
    raw = _get(KP_FORECAST_URL)
    rows = parse_predicted_kp(loads_json(raw), moment)
    target = forecast_dir() / 'd28-kp-forecast.json'
    payload = {'source_id':'D28', 'product':'noaa-planetary-k-index-forecast', 'product_version':'SWPC-current',
        'retrieved_at':moment.isoformat().replace('+00:00','Z'), 'archived_at':moment.isoformat().replace('+00:00','Z'),
        'issued_at':None, 'initialized_at':None, 'issue_time_basis':'El feed no proporciona emisión ni inicialización; recuperación separada, no sustituye emisión.',
        'unit':'Kp', 'steps':rows, 'probability':None, 'validated_for_use':False,
        'note':'Solo filas predicted; validez de 3 horas. Índice planetario, sin intensidad local.', **_archive('d28-kp-forecast',raw,moment)}
    atomic_json(target,payload)
    return 'stored'


def run_due(now: datetime | None = None, *, force: bool = False) -> list[dict[str, str]]:
    moment = now or datetime.now(timezone.utc)
    log_path = feeds_dir() / "jobs.json"
    state = json.loads(log_path.read_text(encoding="utf-8")) if log_path.is_file() else {"jobs": {}}
    jobs = state.setdefault("jobs", {})
    results = []
    for name, cadence in CADENCE.items():
        previous = jobs.get(name, {})
        last = previous.get("finished_at")
        if not force and isinstance(last, str):
            finished = datetime.fromisoformat(last.replace("Z", "+00:00"))
            if moment - finished < cadence:
                results.append({"job": name, "status": "skipped", "error_class": ""})
                continue
        runner = refresh_usgs if name == "d21-events" else refresh_kp
        try:
            status = runner(moment)
            jobs[name] = {
                "finished_at": moment.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "status": status,
                "error_class": "",
                "kept_previous": False,
            }
            results.append({"job": name, "status": status, "error_class": ""})
        except Exception as error:
            jobs[name] = {
                "finished_at": previous.get("finished_at"),
                "status": "failed",
                "error_class": classify_failure(error),
                "kept_previous": True,
                "attempted_at": moment.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            results.append({"job": name, "status": "failed", "error_class": jobs[name]["error_class"]})
    attempts = state.setdefault("attempts", [])
    attempts.append({"at": moment.strftime("%Y-%m-%dT%H:%M:%SZ"), "results": results})
    state["attempts"] = attempts[-20:]
    log_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return results
