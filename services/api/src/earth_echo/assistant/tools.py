"""Consultas compactas. No copian la ciencia ni escriben pronósticos."""

import json
from typing import Any

from earth_echo.catalog.capabilities import capability_matrix
from earth_echo.catalog.overlay import load_overlay
from earth_echo.queries.forecasts import anomaly_table, experiment_report, forecast_dir
from earth_echo.queries.layers import quake_layer
from earth_echo.queries.trend import trend_view
from earth_echo.science.forecast_eval import replay


def phenomenon_capability(phenomenon_id: str) -> dict[str, Any]:
    found = next((item for item in capability_matrix().phenomena if item.id == phenomenon_id), None)
    if found is None:
        return {"tool": "capability", "found": False, "id": phenomenon_id}
    return {
        "tool": "capability",
        "found": True,
        "id": found.id,
        "name": found.name,
        "family": found.family,
        "outputs": [item.model_dump() for item in found.outputs],
    }


def source_status(source_id: str) -> dict[str, Any]:
    item = load_overlay().sources.get(source_id)  # type: ignore[arg-type]
    if item is None:
        return {
            "tool": "source",
            "source_id": source_id,
            "integration_status": "documented",
            "detail": "La fuente está en el catálogo y no tiene una integración operativa.",
        }
    return {
        "tool": "source",
        "source_id": source_id,
        "integration_status": item.integration_status,
        "detail": item.detail,
        "credential_variables": item.credential_variables,
    }


def sst_trend(cutoff: tuple[int, int] | None) -> dict[str, Any]:
    view = trend_view(cutoff)
    return {
        "tool": "sst_trend",
        "region_id": view.region_id,
        "unit": view.unit,
        "method_id": view.method_id,
        "status": view.status,
        "slope_c_per_year": view.slope_c_per_year,
        "interval_low_c_per_year": view.interval_low_c_per_year,
        "interval_high_c_per_year": view.interval_high_c_per_year,
        "present_months": view.present_months,
        "missing_months": view.missing_months,
        "reference_start": view.reference_start,
        "reference_end": view.reference_end,
        "analysis_start": view.analysis_start,
        "analysis_end": view.analysis_end,
        "cutoff": view.cutoff,
        "predictable": view.predictable,
        "cause": view.cause,
        "narrative": view.narrative,
        "link": "/v1/analyses/d15-sst",
    }


def sst_experiment(issue: tuple[int, int] | None, revealed: bool) -> dict[str, Any]:
    if issue is None:
        report = experiment_report()
        metrics = report["metrics"]
        analog = metrics["analog"]
        persistence = metrics["persistence"]
        climatology = metrics["climatology"]
        return {
            "tool": "sst_experiment",
            "experiment_id": report["experiment_id"],
            "experiment_class": report["experiment_class"],
            "validated_for_use": False,
            "additional_skill": report["additional_skill"],
            "reason": report["reason"],
            "cases_scored": report["cases_scored"],
            "cases_excluded": report["cases_excluded"],
            "mae_analog_c": None if analog is None else analog["mae_c"],
            "mae_persistence_c": None if persistence is None else persistence["mae_c"],
            "mae_climatology_c": None if climatology is None else climatology["mae_c"],
            "false_alarms": None if analog is None else analog["events"]["false_alarms"],
            "misses": None if analog is None else analog["events"]["misses"],
            "event_base_rate": report["event_base_rate"],
            "availability_note": report["availability_note"],
            "link": "/v1/experiments/sst-anomaly",
        }
    path = forecast_dir() / "replay" / f"{issue[0]:04d}-{issue[1]:02d}.json"
    if path.is_file():
        saved = json.loads(path.read_text(encoding="utf-8"))
        persisted = True
    else:
        saved = replay(anomaly_table(), issue)
        persisted = False
    payload = {
        "tool": "sst_experiment_replay",
        "experiment_id": "sst-anomaly-next-month-v1",
        "issue": f"{issue[0]:04d}-{issue[1]:02d}",
        "persisted": persisted,
        "validated_for_use": False,
        "analog_c": saved.get("analog_c"),
        "persistence_c": saved.get("persistence_c"),
        "climatology_c": saved.get("climatology_c"),
        "excluded_reason": saved.get("excluded_reason"),
        "outcome_revealed": False,
        "note": "El chat no guarda ni revela el desenlace. Eso lo hace el módulo científico.",
    }
    if revealed and persisted and saved.get("outcome_c") is not None:
        payload["outcome_c"] = saved["outcome_c"]
        payload["analog_error_c"] = saved.get("analog_error_c")
        payload["outcome_revealed"] = True
    return payload


def imported_kp() -> dict[str, Any]:
    path = forecast_dir() / "d28-kp-forecast.json"
    if not path.is_file():
        return {"tool": "imported_kp", "available": False, "probability": "absent"}
    payload = json.loads(path.read_text(encoding="utf-8"))
    steps = payload["steps"]
    return {
        "tool": "imported_kp",
        "available": True,
        "issued_at": payload["issued_at"],
        "retrieved_at": payload.get('retrieved_at',payload.get('archived_at')),
        "valid_start": steps[0]["valid_start"],
        "valid_end": steps[-1]["valid_end"],
        "step_count": len(steps),
        "first_kp": steps[0]["kp"],
        "last_kp": steps[-1]["kp"],
        "unit": "Kp",
        "probability": "absent",
        "validated_for_use": False,
        "note": payload["note"],
        "link": "/v1/forecasts/d28-kp",
    }


def quake_summary() -> dict[str, Any]:
    layer = quake_layer()
    times = [item.time for item in layer.features]
    return {
        "tool": "quakes",
        "count": layer.count,
        "unit": layer.unit,
        "earliest": min(times) if times else None,
        "latest": max(times) if times else None,
        "forecast": "absent",
        "note": "No hay una fecha prevista para el próximo sismo. La lista son eventos observados, no réplicas.",
        "link": "/v1/layers/d21-events",
    }
