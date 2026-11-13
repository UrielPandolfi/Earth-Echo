"""Agregación y tendencia. La configuración queda fija antes de mirar el caso real."""

import math
import random
from dataclasses import dataclass

METHOD_ID = "ols-monthly-anomaly-block-bootstrap-v1"
METHOD_VERSION = "1"
MIN_MONTHS = 96
MIN_DAY_COVERAGE = 0.8
MIN_REFERENCE_YEARS = 8
BLOCK_MONTHS = 12
BOOTSTRAP_DRAWS = 1000
BOOTSTRAP_SEED = 20261113
PRACTICAL_CHANGE_PER_YEAR = 0.02


@dataclass(frozen=True)
class MonthValue:
    year: int
    month: int
    value: float | None
    present_days: int
    expected_days: int


@dataclass(frozen=True)
class TrendEstimate:
    status: str
    reason: str | None
    slope_per_year: float | None
    interval_low: float | None
    interval_high: float | None
    present_months: int
    missing_months: int
    expected_months: int
    includes_zero: bool | None
    practical_threshold_exceeded: bool | None


def area_weight(latitude: float) -> float:
    return math.cos(math.radians(latitude))


def weighted_mean(values: list[float | None], latitudes: list[float], width: int) -> tuple[float | None, int]:
    """Promedio ponderado por el coseno de la latitud. Un hueco no entra como cero."""
    if width <= 0 or len(values) % width != 0:
        raise ValueError("La malla no coincide con el ancho.")
    height = len(values) // width
    if len(latitudes) != height:
        raise ValueError("Cada fila necesita su latitud.")
    weighted = 0.0
    weight_sum = 0.0
    present = 0
    for row, latitude in enumerate(latitudes):
        weight = area_weight(latitude)
        if weight <= 0:
            continue
        for column in range(width):
            value = values[row * width + column]
            if value is None:
                continue
            weighted += value * weight
            weight_sum += weight
            present += 1
    if weight_sum == 0:
        return None, 0
    return weighted / weight_sum, present


def month_mean(days: list[float | None], expected_days: int, minimum_coverage: float = MIN_DAY_COVERAGE) -> float | None:
    if expected_days <= 0:
        return None
    present = [item for item in days if item is not None]
    if len(present) / expected_days < minimum_coverage:
        return None
    return sum(present) / len(present)


def monthly_climatology(
    months: list[MonthValue],
    reference_start: tuple[int, int],
    reference_end: tuple[int, int],
    minimum_years: int = MIN_REFERENCE_YEARS,
) -> dict[int, float] | None:
    """Media del mismo mes calendario dentro de la referencia. No usa fechas posteriores al fin."""
    grouped: dict[int, list[float]] = {month: [] for month in range(1, 13)}
    for item in months:
        if item.value is None:
            continue
        key = (item.year, item.month)
        if key < reference_start or key > reference_end:
            continue
        grouped[item.month].append(item.value)
    if any(len(values) < minimum_years for values in grouped.values()):
        return None
    return {month: sum(values) / len(values) for month, values in grouped.items()}


def anomalies(months: list[MonthValue], climatology: dict[int, float] | None) -> list[float | None]:
    if climatology is None:
        return [None for _ in months]
    return [
        None if item.value is None else item.value - climatology[item.month]
        for item in months
    ]


def ols_slope(times_years: list[float], values: list[float]) -> float | None:
    count = len(values)
    if count < 2 or len(times_years) != count:
        return None
    mean_time = sum(times_years) / count
    mean_value = sum(values) / count
    variance = sum((item - mean_time) ** 2 for item in times_years)
    if variance == 0:
        return None
    covariance = sum((time - mean_time) * (value - mean_value) for time, value in zip(times_years, values, strict=True))
    return covariance / variance


def _year_fraction(year: int, month: int) -> float:
    return year + (month - 0.5) / 12


