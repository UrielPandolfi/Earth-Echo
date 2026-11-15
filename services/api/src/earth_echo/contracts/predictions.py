"""Read-only forecasts adapted from retained products, not scientific skill claims.

Legacy ForecastRecord requires issue/initialization dates. Providers may not supply
them; this contract keeps unknown times null without weakening legacy experiments.
"""
from typing import Literal
from pydantic import Field, model_validator
from earth_echo.contracts.types import ApiModel, CatalogSourceId, PhenomenonId, UtcDateTime, Sha256
from earth_echo.contracts.geometry import GeographicExtent, GeoMultiPolygon
from earth_echo.contracts.products import ScientificGrid, ScientificCalculation
from earth_echo.contracts.operations import RefreshJob

TemporalState = Literal['future', 'in_progress', 'expired', 'unknown']
ResultStatus = Literal['available', 'no_coverage', 'missing_input', 'expired', 'not_implemented']


class ForecastDescriptor(ApiModel):
    id: str
    product_id: str
    source_id: CatalogSourceId
    phenomenon_id: PhenomenonId | None = None
    title: str
    provider: str
    result_type: Literal['imported_probability', 'imported_value', 'derived_indicator', 'own_experiment']
    spatial_support: Literal['field', 'published_region', 'regional_series', 'planetary', 'table']
    queryable: bool
    availability: Literal['available', 'missing_input', 'not_implemented']
    temporal_state: TemporalState
    variable: str
    unit: str
    native_unit: str
    event_definition: str
    scientific_threshold: str | None = None
    reference_period: str | None = None
    trend_treatment: str | None = None
    method: str
    adapter_version: str
    provider_version: str
    identity_basis: str
    initialized_at: UtcDateTime | None = None
    issued_at: UtcDateTime | None = None
    retrieved_at: UtcDateTime
    processed_at: UtcDateTime
    first_seen_at: UtcDateTime
    first_seen_basis: str
    valid_from: UtcDateTime | None = None
    valid_to: UtcDateTime | None = None
    temporal_semantics: Literal['monthly_interval', 'instant', 'accumulation_interval', 'published_interval', 'three_hour_windows', 'unknown']
    coverage: str
    resolution: str | None = None
    quality_mask: str | None = None
    sampling: str | None = None
    calculation: ScientificCalculation | None = None
    original_url: str
    original_sha256: Sha256
    original_download: str
    metadata_download: str
    reference_url: str
    limitation: str
    experimental: bool
    validated_for_use: Literal[False] = False
    skill: None = None
    skill_note: str = 'Habilidad por región/plazo no evaluada en Earth Echo.'
    update: RefreshJob | None = None
    update_pending: bool


class ForecastCatalog(ApiModel):
    data_mode: Literal['real'] = 'real'
    as_of: UtcDateTime
    forecasts: list[ForecastDescriptor]
    default_d16_id: str | None
    future_fields: int
    current_fields: int
    archived_fields: int
    own_experiments: int
    note: str


class ForecastField(ApiModel):
    status: ResultStatus
    reason: str | None = None
    forecast: ForecastDescriptor | None = None
    grid: ScientificGrid | None = None


class ForecastCell(ApiModel):
    id: str
    row: int = Field(ge=0)
    column: int = Field(ge=0)
    longitude: float
    latitude: float
    extent: GeographicExtent
    geometry: GeoMultiPolygon
    support_note: str


class ForecastPoint(ApiModel):
    data_mode: Literal['real'] = 'real'
    status: ResultStatus
    reason: str | None = None
    forecast: ForecastDescriptor | None = None
    requested_longitude: float
    requested_latitude: float
    cell: ForecastCell | None = None
    value: float | None = Field(default=None, allow_inf_nan=False)
    probability: float | None = Field(default=None, ge=0, le=1)
    unit: str | None = None
    uncertainty: None = None
    selection_rule: str

    @model_validator(mode='after')
    def disjoint_values(self):
        if self.value is not None and self.probability is not None:
            raise ValueError('Use probability or deterministic value, not both')
        if self.status in {'no_coverage', 'missing_input', 'not_implemented'} and (self.value is not None or self.probability is not None):
            raise ValueError('An unavailable result cannot contain a value')
        return self


class ForecastHighlight(ApiModel):
    id: str
    cell_count: int = Field(gt=0)
    probability_min: float = Field(ge=0, le=1)
    probability_max: float = Field(ge=0, le=1)
    representative: ForecastPoint


class ForecastHighlights(ApiModel):
    status: ResultStatus
    reason: str | None = None
    forecast_id: str
    probability_filter: float = Field(ge=0, le=1)
    rule: str
    matching_cells: int | None
    total_areas: int | None
    returned_areas: int | None
    limit: int
    areas: list[ForecastHighlight]


class PlanetaryWindow(ApiModel):
    valid_from: UtcDateTime
    valid_to: UtcDateTime
    value: float = Field(ge=0, le=9)
    provider_type: Literal['predicted'] = 'predicted'
    temporal_state: TemporalState


class PlanetaryForecast(ApiModel):
    data_mode: Literal['real'] = 'real'
    status: ResultStatus
    reason: str | None = None
    forecast: ForecastDescriptor | None = None
    windows: list[PlanetaryWindow]
    probability: None = None
    note: str
