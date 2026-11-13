"""Carga el catálogo de referencia sin reescribirlo."""

import hashlib
import json
from pathlib import Path

from earth_echo.catalog.models import CatalogDocument
from earth_echo.paths import repo_root
from earth_echo.settings import get_settings

REFERENCE_FILES = (
    "Earth_Echo_Catalogo.json",
    "Earth_Echo_Especificacion.md",
    "Earth Echo Global Environmental Observatory.png",
)


def catalog_path() -> Path:
    configured = get_settings().catalog_path
    if configured is not None:
        return configured
    return repo_root() / "Earth_Echo_Catalogo.json"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_catalog() -> CatalogDocument:
    payload = json.loads(catalog_path().read_text(encoding="utf-8"))
    return CatalogDocument.model_validate(payload)


def load_integrity_pin() -> dict[str, str] | None:
    path = repo_root() / "data" / "operational" / "reference_integrity.json"
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    files = payload.get("files")
    if not isinstance(files, dict):
        raise ValueError("reference_integrity.json no tiene un objeto files.")
    return {str(key): str(value) for key, value in files.items()}
