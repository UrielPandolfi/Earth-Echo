"""Descarga muestras públicas pequeñas y fija la integridad de los archivos de referencia.

No descarga el HDF de SMAP ni colecciones mundiales.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from earth_echo.paths import repo_root

USER_AGENT = "EarthEcho/0.1 (viability sample; local phase 1)"
USGS_URL = (
    "https://earthquake.usgs.gov/fdsnws/event/1/query"
    "?format=geojson&starttime=2024-09-01&endtime=2024-09-02&minmagnitude=6&limit=1"
)
CMR_URL = (
    "https://cmr.earthdata.nasa.gov/search/granules.json"
    "?short_name=SPL3SMP_E&page_size=1&sort_key=-start_date"
)
REFERENCE_FILES = (
    "Earth_Echo_Catalogo.json",
    "Earth_Echo_Especificacion.md",
    "Earth Echo Global Environmental Observatory.png",
)


def _get(url: str) -> tuple[int, str, bytes]:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=60) as response:
        body = response.read()
        status = int(response.status)
        content_type = response.headers.get("content-type", "")
    if status != 200:
        raise RuntimeError(f"{url} respondió {status}.")
    return status, content_type, body


def _sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _write_sample(directory: Path, filename: str, body: bytes, sidecar: dict) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / filename).write_bytes(body)
    (directory / "retrieval.json").write_text(
        json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _pin_references(root: Path) -> None:
    files = {}
    for name in REFERENCE_FILES:
        digest = hashlib.sha256()
        with (root / name).open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        files[name] = digest.hexdigest()
    destination = root / "data" / "operational" / "reference_integrity.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps({"algorithm": "sha256", "files": files}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    root = repo_root()
    retrieved_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    usgs_status, usgs_type, usgs_body = _get(USGS_URL)
    _write_sample(
        root / "data" / "samples" / "d21-usgs",
        "event.geojson",
        usgs_body,
        {
            "source_id": "D21",
            "retrieved_at": retrieved_at,
            "request_url": USGS_URL,
            "http_status": usgs_status,
            "content_type": usgs_type,
            "sha256": _sha256(usgs_body),
            "byte_size": len(usgs_body),
            "note": "Muestra de viabilidad de un evento. No es una conexión operativa ni un pronóstico.",
        },
    )
    cmr_status, cmr_type, cmr_body = _get(CMR_URL)
    _write_sample(
        root / "data" / "samples" / "d02-smap",
        "cmr-granule.json",
        cmr_body,
        {
            "source_id": "D02",
            "retrieved_at": retrieved_at,
            "request_url": CMR_URL,
            "http_status": cmr_status,
            "content_type": cmr_type,
            "sha256": _sha256(cmr_body),
            "byte_size": len(cmr_body),
            "science_file_retrieved": False,
            "credential_variables": ["EARTHDATA_USERNAME", "EARTHDATA_PASSWORD"],
            "note": (
                "Metadatos públicos de un gránulo SPL3SMP_E. "
                "El HDF científico no se descargó."
            ),
        },
    )
    _pin_references(root)
    print(f"Muestras guardadas a las {retrieved_at}.")


if __name__ == "__main__":
    main()
