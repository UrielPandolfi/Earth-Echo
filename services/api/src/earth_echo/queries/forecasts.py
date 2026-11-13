"""Pronóstico importado y experimento retrospectivo. El corte se aplica acá."""

import json
from datetime import datetime, timezone
from pathlib import Path

from earth_echo.ingest.d15_history import series_path
from earth_echo.paths import repo_root
from earth_echo.science.forecast_eval import evaluate, replay
from earth_echo.science.series import MonthValue, anomalies, monthly_climatology
from earth_echo.science.forecast_eval import REFERENCE_END, REFERENCE_START


def forecast_dir() -> Path:
    path = repo_root() / "data" / "real" / "forecasts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def anomaly_table() -> dict[tuple[int, int], float | None]:
    payload = json.loads(series_path().read_text(encoding="utf-8"))
    months = [
        MonthValue(
            year=int(item["year"]),
            month=int(item["month"]),
            value=None if item["value"] is None else float(item["value"]),
            present_days=int(item["present_days"]),
            expected_days=int(item["expected_days"]),
        )
        for item in payload["months"]
        if isinstance(item, dict)
    ]
    climatology = monthly_climatology(months, REFERENCE_START, REFERENCE_END)
    values = anomalies(months, climatology)
    return {(item.year, item.month): value for item, value in zip(months, values, strict=True)}


def experiment_report() -> dict[str, object]:
    table = anomaly_table()
    report = evaluate(table)
    report["reference"] = {"start": list(REFERENCE_START), "end": list(REFERENCE_END)}
    return report


def _replay_path(issue: tuple[int, int]) -> Path:
    return forecast_dir() / "replay" / f"{issue[0]:04d}-{issue[1]:02d}.json"


def calculate_replay(issue: tuple[int, int]) -> dict[str, object]:
    path = _replay_path(issue)
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    saved = replay(anomaly_table(), issue)
    saved["saved_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    saved["outcome_c"] = None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(saved, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return saved


def reveal_replay(issue: tuple[int, int]) -> dict[str, object]:
    path = _replay_path(issue)
    if not path.is_file():
        return {
            "status": "prediction_not_saved",
            "reason": "Primero hay que guardar la predicción. El desenlace no se muestra antes.",
        }
    saved = json.loads(path.read_text(encoding="utf-8"))
    if saved.get("outcome_c") is None:
        outcome = anomaly_table().get(tuple(saved["outcome_month"]))
        saved["outcome_c"] = outcome
        if saved.get("analog_c") is not None and outcome is not None:
            saved["analog_error_c"] = saved["analog_c"] - outcome
        path.write_text(json.dumps(saved, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    saved["status"] = "revealed"
    return saved
