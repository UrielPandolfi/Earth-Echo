"""Experimento de anomalía de SST a un mes. Los parámetros quedan fijos."""

from dataclasses import dataclass

EXPERIMENT_ID = "sst-anomaly-next-month-v1"
METHOD_VERSION = "1"
HORIZON_MONTHS = 1
ANALOG_NEIGHBORS = 3
EVENT_THRESHOLD_C = 0.3
MIN_CASES = 24
REFERENCE_START = (2014, 1)
REFERENCE_END = (2021, 12)
TEST_START = (2022, 1)
TEST_END = (2025, 11)


@dataclass(frozen=True)
class CasePrediction:
    issue: tuple[int, int]
    outcome_month: tuple[int, int]
    analog_c: float | None
    persistence_c: float
    climatology_c: float
    neighbors: list[tuple[int, int]]
    excluded_reason: str | None


def shift_month(year: int, month: int, steps: int) -> tuple[int, int]:
    index = year * 12 + (month - 1) + steps
    return index // 12, index % 12 + 1


def eligible_neighbors(
    anomalies: dict[tuple[int, int], float | None],
    issue: tuple[int, int],
) -> list[tuple[tuple[int, int], float]]:
    """Vecinos cuyo desenlace ya había ocurrido antes del mes de emisión."""
    antecedent = anomalies.get(issue)
    if antecedent is None:
        return []
    outcome_month = shift_month(*issue, HORIZON_MONTHS)[1]
    found: list[tuple[float, tuple[int, int], float]] = []
    for (year, month), outcome in anomalies.items():
        if month != outcome_month or outcome is None or (year, month) >= issue:
            continue
        neighbor_issue = shift_month(year, month, -HORIZON_MONTHS)
        if neighbor_issue >= issue:
            continue
        neighbor_value = anomalies.get(neighbor_issue)
        if neighbor_value is None:
            continue
        found.append((abs(neighbor_value - antecedent), (year, month), outcome))
    found.sort(key=lambda item: (item[0], item[1]))
    return [(item[1], item[2]) for item in found[:ANALOG_NEIGHBORS]]


def predict_case(
    anomalies: dict[tuple[int, int], float | None],
    issue: tuple[int, int],
) -> CasePrediction:
    outcome_month = shift_month(*issue, HORIZON_MONTHS)
    antecedent = anomalies.get(issue)
    if antecedent is None:
        return CasePrediction(issue, outcome_month, None, 0.0, 0.0, [], "El mes de emisión no tiene anomalía.")
    neighbors = eligible_neighbors(anomalies, issue)
    if len(neighbors) < ANALOG_NEIGHBORS:
        return CasePrediction(
            issue,
            outcome_month,
            None,
            antecedent,
            0.0,
            [item[0] for item in neighbors],
            f"Hay {len(neighbors)} análogos elegibles y el método pide {ANALOG_NEIGHBORS}.",
        )
    analog = sum(item[1] for item in neighbors) / len(neighbors)
    return CasePrediction(issue, outcome_month, analog, antecedent, 0.0, [item[0] for item in neighbors], None)


def _in_test(issue: tuple[int, int]) -> bool:
    return TEST_START <= issue <= TEST_END


def evaluate(anomalies: dict[tuple[int, int], float | None]) -> dict[str, object]:
    predictions: list[dict[str, object]] = []
    scored: list[tuple[CasePrediction, float]] = []
    excluded = 0
    for issue in sorted(anomalies):
        if not _in_test(issue):
            continue
        prediction = predict_case(anomalies, issue)
        outcome = anomalies.get(prediction.outcome_month)
        record = {
            "issue": list(issue),
            "outcome_month": list(prediction.outcome_month),
            "analog_c": prediction.analog_c,
            "persistence_c": prediction.persistence_c,
            "climatology_c": prediction.climatology_c,
            "neighbors": [list(item) for item in prediction.neighbors],
            "excluded_reason": prediction.excluded_reason,
            "outcome_c": None,
        }
        if prediction.excluded_reason is not None or outcome is None:
            excluded += 1
            if outcome is None and prediction.excluded_reason is None:
                record["excluded_reason"] = "El desenlace no está en la serie."
            predictions.append(record)
            continue
        record["outcome_c"] = outcome
        predictions.append(record)
        scored.append((prediction, outcome))
    summary = _summarize(scored, excluded)
    summary["cases"] = predictions
    return summary


