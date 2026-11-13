"""Configuración por entorno. Los secretos se leen de variables, nunca del código."""

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field

from earth_echo.paths import repo_root


def load_dotenv_file(path: Path) -> None:
    """Carga KEY=VALUE sin pisar variables que ya existen en el entorno."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if key:
            os.environ.setdefault(key, value)


class Settings(BaseModel):
    host: str = "0.0.0.0"
    port: int = Field(ge=1, le=65535)
    env_name: str
    cors_origins: list[str]
    max_body_bytes: int = Field(ge=1)
    catalog_path: Path | None = None


def _split_origins(raw: str) -> list[str]:
    origins = [item.strip() for item in raw.split(",") if item.strip()]
    if not origins:
        raise ValueError("EARTH_ECHO_CORS_ORIGINS no puede quedar vacío.")
    return origins


@lru_cache
def get_settings() -> Settings:
    load_dotenv_file(repo_root() / ".env")
    catalog_raw = os.environ.get("EARTH_ECHO_CATALOG_PATH", "").strip()
    return Settings(
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8000")),
        env_name=os.environ.get("EARTH_ECHO_ENV", "development"),
        cors_origins=_split_origins(
            os.environ.get(
                "EARTH_ECHO_CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173",
            )
        ),
        max_body_bytes=int(os.environ.get("EARTH_ECHO_MAX_BODY_BYTES", "1048576")),
        catalog_path=Path(catalog_raw) if catalog_raw else None,
    )
