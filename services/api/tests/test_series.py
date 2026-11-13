import pytest

from earth_echo.science.series import (
    MIN_MONTHS,
    MonthValue,
    anomalies,
    area_weight,
    estimate_trend,
    month_mean,
    monthly_climatology,
    weighted_mean,
)


def _linear_months(years: int, slope: float, gap_months: set[tuple[int, int]] | None = None) -> tuple[list[MonthValue], list[float | None]]:
    gaps = gap_months or set()
    months: list[MonthValue] = []
    anomaly_values: list[float | None] = []
    for index in range(years * 12):
        year = 2000 + index // 12
        month = index % 12 + 1
        fraction = year + (month - 0.5) / 12
        anomaly = None if (year, month) in gaps else slope * (fraction - 2000)
        months.append(MonthValue(year, month, 20 + (anomaly or 0), 28 if anomaly is not None else 0, 30))
        anomaly_values.append(anomaly)
    return months, anomaly_values


def test_area_weight_changes_the_mean() -> None:
    values = [10.0, None, 20.0]
    mean, present = weighted_mean(values, [0.0, 60.0, 60.0], 1)
    expected = (10 * area_weight(0) + 20 * area_weight(60)) / (area_weight(0) + area_weight(60))
    assert present == 2
    assert mean == expected
    assert mean != 15
    assert mean is not None and mean < 15


def test_sparse_month_stays_missing_instead_of_zero() -> None:
    assert month_mean([1.0, None, 3.0], expected_days=30) is None
    assert month_mean([1.0, None, 3.0] + [2.0] * 24, expected_days=30) == (1 + 3 + 48) / 26


def test_climatology_ignores_the_future_and_refuses_a_short_reference() -> None:
    months = [
        MonthValue(year, month, 10.0, 30, 30)
        for year in range(2000, 2008)
        for month in range(1, 13)
    ]
    assert monthly_climatology(months, (2000, 1), (2006, 12)) is None
    months.append(MonthValue(2010, 1, 99.0, 30, 30))
    ready = monthly_climatology(months, (2000, 1), (2007, 12))
    assert ready is not None
    assert ready[1] == 10
    assert anomalies([MonthValue(2010, 1, 12.0, 30, 30)], ready) == [2.0]


def test_known_slope_survives_a_gap_and_a_short_series_does_not_become_zero() -> None:
    months, anomaly_values = _linear_months(8, 0.04)
    estimate = estimate_trend(months, anomaly_values)
    assert estimate.status == "evaluated"
    assert estimate.slope_per_year == pytest.approx(0.04)
    assert estimate.interval_low == pytest.approx(0.04)
    assert estimate.interval_high == pytest.approx(0.04)
    gapped_months, gapped_values = _linear_months(9, 0.04, {(2003, 6), (2003, 7), (2003, 8)})
    gapped = estimate_trend(gapped_months, gapped_values)
    assert gapped.slope_per_year is not None
    assert gapped.slope_per_year == pytest.approx(0.04)
    assert gapped.missing_months == 3
    short_months, short_values = _linear_months(3, 0.2)
    short = estimate_trend(short_months, short_values)
    assert short.status == "not_evaluable"
    assert short.slope_per_year is None
    assert MIN_MONTHS > len(short_months)


def test_constant_series_includes_zero_without_claiming_no_change() -> None:
    months, anomaly_values = _linear_months(8, 0)
    estimate = estimate_trend(months, anomaly_values)
    assert estimate.includes_zero is True
    assert estimate.slope_per_year == 0
    text = __import__("earth_echo.science.series", fromlist=["explain"]).explain(estimate)
    assert "no demuestra" in text
    assert "pronóstico" in text
