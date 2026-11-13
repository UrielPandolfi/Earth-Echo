import json

import pytest
from fastapi.testclient import TestClient

from earth_echo.api.app import create_app
from earth_echo.queries import trend
from earth_echo.settings import get_settings


def _months() -> list[dict[str, object]]:
    rows = []
    for year in range(2014, 2023):
        for month in range(1, 13):
            missing = year == 2022 and month == 6
            rows.append(
                {
                    "year": year,
                    "month": month,
                    "value": None if missing else 28.0,
                    "present_days": 0 if missing else 30,
                    "expected_days": 30,
                }
            )
    return rows


def test_constant_series_keeps_the_gap_and_does_not_forecast(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "monthly_series.json"
    path.write_text(
        json.dumps(
            {
                "reference": {"start": [2014, 1], "end": [2021, 12]},
                "analysis": {"start": [2014, 1], "end": [2022, 12]},
                "aggregation": "prueba",
                "region_id": "caribe-occidental",
                "assets": [{"sha256": "a" * 64}],
                "months": _months(),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(trend, "series_path", lambda: path)
    trend._CACHE.clear()
    view = trend.trend_view()
    assert view.status == "evaluated"
    assert view.slope_c_per_year == pytest.approx(0)
    assert view.includes_zero is True
    assert view.predictable == "not_a_forecast"
    june = next(item for item in view.series if item.year == 2022 and item.month == 6)
    assert june.sst_c is None
    assert june.anomaly_c is None
    assert "2022,6,,," in trend.trend_csv()


def test_another_region_is_not_replaced_by_demo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EARTH_ECHO_MAX_BODY_BYTES", raising=False)
    get_settings.cache_clear()
    client = TestClient(create_app())
    body = client.get("/v1/analyses/d15-sst", params={"region_id": "amazonia"}).json()
    assert body["status"] == "unavailable"
    assert body["slope_c_per_year"] is None
    assert "DEMO" in body["reason"]
    assert "-0.041" not in json.dumps(body)
