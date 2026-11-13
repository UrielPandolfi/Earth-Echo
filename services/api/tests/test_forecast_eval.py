from earth_echo.science.forecast_eval import (
    ANALOG_NEIGHBORS,
    eligible_neighbors,
    evaluate,
    predict_case,
    replay,
)


def _series(start: int, end: int, value) -> dict[tuple[int, int], float | None]:
    rows = {}
    for year in range(start, end + 1):
        for month in range(1, 13):
            rows[(year, month)] = value(year, month)
    return rows


def test_neighbors_cannot_see_the_future_outcome() -> None:
    anomalies = _series(2010, 2024, lambda year, month: float(year) + month / 100)
    issue = (2024, 6)
    neighbors = eligible_neighbors(anomalies, issue)
    assert len(neighbors) == ANALOG_NEIGHBORS
    assert all(month == 7 and (year, month) < issue for (year, month), _outcome in neighbors)
    saved = replay(anomalies, issue)
    assert "outcome_c" not in saved
    assert saved["experiment_class"] == "retrospective_reconstructed"


def test_constant_series_does_not_claim_skill_over_persistence() -> None:
    anomalies = _series(2010, 2025, lambda _year, _month: 1.0)
    report = evaluate(anomalies)
    assert report["validated_for_use"] is False
    assert report["additional_skill"] is False
    assert report["cases_scored"] >= 24
    metrics = report["metrics"]
    assert metrics["persistence"]["mae_c"] == 0
    assert metrics["analog"]["mae_c"] == 0
    assert metrics["climatology"]["mae_c"] == 1
    assert "no queda validado" in str(report["reason"])


def test_a_case_without_analogs_is_excluded_not_scored_as_zero() -> None:
    anomalies = {(2024, 6): 0.2, (2024, 7): 9.0}
    prediction = predict_case(anomalies, (2024, 6))
    assert prediction.analog_c is None
    assert prediction.excluded_reason is not None
    report = evaluate(anomalies)
    assert report["cases_scored"] == 0
    assert report["cases_excluded"] == 2
    assert report["additional_skill"] is False
