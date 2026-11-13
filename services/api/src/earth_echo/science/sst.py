"""Conversión mínima de SST. No estima blanqueamiento ni anomalía."""

import math


def celsius_or_missing(
    raw: float,
    *,
    fill_value: float | None,
    valid_min: float,
    valid_max: float,
    scale_factor: float = 1.0,
    add_offset: float = 0.0,
) -> float | None:
    """Pasa la unidad nativa a grados Celsius y descarta relleno."""
    if not math.isfinite(raw) or not math.isfinite(scale_factor) or not math.isfinite(add_offset):
        return None
    if fill_value is not None and math.isfinite(fill_value) and raw == fill_value:
        return None
    value = raw * scale_factor + add_offset
    if not math.isfinite(value) or value < valid_min or value > valid_max:
        return None
    return value


def mean_present(values: list[float | None]) -> tuple[float | None, int, int]:
    present = [item for item in values if item is not None]
    missing = len(values) - len(present)
    if not present:
        return None, 0, missing
    return sum(present) / len(present), len(present), missing
