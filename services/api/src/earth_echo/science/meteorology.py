"""Physical derived variables. No event detector or predictive validation implied."""
import math

def wind_speed(u: float | None,v: float | None) -> float | None:
    if u is None or v is None or not math.isfinite(u) or not math.isfinite(v): return None
    return math.hypot(u,v)

def saturation_vapour_pressure(temperature_c: float) -> float:
    return .6108*math.exp(17.27*temperature_c/(temperature_c+237.3))

def vapour_pressure_deficit(temperature_c: float | None,dewpoint_c: float | None) -> float | None:
    # Conservative applicability chosen by this implementation, not a claim of global validity over ice.
    if temperature_c is None or dewpoint_c is None or not all(math.isfinite(v) for v in (temperature_c,dewpoint_c)) or not 0<=dewpoint_c<=temperature_c<=50:
        return None
    return saturation_vapour_pressure(temperature_c)-saturation_vapour_pressure(dewpoint_c)
