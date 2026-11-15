"""Rutas del repositorio, independientes del directorio de trabajo."""

import os
from pathlib import Path


def repo_root() -> Path:
    override = os.environ.get("EARTH_ECHO_ROOT", "").strip()
    if override:
        root = Path(override)
        if (root / "Earth_Echo_Catalogo.json").is_file():
            return root
        raise FileNotFoundError(f"EARTH_ECHO_ROOT no contiene el catálogo: {root}")
    here = Path(__file__).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "Earth_Echo_Catalogo.json").is_file():
            return candidate
    raise FileNotFoundError(
        "No se encontró Earth_Echo_Catalogo.json al subir desde el código de la API."
    )


def relative_to_repo(path: Path) -> str:
    return path.resolve().relative_to(repo_root()).as_posix()
