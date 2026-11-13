"""Tendencia del recorte ya agregado. No descarga ni rellena huecos."""

import csv
import hashlib
import io
import json
from typing import Literal

from earth_echo.ingest.d15_history import series_path
from earth_echo.science.series import (
    METHOD_ID,
    METHOD_VERSION,
    PRACTICAL_CHANGE_PER_YEAR,
    MonthValue,
    anomalies,
    estimate_trend,
    explain,
    monthly_climatology,
)
from earth_echo.contracts.types import ApiModel

AnalysisStatus = Literal["evaluated", "not_evaluable", "unavailable"]


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
    schema_version: Literal["1.0"]
    execution_id: str
    data_mode: Literal["real"]
    status: AnalysisStatus
    reason: str | None = None
    method_id: str
    method_version: str
    source_id: Literal["D15"]
    variable_id: Literal["V15"]
    region_id: str
    unit: Literal["°C"]
    anomaly_kind: Literal["absolute_celsius"]
    aggregation: str
    reference_start: str
    reference_end: str
    analysis_start: str
    analysis_end: str
    cutoff: str | None = None
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
    predictable: Literal["not_a_forecast"]
    cause: Literal["not_identified"]
    assumptions: list[str]
    warnings: list[str]
    asset_checksums: list[str]
    narrative: str
    series: list[SeriesPoint]
    trend_line: list[LinePoint]
    interval_low_line: list[LinePoint]
    interval_high_line: list[LinePoint]


_CACHE: dict[str, TrendView] = {}


def trend_view(cutoff: tuple[int, int] | None = None) -> TrendView:
    key = f"{METHOD_ID}:{cutoff}"
    path = series_path()
    if not path.is_file():
        return _missing("No está la serie mensual. Ejecutá la ingestión histórica de CoralTemp.")
    payload = json.loads(path.read_text(encoding="utf-8"))
    stamp = path.stat().st_mtime_ns
    cache_key = f"{key}:{stamp}"
    cached = _CACHE.get(cache_key)
    if cached is not None:
        return cached
    view = _build(payload, cutoff, cache_key)
    _CACHE[cache_key] = view
    return view


def trend_csv(cutoff: tuple[int, int] | None = None) -> str:
    view = trend_view(cutoff)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["year", "month", "sst_c", "anomaly_c", "present_days", "expected_days"])
    for point in view.series:
        writer.writerow(
            [
                point.year,
                point.month,
                "" if point.sst_c is None else point.sst_c,
                "" if point.anomaly_c is None else point.anomaly_c,
                point.present_days,
                point.expected_days,
            ]
        )
    return buffer.getvalue()


def _missing(reason: str) -> TrendView:
    return TrendView(
        schema_version="1.0",
        execution_id="missing",
        data_mode="real",
        status="unavailable",
        reason=reason,
        method_id=METHOD_ID,
        method_version=METHOD_VERSION,
        source_id="D15",
        variable_id="V15",
        region_id="caribe-occidental",
        unit="°C",
        anomaly_kind="absolute_celsius",
        aggregation="",
        reference_start="2014-01",
        reference_end="2021-12",
        analysis_start="2014-01",
        analysis_end="2025-12",
        expected_months=0,
        present_months=0,
        missing_months=0,
        coverage=None,
        slope_c_per_year=None,
        interval_low_c_per_year=None,
        interval_high_c_per_year=None,
        includes_zero=None,
        practical_threshold_c_per_year=PRACTICAL_CHANGE_PER_YEAR,
        practical_threshold_exceeded=None,
        predictable="not_a_forecast",
        cause="not_identified",
        assumptions=_assumptions(),
        warnings=["Este resultado no es un pronóstico ni una causa."],
        asset_checksums=[],
        narrative=reason,
        series=[],
        trend_line=[],
        interval_low_line=[],
        interval_high_line=[],
    )