def estimate_trend(months: list[MonthValue], anomaly_values: list[float | None]) -> TrendEstimate:
    expected = len(months)
    present_pairs = [
        (_year_fraction(item.year, item.month), anomaly)
        for item, anomaly in zip(months, anomaly_values, strict=True)
        if anomaly is not None
    ]
    present = len(present_pairs)
    missing = expected - present
    if anomaly_values and all(item is None for item in anomaly_values):
        return _unavailable(
            "La referencia estacional no tiene años suficientes. No se inventó una línea de base.",
            present,
            missing,
            expected,
        )
    if present < MIN_MONTHS:
        return _unavailable(
            f"Hay {present} meses con anomalía y el método pide al menos {MIN_MONTHS}. La pendiente no se reemplaza por cero.",
            present,
            missing,
            expected,
        )
    times = [item[0] for item in present_pairs]
    values = [item[1] for item in present_pairs]
    slope = ols_slope(times, values)
    if slope is None:
        return _unavailable("El tiempo no varía y la pendiente no está definida.", present, missing, expected)
    low, high = _residual_block_interval(times, values, slope)
    includes_zero = low <= 0 <= high
    return TrendEstimate(
        status="evaluated",
        reason=None,
        slope_per_year=slope,
        interval_low=low,
        interval_high=high,
        present_months=present,
        missing_months=missing,
        expected_months=expected,
        includes_zero=includes_zero,
        practical_threshold_exceeded=abs(slope) >= PRACTICAL_CHANGE_PER_YEAR,
    )


def _unavailable(reason: str, present: int, missing: int, expected: int) -> TrendEstimate:
    return TrendEstimate(
        status="not_evaluable",
        reason=reason,
        slope_per_year=None,
        interval_low=None,
        interval_high=None,
        present_months=present,
        missing_months=missing,
        expected_months=expected,
        includes_zero=None,
        practical_threshold_exceeded=None,
    )


def _residual_block_interval(times: list[float], values: list[float], slope: float) -> tuple[float, float]:
    """Intervalo por bloques de residuos. No supone errores independientes."""
    count = len(values)
    mean_time = sum(times) / count
    mean_value = sum(values) / count
    intercept = mean_value - slope * mean_time
    residuals = [value - (intercept + slope * time) for time, value in zip(times, values, strict=True)]
    generator = random.Random(BOOTSTRAP_SEED)
    slopes: list[float] = []
    for _ in range(BOOTSTRAP_DRAWS):
        drawn: list[float] = []
        while len(drawn) < count:
            start = generator.randrange(count)
            for offset in range(BLOCK_MONTHS):
                drawn.append(residuals[(start + offset) % count])
                if len(drawn) == count:
                    break
        synthetic = [intercept + slope * time + residual for time, residual in zip(times, drawn, strict=True)]
        resampled = ols_slope(times, synthetic)
        if resampled is not None:
            slopes.append(resampled)
    slopes.sort()
    return slopes[int(0.025 * (len(slopes) - 1))], slopes[int(0.975 * (len(slopes) - 1))]


def explain(estimate: TrendEstimate) -> str:
    if estimate.status != "evaluated" or estimate.slope_per_year is None or estimate.interval_low is None or estimate.interval_high is None:
        return estimate.reason or "La tendencia no se evaluó."
    direction = "sube" if estimate.slope_per_year > 0 else "baja" if estimate.slope_per_year < 0 else "no cambia en la recta"
    zero = (
        "El intervalo incluye cero: eso no demuestra que no haya habido cambio."
        if estimate.includes_zero
        else "El intervalo no incluye cero bajo este remuestreo. Eso no identifica la causa ni permite proyectar el futuro."
    )
    practical = (
        "La magnitud supera el umbral práctico fijado para este caso."
        if estimate.practical_threshold_exceeded
        else "La magnitud queda por debajo del umbral práctico fijado para este caso."
    )
    return (
        f"La anomalía mensual {direction} unos {abs(estimate.slope_per_year):.3f} °C por año. "
        f"El intervalo del 95 % va de {estimate.interval_low:.3f} a {estimate.interval_high:.3f} °C por año. "
        f"{zero} {practical} No es un pronóstico."
    )
