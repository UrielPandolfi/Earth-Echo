"""Norm of a mean horizontal velocity, not the mean of instantaneous speeds."""
import math


def mean_velocity_norm(u, v):
    if u is None or v is None or not math.isfinite(u) or not math.isfinite(v):
        return None
    return math.hypot(u, v)
