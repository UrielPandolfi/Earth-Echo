"""Vistas de catálogo y reporte de validación que salen por la API."""

from typing import Literal

from pydantic import Field, model_validator

from earth_echo.catalog.models import CatalogModule, CatalogSource, CatalogVariable
from earth_echo.contracts.types import ApiModel, CapabilityStatus, IntegrationStatus


class CatalogSourceView(CatalogSource):
    integration_status: IntegrationStatus


class PhenomenonView(CatalogModule):
    capability_status: CapabilityStatus


class SourceList(ApiModel):
    schema_version: Literal["1.0"]
    total: int = Field(ge=0)
    returned: int = Field(ge=0)
    sources: list[CatalogSourceView]

    @model_validator(mode="after")
    def check_counts(self) -> "SourceList":
        if self.returned != len(self.sources) or self.returned > self.total:
            raise ValueError("El total y la cantidad devuelta no coinciden con la lista.")
        return self


class PhenomenonList(ApiModel):
    schema_version: Literal["1.0"]
    total: int = Field(ge=0)
    returned: int = Field(ge=0)
    phenomena: list[PhenomenonView]

    @model_validator(mode="after")
    def check_counts(self) -> "PhenomenonList":
        if self.returned != len(self.phenomena) or self.returned > self.total:
            raise ValueError("El total y la cantidad devuelta no coinciden con la lista.")
        return self


class VariableList(ApiModel):
    schema_version: Literal["1.0"]
    total: int = Field(ge=0)
    returned: int = Field(ge=0)
    variables: list[CatalogVariable]

    @model_validator(mode="after")
    def check_counts(self) -> "VariableList":
        if self.returned != len(self.variables) or self.returned > self.total:
            raise ValueError("El total y la cantidad devuelta no coinciden con la lista.")
        return self


class ReferenceMention(ApiModel):
    owner_type: Literal["variable", "module"]
    owner_id: str
    source_id: str


class DescriptiveNote(ApiModel):
    variable_id: str
    remainder: str


class StatusCount(ApiModel):
    status: str
    count: int = Field(ge=0)


class RecordedHttpCheck(ApiModel):
    source: str
    url: str
    status: int
    byte_count: int
    json_keys: list[str]
    tested: str
    reexecuted: Literal[False]


class CatalogValidationReport(ApiModel):
    schema_version: Literal["1.0"]
    reference_path: str
    reference_sha256: str
    pinned_sha256: str | None
    reference_integrity: Literal["match", "mismatch", "pin_missing"]
    specification_integrity: Literal["match", "mismatch", "pin_missing"]
    image_integrity: Literal["match", "mismatch", "pin_missing"]
    source_count: int
    variable_count: int
    phenomenon_count: int
    duplicate_ids: list[str]
    dangling_references: list[ReferenceMention]
    unreferenced_source_ids: list[str]
    descriptive_source_notes: list[DescriptiveNote]
    capability_counts: list[StatusCount]
    recorded_http_checks: list[RecordedHttpCheck]
    recorded_http_checks_note: str
