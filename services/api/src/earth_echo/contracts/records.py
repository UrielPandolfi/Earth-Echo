"""Registros operativos. El catálogo original no se guarda dentro de estos modelos."""

import math
from typing import Annotated, Literal

from pydantic import Field, model_validator

from earth_echo.contracts.geometry import SpatialSupport
from earth_echo.contracts.types import (
    ApiModel,
    CapabilityStatus,
    CatalogSourceId,
    DataMode,
    OutputClass,
    PhenomenonId,
    RecordId,
    RetrievalKind,
    Sha256,
    UnavailableReason,
    UtcDateTime,
    VariableId,
)


class MissingValue(ApiModel):
    status: Literal["missing"]
    value: None = None
    unit: None = None


class PresentValue(ApiModel):
    status: Literal["present"]
    value: float
    unit: str = Field(min_length=1)

    @model_validator(mode="after")
    def finite_value(self) -> "PresentValue":
        if not math.isfinite(self.value):
            raise ValueError("Un valor presente debe ser finito. Un faltante usa estado missing.")
        return self


MeasuredValue = Annotated[MissingValue | PresentValue, Field(discriminator="status")]


class ProbabilityAbsent(ApiModel):
    state: Literal["absent"]
    value: None = None
    definition: None = None


class ProbabilityDefined(ApiModel):
    state: Literal["defined"]
    value: float = Field(ge=0, le=1)
    definition: str = Field(min_length=1)

    @model_validator(mode="after")
    def finite_value(self) -> "ProbabilityDefined":
        if not math.isfinite(self.value):
            raise ValueError("La probabilidad debe ser finita.")
        return self


ProbabilityStatement = Annotated[
    ProbabilityAbsent | ProbabilityDefined,
    Field(discriminator="state"),
]


class InstantSpan(ApiModel):
    kind: Literal["instant"]
    start: UtcDateTime


class IntervalSpan(ApiModel):
    kind: Literal["interval"]
    start: UtcDateTime
    end: UtcDateTime
    bounds: Literal["start_inclusive_end_exclusive"]

    @model_validator(mode="after")
    def ordered(self) -> "IntervalSpan":
        if self.end <= self.start:
            raise ValueError("El fin del intervalo debe ser posterior al inicio.")
        return self


TimeSpan = Annotated[InstantSpan | IntervalSpan, Field(discriminator="kind")]


class AvailabilityKnown(ApiModel):
    status: Literal["known"]
    at: UtcDateTime


class AvailabilityUnknown(ApiModel):
    status: Literal["unknown"]


Availability = Annotated[
    AvailabilityKnown | AvailabilityUnknown,
    Field(discriminator="status"),
]


class Quality(ApiModel):
    flags: list[str] = Field(default_factory=list)
    summary: str | None = None


class Provenance(ApiModel):
    source_ids: list[CatalogSourceId]
    asset_ids: list[RecordId] = Field(default_factory=list)
    collection_id: str | None = None
    product_version: str | None = None
    license_url: str | None = None
    native_unit: str | None = None
    retrieval: RetrievalKind | None = None
    note: str | None = None


class Uncertainty(ApiModel):
    description: str = Field(min_length=1)
    low: float | None = None
    high: float | None = None
    unit: str | None = None

    @model_validator(mode="after")
    def check_interval(self) -> "Uncertainty":
        if (self.low is None) != (self.high is None):
            raise ValueError("El intervalo de incertidumbre necesita ambos extremos o ninguno.")
        if self.low is not None and self.high is not None:
            if not math.isfinite(self.low) or not math.isfinite(self.high):
                raise ValueError("Los extremos de incertidumbre deben ser finitos.")
            if self.low > self.high:
                raise ValueError("El extremo inferior de la incertidumbre supera al superior.")
            if not self.unit:
                raise ValueError("Un intervalo numérico de incertidumbre necesita unidad.")
        return self


class AssetRecord(ApiModel):
    schema_version: Literal["1.0"]
    id: RecordId
    data_mode: DataMode
    source_id: CatalogSourceId
    collection_id: str = Field(min_length=1)
    product_version: str | None
    variable_id: VariableId
    native_unit: str | None
    spatial: SpatialSupport
    observed: TimeSpan
    issued_at: UtcDateTime | None
    availability: Availability
    ingested_at: UtcDateTime
    quality: Quality
    checksum_sha256: Sha256 | None
    byte_size: int | None = Field(default=None, ge=0)
    original_locator: str = Field(min_length=1)
    science_file_retrieved: bool
    provenance: Provenance


