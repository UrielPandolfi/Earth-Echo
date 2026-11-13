"""Explicit, testable conversions. Missing values stay missing."""
def kelvin_to_celsius(value: float | None) -> float | None:
    return None if value is None else value - 273.15

def metres_to_mm(value: float | None) -> float | None:
    return None if value is None else value * 1000
