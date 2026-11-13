"""Rutas del repositorio, independientes del directorio de trabajo."""

from pathlib import Path


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "Earth_Echo_Catalogo.json").is_file():
            return candidate
    raise FileNotFoundError(
        "No se encontró Earth_Echo_Catalogo.json al subir desde el código de la API."
    )


def relative_to_repo(path: Path) -> str:
    return path.resolve().relative_to(repo_root()).as_posix()