def replay(anomalies: dict[tuple[int, int], float | None], issue: tuple[int, int]) -> dict[str, object]:
    """Predicción sin desenlace. El desenlace se agrega en una operación aparte."""
    prediction = predict_case(anomalies, issue)
    return {
        "experiment_id": EXPERIMENT_ID,
        "issue": list(issue),
        "outcome_month": list(prediction.outcome_month),
        "analog_c": prediction.analog_c,
        "persistence_c": prediction.persistence_c,
        "climatology_c": prediction.climatology_c,
        "neighbors": [list(item) for item in prediction.neighbors],
        "excluded_reason": prediction.excluded_reason,
        "availability": "unknown",
        "experiment_class": "retrospective_reconstructed",
    }


def _event_counts(pairs: list[tuple[float, float]]) -> dict[str, int]:
    hits = false_alarms = misses = quiet = 0
    for predicted, observed in pairs:
        event = observed > EVENT_THRESHOLD_C
        alarm = predicted > EVENT_THRESHOLD_C
        if alarm and event:
            hits += 1
        elif alarm and not event:
            false_alarms += 1
        elif not alarm and event:
            misses += 1
        else:
            quiet += 1
    return {"hits": hits, "false_alarms": false_alarms, "misses": misses, "quiet": quiet}


def _mae(errors: list[float]) -> float | None:
    if not errors:
        return None
    return sum(abs(item) for item in errors) / len(errors)


def _bias(errors: list[float]) -> float | None:
    if not errors:
        return None
    return sum(errors) / len(errors)


def _summarize(scored: list[tuple[CasePrediction, float]], excluded: int) -> dict[str, object]:
    count = len(scored)
    methods = {
        "analog": [item.analog_c for item, _outcome in scored],
        "persistence": [item.persistence_c for item, _outcome in scored],
        "climatology": [item.climatology_c for item, _outcome in scored],
    }
    outcomes = [outcome for _item, outcome in scored]
    metrics = {}
    for name, forecasts in methods.items():
        if any(item is None for item in forecasts):
            metrics[name] = None
            continue
        errors = [forecast - outcome for forecast, outcome in zip(forecasts, outcomes, strict=True)]
        metrics[name] = {
            "mae_c": _mae(errors),
            "bias_c": _bias(errors),
            "events": _event_counts([(float(forecast), outcome) for forecast, outcome in zip(forecasts, outcomes, strict=True)]),
        }
    analog = metrics["analog"]
    persistence = metrics["persistence"]
    climatology = metrics["climatology"]
    skill = False
    reason = "No hay casos suficientes para comparar métodos."
    if count < MIN_CASES or analog is None or persistence is None or climatology is None:
        reason = f"Hay {count} casos puntuables y el informe pide al menos {MIN_CASES}."
    else:
        skill = analog["mae_c"] < persistence["mae_c"] and analog["mae_c"] < climatology["mae_c"]
        reason = (
            "El análogo tiene menor error absoluto que la persistencia y que la climatología. Sigue siendo experimental."
            if skill
            else "No se demostró un error menor que la persistencia y la climatología. El experimento no queda validado."
        )
    base = None
    if count:
        base = sum(outcome > EVENT_THRESHOLD_C for outcome in outcomes) / count
    return {
        "experiment_id": EXPERIMENT_ID,
        "method_version": METHOD_VERSION,
        "experiment_class": "retrospective_reconstructed",
        "capability_status": "experimental",
        "validated_for_use": False,
        "additional_skill": skill,
        "reason": reason,
        "target": "Anomalía de SST del mes siguiente, en °C, en el recorte del Caribe occidental.",
        "event_threshold_c": EVENT_THRESHOLD_C,
        "event_base_rate": base,
        "cases_scored": count,
        "cases_excluded": excluded,
        "independent_cases": None,
        "metrics": metrics,
        "availability_note": (
            "La serie mensual no trae available_at. El corte oculta meses posteriores en las entradas, "
            "pero el experimento no afirma fidelidad operativa al momento de publicación."
        ),
    }
