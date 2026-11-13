import math
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from earth_echo.contracts.geometry import (
    GeographicExtent,
    GeoLineString,
    GeoPoint,
    SpatialSupport,
)
from earth_echo.contracts.records import (
    AvailabilityUnknown,
    ForecastRecord,
    InstantSpan,
    IntervalSpan,
    MissingValue,
    PresentValue,
    ProbabilityAbsent,
    ProbabilityDefined,
    Provenance,
    Quality,
)


NOW = datetime(2026, 11, 13, tzinfo=timezone.utc)
POINT = SpatialSupport(
    role="observation_location",
    geometry=GeoPoint(type="Point", coordinates=[10.0, 20.0]),
)


def test_missing_measurement_rejects_zero() -> None:
    with pytest.raises(ValidationError):
        MissingValue.model_validate({"status": "missing", "value": 0, "unit": "m"})


def test_present_zero_is_a_real_value() -> None:
    value = PresentValue(status="present", value=0, unit="m")
    assert value.value == 0


def test_present_value_rejects_nan() -> None:
    with pytest.raises(ValidationError):
        PresentValue(status="present", value=math.nan, unit="m")


def test_probability_requires_definition_and_bounds() -> None:
    with pytest.raises(ValidationError):
        ProbabilityDefined(state="defined", value=0.2, definition="")
    with pytest.raises(ValidationError):
        ProbabilityDefined(state="defined", value=1.2, definition="fuera de rango")
    absent = ProbabilityAbsent(state="absent")
    assert absent.value is None


def test_instant_does_not_invent_an_end() -> None:
    instant = InstantSpan(kind="instant", start=NOW)
    assert instant.start == NOW
    with pytest.raises(ValidationError):
        InstantSpan.model_validate(
            {"kind": "instant", "start": "2026-11-13T00:00:00Z", "end": "2026-11-13T01:00:00Z"}
        )


def test_interval_is_half_open_and_ordered() -> None:
    with pytest.raises(ValidationError):
        IntervalSpan(
            kind="interval",
            start=NOW,
            end=NOW,
            bounds="start_inclusive_end_exclusive",
        )
    span = IntervalSpan(
        kind="interval",
        start=NOW,
        end=NOW + timedelta(days=1),
        bounds="start_inclusive_end_exclusive",
    )
    assert span.end - span.start == timedelta(days=1)


def test_naive_datetime_is_rejected() -> None:
    with pytest.raises(ValidationError):
        InstantSpan.model_validate({"kind": "instant", "start": "2026-11-13T00:00:00"})


def test_antimeridian_extent_and_line() -> None:
    GeographicExtent(west=175, south=-10, east=-175, north=10, crosses_antimeridian=True)
    with pytest.raises(ValidationError):
        GeographicExtent(west=175, south=-10, east=-175, north=10, crosses_antimeridian=False)
    with pytest.raises(ValidationError):
        GeoLineString(type="LineString", coordinates=[[170.0, 0.0], [-170.0, 0.0]])


def test_region_anchor_requires_region_id() -> None:
    with pytest.raises(ValidationError):
        SpatialSupport(role="region_anchor", geometry=GeoPoint(type="Point", coordinates=[0, 0]))
    with pytest.raises(ValidationError):
        SpatialSupport(
            role="observation_location",
            region_id="demo-region",
            geometry=GeoPoint(type="Point", coordinates=[0, 0]),
        )


def _forecast(**overrides) -> ForecastRecord:
    payload = dict(
        schema_version="1.0",
        id="forecast-example",
        data_mode="demo",
        phenomenon_id="F01",
        model_id="ejemplo",
        model_version=None,
        run_id=None,
        initialization_time=NOW,
        issued_at=NOW,
        valid=IntervalSpan(
            kind="interval",
            start=NOW + timedelta(hours=24),
            end=NOW + timedelta(hours=48),
            bounds="start_inclusive_end_exclusive",
        ),
        lead_time_hours=24,
        variable_id="V01",
        measurement=PresentValue(status="present", value=12, unit="mm"),
        probability=ProbabilityAbsent(state="absent"),
        uncertainty=None,
        spatial=POINT,
        availability=AvailabilityUnknown(status="unknown"),
        ingested_at=NOW,
        quality=Quality(flags=[], summary=None),
        provenance=Provenance(source_ids=[], retrieval="demo_fixture", note="ejemplo de contrato"),
        validation_reference=None,
        capability_status="specified",
    )
    payload.update(overrides)
    return ForecastRecord(**payload)


def test_forecast_requires_initialization_validity_and_a_result() -> None:
    forecast = _forecast()
    assert forecast.lead_time_hours == 24
    with pytest.raises(ValidationError):
        _forecast(lead_time_hours=3)
    with pytest.raises(ValidationError):
        _forecast(
            measurement=MissingValue(status="missing"),
            probability=ProbabilityAbsent(state="absent"),
        )
    with pytest.raises(ValidationError):
        _forecast(issued_at=NOW - timedelta(hours=1))
