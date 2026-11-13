"""Respuestas de salud y de proveedores. La salud del proceso no afirma fuentes."""

from typing import Literal

from earth_echo.contracts.types import (
    ApiModel,
    CatalogSourceId,
    IntegrationStatus,
    UtcDateTime,
)


class HealthResponse(ApiModel):
    schema_version: Literal["1.0"]
    status: Literal["ok"]
    service: Literal["earth-echo-api"]
    time: UtcDateTime
    checks: list[Literal["process"]]


class StoreCheck(ApiModel):
    name: str
    path: str
    present: bool


class ReadyResponse(ApiModel):
    schema_version: Literal["1.0"]
    process: Literal["ok"]
    query_stores: Literal["ready", "incomplete"]
    providers_updated: Literal["not_checked"]
    assistant: Literal["unavailable", "configured"]
    stores: list[StoreCheck]
    note: str


class ProviderStatus(ApiModel):
    source_id: CatalogSourceId
    name: str
    integration_status: IntegrationStatus
    sample_kind: str | None
    live_status: Literal["not_probed", "reachable", "unreachable"]
    detail: str


class ProviderReport(ApiModel):
    schema_version: Literal["1.0"]
    checked_at: UtcDateTime
    live_probe: Literal["not_performed", "performed"]
    note: str
    providers: list[ProviderStatus]