def _build(payload: dict[str, object], cutoff: tuple[int, int] | None, cache_key: str) -> TrendView:
    reference = payload["reference"]
    analysis = payload["analysis"]
    if not isinstance(reference, dict) or not isinstance(analysis, dict):
        return _missing("La serie guardada no tiene los períodos.")
    reference_start = _pair(reference["start"])
    reference_end = _pair(reference["end"])
    analysis_start = _pair(analysis["start"])
    analysis_end = _pair(analysis["end"])
    if cutoff is not None and cutoff < reference_end:
        reference_end = cutoff
    months = [
        MonthValue(
            year=int(item["year"]),
            month=int(item["month"]),
            value=None if item["value"] is None else float(item["value"]),
            present_days=int(item["present_days"]),
            expected_days=int(item["expected_days"]),
        )
        for item in payload["months"]
        if isinstance(item, dict) and analysis_start <= (int(item["year"]), int(item["month"])) <= (cutoff or analysis_end)
    ]
    climatology = monthly_climatology(months, reference_start, reference_end)
    anomaly_values = anomalies(months, climatology)
    estimate = estimate_trend(months, anomaly_values)
    assets = payload["assets"] if isinstance(payload["assets"], list) else []
    checksums = [str(item["sha256"]) for item in assets if isinstance(item, dict)]
    execution_id = hashlib.sha256(f"{cache_key}:{checksums}".encode()).hexdigest()[:16]
    coverage = None if estimate.expected_months == 0 else estimate.present_months / estimate.expected_months
    warnings = [
        "La referencia tiene ocho años, no es una normal de treinta.",
        "El intervalo describe la pendiente, no un pronóstico ni la incertidumbre de cada mes.",
        "La climatología usa 2014–2021 y la recta incluye esos años: una tendencia lineal uniforme puede quedar atenuada.",
        "Una sola región: no hay corrección por comparaciones múltiples.",
        "Una tendencia no identifica la causa.",
    ]
    if estimate.status != "evaluated":
        warnings.append(estimate.reason or "No evaluable.")
    return TrendView(
        schema_version="1.0",
        execution_id=execution_id,
        data_mode="real",
        status="evaluated" if estimate.status == "evaluated" else "not_evaluable",
        reason=estimate.reason,
        method_id=METHOD_ID,
        method_version=METHOD_VERSION,
        source_id="D15",
        variable_id="V15",
        region_id=str(payload.get("region_id") or "caribe-occidental"),
        unit="°C",
        anomaly_kind="absolute_celsius",
        aggregation=str(payload.get("aggregation") or ""),
        reference_start=_label(reference_start),
        reference_end=_label(reference_end),
        analysis_start=_label(analysis_start),
        analysis_end=_label(cutoff or analysis_end),
        cutoff=None if cutoff is None else _label(cutoff),
        expected_months=estimate.expected_months,
        present_months=estimate.present_months,
        missing_months=estimate.missing_months,
        coverage=coverage,
        slope_c_per_year=estimate.slope_per_year,
        interval_low_c_per_year=estimate.interval_low,
        interval_high_c_per_year=estimate.interval_high,
        includes_zero=estimate.includes_zero,
        practical_threshold_c_per_year=PRACTICAL_CHANGE_PER_YEAR,
        practical_threshold_exceeded=estimate.practical_threshold_exceeded,
        predictable="not_a_forecast",
        cause="not_identified",
        assumptions=_assumptions(),
        warnings=warnings,
        asset_checksums=checksums,
        narrative=explain(estimate),
        series=[
            SeriesPoint(
                year=item.year,
                month=item.month,
                sst_c=item.value,
                anomaly_c=anomaly,
                present_days=item.present_days,
                expected_days=item.expected_days,
            )
            for item, anomaly in zip(months, anomaly_values, strict=True)
        ],
        trend_line=_lines(months, anomaly_values, estimate, "center"),
        interval_low_line=_lines(months, anomaly_values, estimate, "low"),
        interval_high_line=_lines(months, anomaly_values, estimate, "high"),
    )


def _lines(months: list[MonthValue], anomaly_values: list[float | None], estimate, which: str) -> list[LinePoint]:
    if estimate.status != "evaluated" or estimate.slope_per_year is None:
        return []
    present = [(item, value) for item, value in zip(months, anomaly_values, strict=True) if value is not None]
    if len(present) < 2:
        return []
    first, last = present[0][0], present[-1][0]
    times = [item.year + (item.month - 0.5) / 12 for item, _value in present]
    values = [value for _item, value in present]
    mean_time = sum(times) / len(times)
    mean_value = sum(values) / len(values)
    slope = estimate.interval_low if which == "low" else estimate.interval_high if which == "high" else estimate.slope_per_year
    if slope is None:
        return []

    def at(item: MonthValue) -> float:
        moment = item.year + (item.month - 0.5) / 12
        return mean_value + slope * (moment - mean_time)

    return [
        LinePoint(year=first.year, month=first.month, anomaly_c=at(first)),
        LinePoint(year=last.year, month=last.month, anomaly_c=at(last)),
    ]


def _assumptions() -> list[str]:
    return [
        "La pendiente es la recta de mínimos cuadrados de la anomalía mensual contra el tiempo, en °C por año.",
        "La anomalía es la diferencia en °C respecto de la media del mismo mes en la referencia. No es un porcentaje.",
        "El intervalo sale de remuestrear por bloques de 12 meses los residuos de esa recta, con semilla fija.",
        "Los residuos pueden seguir autocorrelacionados. El intervalo no demuestra causalidad.",
        f"El umbral práctico de este caso es {PRACTICAL_CHANGE_PER_YEAR} °C por año. No es un límite de daño.",
    ]


def _pair(value: object) -> tuple[int, int]:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError("El período tiene que ser año y mes.")
    return int(value[0]), int(value[1])


def _label(value: tuple[int, int]) -> str:
    return f"{value[0]:04d}-{value[1]:02d}"
