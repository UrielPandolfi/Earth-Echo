"""Estado operativo de integración, separado del catálogo original."""

import json
from functools import lru_cache
from pathlib import Path

from pydantic import Field

from earth_echo.contracts.types import ApiModel, CatalogSourceId, IntegrationStatus
from earth_echo.paths import repo_root


class SourceIntegration(ApiModel):
    integration_status: IntegrationStatus
    sample_kind: str | None = None
    sample_path: str | None = None
    credential_variables: list[str] = Field(default_factory=list)
    detail: str = Field(min_length=1)


class IntegrationOverlay(ApiModel):
    sources: dict[CatalogSourceId, SourceIntegration]


@lru_cache(maxsize=2)
def _load_revision(path: Path, revision: tuple[int,int,int]) -> IntegrationOverlay:
    # The version key includes the atomic replacement's file identity as well as
    # mtime/size. Repeated per-source lookups share parsing, not stale status.
    payload = json.loads(path.read_text(encoding="utf-8"))
    return IntegrationOverlay.model_validate(payload)


def load_overlay() -> IntegrationOverlay:
    path = repo_root() / "data" / "operational" / "source_integration.json"
    info=path.stat()
    return _load_revision(path,(info.st_mtime_ns,info.st_size,info.st_ino))


def integration_status_for(source_id: str) -> IntegrationStatus:
    item = load_overlay().sources.get(source_id)  # type: ignore[arg-type]
    if item is None:
        return "documented"
    return item.integration_status
