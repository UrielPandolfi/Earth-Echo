"""Typed summaries of calculated analyses, separate from event counts."""
from typing import Literal
from earth_echo.contracts.types import ApiModel,UtcDateTime
from earth_echo.contracts.products import ScientificProduct,CalculationInput
from pydantic import Field
from earth_echo.contracts.geometry import GeographicExtent


class SSTAnomalyView(ApiModel):
    data_mode: Literal['real']='real'
    status: Literal['evaluated','not_evaluable','unavailable']
    reason: str | None=None
    assessment_period: str='2022–2025 · histórico'
    assessed_months: int=0
    flagged_months: int=0
    warm_months: int=0
    cold_months: int=0
    missing_months: int=0
    stale_input: bool=False
    product: ScientificProduct | None=None


class AssociationPoint(ApiModel):
    year: int
    quarter: int=Field(ge=1,le=4)
    start: UtcDateTime
    end: UtcDateTime
    x: float | None
    y: float | None
    residual_x: float | None
    residual_y: float | None


class BlockInterval(ApiModel):
    block_quarters: int
    low: float | None
    high: float | None
    valid_draws: int
    draws: int


class AssociationPairView(ApiModel):
    id: str
    title: str
    status: Literal['evaluated','not_evaluable']
    reason: str | None
    x_name: str
    y_name: str
    x_unit: str
    y_unit: str
    x_scope: str
    y_scope: str
    n_pairs: int
    missing_pairs: int
    raw_r: float | None=Field(ge=-1,le=1,allow_inf_nan=False)
    residual_r: float | None=Field(ge=-1,le=1,allow_inf_nan=False)
    slope_x_per_year: float | None
    slope_y_per_year: float | None
    intervals: list[BlockInterval]
    points: list[AssociationPoint]
    inputs: list[CalculationInput]
    warnings: list[str]


class AssociationView(ApiModel):
    data_mode: Literal['real']='real'
    status: Literal['evaluated','not_evaluable','unavailable']
    reason: str | None=None
    method_version: str
    execution_id: str
    computed_at: UtcDateTime | None
    causal_attribution: Literal['not_identified']='not_identified'
    predictive_validation: Literal['not_a_forecast']='not_a_forecast'
    parameters: dict[str,float]
    references: list[str]
    stale_inputs: list[str]=Field(default_factory=list)
    verification: str
    pairs: list[AssociationPairView]


class SeriesPoint(ApiModel):
    year: int
    month: int
    sst_c: float | None
    anomaly_c: float | None
    present_days: int
    expected_days: int


class LinePoint(ApiModel):
    year: int
    month: int
    anomaly_c: float


class TrendView(ApiModel):
    schema_version: Literal['1.0']
    execution_id: str
    data_mode: Literal['real']
    status: Literal['evaluated','not_evaluable','unavailable']
    reason: str | None=None
    method_id: str
    method_version: str
    source_id: Literal['D15']
    variable_id: Literal['V15']
    region_id: str
    unit: Literal['°C']
    anomaly_kind: Literal['absolute_celsius']
    aggregation: str
    reference_start: str
    reference_end: str
    analysis_start: str
    analysis_end: str
    cutoff: str | None=None
    expected_months: int
    present_months: int
    missing_months: int
    coverage: float | None
    slope_c_per_year: float | None
    interval_low_c_per_year: float | None
    interval_high_c_per_year: float | None
    includes_zero: bool | None
    practical_threshold_c_per_year: float
    practical_threshold_exceeded: bool | None
    predictable: Literal['not_a_forecast']
    cause: Literal['not_identified']
    assumptions: list[str]
    warnings: list[str]
    asset_checksums: list[str]
    narrative: str
    series: list[SeriesPoint]
    trend_line: list[LinePoint]
    interval_low_line: list[LinePoint]
    interval_high_line: list[LinePoint]
    source_series_sha256: str | None=None
    region_extent: GeographicExtent | None=None
    bootstrap_block_months: int=12
    bootstrap_draws: int=1000
    bootstrap_valid_draws: int=0
    sensitivity_block_months: int=24
    sensitivity_low_c_per_year: float | None=None
    sensitivity_high_c_per_year: float | None=None
    sensitivity_valid_draws: int=0
    residual_lag1_r: float | None=None
    conditional_interval: Literal[True]=True
