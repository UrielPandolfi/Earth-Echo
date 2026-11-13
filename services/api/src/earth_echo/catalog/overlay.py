"""Estado operativo de integración, separado del catálogo original."""

import json
from functools import lru_cache

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


@lru_cache
def load_overlay() -> IntegrationOverlay:
    path = repo_root() / "data" / "operational" / "source_integration.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return IntegrationOverlay.model_validate(payload)


def integration_status_for(source_id: str) -> IntegrationStatus:
    item = load_overlay().sources.get(source_id)  # type: ignore[arg-type]
    if item is None:
        return "documented"
    return item.integration_status
