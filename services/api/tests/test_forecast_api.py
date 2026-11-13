import json
from datetime import datetime, timezone

import pytest

from earth_echo.connectors.swpc_forecast import parse_predicted_kp
from earth_echo.paths import repo_root
from earth_echo.queries import forecasts


def test_imported_kp_keeps_only_future_predicted_steps() -> None:
    payload = json.loads(
        (repo_root() / "data/samples/d28-swpc/planetary-k-index-forecast.json").read_text(encoding="utf-8")
    )
    issued = datetime(2026, 11, 13, 8, tzinfo=timezone.utc)
    steps = parse_predicted_kp(payload, issued)
    assert steps
    assert all(step["valid_start"] >= "2026-11-14" for step in steps)
    assert all(step["lead_time_hours"] > 0 for step in steps)
    assert "probability" not in steps[0]


def test_replay_saves_the_prediction_before_the_outcome(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(forecasts, "forecast_dir", lambda: tmp_path)
    blocked = forecasts.reveal_replay((2024, 6))
    assert blocked["status"] == "prediction_not_saved"
    saved = forecasts.calculate_replay((2024, 6))
    assert saved["outcome_c"] is None
    assert "analog_error_c" not in saved
    assert all(tuple(item) < (2024, 6) for item in saved["neighbors"])
    revealed = forecasts.reveal_replay((2024, 6))
    assert revealed["status"] == "revealed"
    assert revealed["outcome_c"] is not None
    assert revealed["analog_error_c"] == pytest.approx(revealed["analog_c"] - revealed["outcome_c"])