class ObservationRecord(ApiModel):
    schema_version: Literal["1.0"]
    id: RecordId
    data_mode: DataMode
    asset_id: RecordId
    variable_id: VariableId
    phenomenon_id: PhenomenonId | None
    measurement: MeasuredValue
    spatial: SpatialSupport
    observed: TimeSpan
    issued_at: UtcDateTime | None
    availability: Availability
    ingested_at: UtcDateTime
    quality: Quality
    product_version: str | None
    provenance: Provenance


class SignalRecord(ApiModel):
    schema_version: Literal["1.0"]
    id: RecordId
    data_mode: DataMode
    phenomenon_id: PhenomenonId
    output_class: OutputClass
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    variable_id: VariableId | None
    measurement: MeasuredValue
    spatial: SpatialSupport
    observed: TimeSpan | None
    valid: TimeSpan | None
    issued_at: UtcDateTime | None
    availability: Availability
    ingested_at: UtcDateTime
    quality: Quality
    provenance: Provenance
    capability_status: CapabilityStatus
    probability: ProbabilityStatement


class ForecastRecord(ApiModel):
    schema_version: Literal["1.0"]
    id: RecordId
    data_mode: DataMode
    phenomenon_id: PhenomenonId
    model_id: str = Field(min_length=1)
    model_version: str | None
    run_id: str | None
    initialization_time: UtcDateTime
    issued_at: UtcDateTime
    valid: IntervalSpan
    lead_time_hours: float | None = None
    variable_id: VariableId | None
    measurement: MeasuredValue
    probability: ProbabilityStatement
    uncertainty: Uncertainty | None = None
    spatial: SpatialSupport
    availability: Availability
    ingested_at: UtcDateTime
    quality: Quality
    provenance: Provenance
    validation_reference: str | None
    capability_status: CapabilityStatus

    @model_validator(mode="after")
    def check_forecast(self) -> "ForecastRecord":
        if self.issued_at < self.initialization_time:
            raise ValueError("La emisión no puede ser anterior a la inicialización.")
        if self.valid.start < self.initialization_time:
            raise ValueError("La validez no puede empezar antes de la inicialización.")
        if self.lead_time_hours is not None:
            if not math.isfinite(self.lead_time_hours) or self.lead_time_hours < 0:
                raise ValueError("El plazo del pronóstico debe ser un número de horas no negativo.")
            expected = (self.valid.start - self.initialization_time).total_seconds() / 3600
            if abs(expected - self.lead_time_hours) > (1 / 3600):
                raise ValueError("El plazo no coincide con el inicio de la ventana de validez.")
        if self.measurement.status == "missing" and self.probability.state == "absent":
            raise ValueError(
                "Un pronóstico sin valor y sin probabilidad definida no es un resultado. "
                "Usá un resultado no disponible."
            )
        return self


class UnavailableResult(ApiModel):
    schema_version: Literal["1.0"]
    status: Literal["unavailable"]
    requested_data_mode: DataMode
    reason_code: UnavailableReason
    reason: str = Field(min_length=1)
    phenomenon_id: PhenomenonId | None
    variable_id: VariableId | None
    source_ids: list[CatalogSourceId]
    as_of: UtcDateTime


class SignalQueryResult(ApiModel):
    schema_version: Literal["1.0"]
    requested_data_mode: DataMode
    phenomenon_id: PhenomenonId
    status: Literal["available", "unavailable"]
    signals: list[SignalRecord]
    forecasts: list[ForecastRecord]
    unavailable: UnavailableResult | None

    @model_validator(mode="after")
    def check_status(self) -> "SignalQueryResult":
        if self.status == "unavailable":
            if self.unavailable is None or self.signals or self.forecasts:
                raise ValueError("Un resultado no disponible no puede traer señales ni pronósticos.")
            if self.unavailable.requested_data_mode != self.requested_data_mode:
                raise ValueError("El modo del resultado no disponible no coincide con la consulta.")
            if self.unavailable.phenomenon_id not in {None, self.phenomenon_id}:
                raise ValueError("El fenómeno no disponible no coincide con la consulta.")
        elif self.unavailable is not None:
            raise ValueError("Un resultado disponible no lleva bloque de no disponibilidad.")
        for signal in self.signals:
            if signal.data_mode != self.requested_data_mode or signal.phenomenon_id != self.phenomenon_id:
                raise ValueError("La señal no corresponde al modo y fenómeno consultados.")
        for forecast in self.forecasts:
            if forecast.data_mode != self.requested_data_mode or forecast.phenomenon_id != self.phenomenon_id:
                raise ValueError("El pronóstico no corresponde al modo y fenómeno consultados.")
        return self
