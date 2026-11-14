"""Conservative display-only topology handling for static inventories."""
import math
from shapely import make_valid
from shapely.validation import explain_validity


def prepare_static_polygon(geometry):
    if geometry.is_empty:
        return geometry,False,'Geometría vacía no dibujada'
    if geometry.is_valid:
        return geometry,True,'Geometría nativa válida'
    reason=explain_validity(geometry)
    candidate=make_valid(geometry,method='structure',keep_collapsed=False)
    if (candidate.geom_type in ('Polygon','MultiPolygon') and candidate.is_valid
        and math.isclose(candidate.area,geometry.area,rel_tol=1e-10,abs_tol=1e-12)
        and all(math.isclose(a,b,abs_tol=1e-10,rel_tol=0) for a,b in zip(candidate.bounds,geometry.bounds))):
        return candidate,True,f'Topología normalizada sólo para visualizar con GEOS make_valid(structure); original: {reason}; área planar relativa conservada a 1e-10 y bbox a 1e-10°'
    return geometry,False,f'Geometría inválida no dibujada: {reason}'
