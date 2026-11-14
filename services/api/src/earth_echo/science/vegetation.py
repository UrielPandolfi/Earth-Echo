"""Spectral index with an explicit conservative domain; no crop diagnosis."""
import math


def ndvi(red:float|None,nir:float|None)->float|None:
    if red is None or nir is None or not all(math.isfinite(v) and v>=0 for v in (red,nir)) or red+nir<=0:
        return None
    return (nir-red)/(nir+red)
