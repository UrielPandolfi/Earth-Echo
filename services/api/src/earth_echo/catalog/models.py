"""Forma del archivo Earth_Echo_Catalogo.json. Los textos siguen siendo documentación."""

from pydantic import ConfigDict, Field

from earth_echo.contracts.types import ApiModel, CatalogSourceId


class CatalogSource(ApiModel):
    id: CatalogSourceId
    name: str = Field(min_length=1)
    url: str = Field(min_length=1)
    variables: str
    coverage: str
    cadence: str
    access: str
    limits: str
    verification: str


class CatalogVariable(ApiModel):
    id: str = Field(pattern=r"^V\d{2}$")
    name: str = Field(min_length=1)
    units: str
    source_ids: list[CatalogSourceId]
    source_notes: str
    processing_notes: str


class CatalogModule(ApiModel):
    id: str = Field(pattern=r"^F\d{2}$")
    name: str = Field(min_length=1)
    family: str
    global_scope: str
    output_type: str
    required_inputs: str
    proposed_method: str
    horizon: str
    missing_or_local_data: str
    validation: str
    source_ids: list[CatalogSourceId]
    implementation_priority: str
    implementation_status: str


class HttpSampleCheck(ApiModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    source: str
    url: str
    status: int
    byte_count: int = Field(validation_alias="bytes")
    json_keys: list[str]
    tested: str


class OutputContractExample(ApiModel):
    phenomenon_id: str
    output_type: str
    model_version: str | None
    run_id: str | None
    issued_at: str | None
    valid_from: str | None
    valid_to: str | None
    source_asset_ids: list[str]
    probability: float | None
    probability_definition: str | None
    uncertainty: str | None
    validation_reference: str | None
    operational_state: str


class CatalogDocument(ApiModel):
    project: str
    version: str
    reviewed_on: str
    language: str
    purpose: str
    all_modules_implemented: bool
    all_sources_ingestion_verified: bool
    evidence_levels: list[str]
    sources: list[CatalogSource]
    variables: list[CatalogVariable]
    modules: list[CatalogModule]
    http_sample_checks: list[HttpSampleCheck]
    output_contract_example: OutputContractExample
