"""Cell support and exploration rules. No forecast probability is calculated here."""
from bisect import bisect_right
import math
from earth_echo.contracts.products import ScientificGrid
from earth_echo.contracts.geometry import GeographicExtent, GeoMultiPolygon
from earth_echo.contracts.predictions import ForecastCell

CELL_RULE = ('Celda contenedora entre puntos medios de centros; bordes oeste/sur incluidos, '
             'este/norte excluidos (polo norte incluido). Empates: este/norte. '
             'Longitud normalizada a [-180,180); sin interpolación ni búsqueda de vecino válido. '
             'Para IFS es soporte de visualización 1°, valor de un nodo nativo 0,25°, no media de área.')
HIGHLIGHT_RULE = ('Componentes de celdas válidas con p >= filtro; conectividad 4 (lados), '
                  'unión cíclica sólo en longitud mundial, sin atravesar huecos o tierra enmascarada. '
                  'Representante: máximo p, empate fila norte→sur/columna oeste→este. '
                  'Orden: máximo p descendente, cantidad de celdas descendente, índice representante ascendente. '
                  'Se limita la lista después de ordenar; rangos por celda, sin probabilidad regional.')


def normalize_longitude(longitude: float) -> float:
    if not math.isfinite(longitude):
        raise ValueError('Nonfinite longitude')
    return (longitude + 180) % 360 - 180


def axes(grid: ScientificGrid):
    """Only qualified regular grids. Midpoints are scientific view supports, not coastlines."""
    xs, ys = grid.longitudes, list(reversed(grid.latitudes))
    if len(xs) < 2 or len(ys) < 2:
        raise ValueError('A field needs at least two centres per axis')
    dx, dy = xs[1]-xs[0], ys[1]-ys[0]
    if not all(math.isclose(b-a, dx, abs_tol=1e-6) for a,b in zip(xs,xs[1:])) or not all(math.isclose(b-a,dy,abs_tol=1e-6) for a,b in zip(ys,ys[1:])):
        raise ValueError('Unqualified irregular grid')
    wrap = math.isclose(dx*len(xs), 360, abs_tol=1e-6)
    xe = [xs[0]-dx/2] + [(a+b)/2 for a,b in zip(xs,xs[1:])] + [xs[-1]+dx/2]
    ye = [max(-90,ys[0]-dy/2)] + [(a+b)/2 for a,b in zip(ys,ys[1:])] + [min(90,ys[-1]+dy/2)]
    return xe, ye, wrap


def locate(grid: ScientificGrid, longitude: float, latitude: float) -> tuple[int,int] | None:
    xe, ye, wrap = axes(grid)
    lon = normalize_longitude(longitude)
    if wrap:
        lon = (lon-xe[0]) % 360 + xe[0]
    if not xe[0] <= lon < xe[-1] or not ye[0] <= latitude <= ye[-1]:
        return None
    # A finite northern boundary belongs to the next (absent) cell, except90°.
    if latitude == ye[-1] and latitude != 90:
        return None
    col = bisect_right(xe,lon)-1
    south_row = min(bisect_right(ye,latitude)-1,grid.height-1)
    return grid.height-1-south_row, col


def cell_at(grid: ScientificGrid, row: int, column: int) -> ForecastCell:
    xe, ye, _ = axes(grid)
    west,east=xe[column:column+2]
    south,north=ye[grid.height-1-row:grid.height+1-row]
    if west < -180:
        parts=[(-180,east),(west+360,180)]
    elif east > 180:
        parts=[(west,180),(-180,east-360)]
    else:
        parts=[(west,east)]
    crossing=len(parts)>1
    extent=GeographicExtent(west=normalize_longitude(west),east=east if east<=180 else east-360,
                            south=south,north=north,crosses_antimeridian=crossing)
    geometry=GeoMultiPolygon(type='MultiPolygon',coordinates=[[[[w,south],[e,south],[e,north],[w,north],[w,south]]] for w,e in parts])
    return ForecastCell(id=f'r{row}-c{column}',row=row,column=column,longitude=grid.longitudes[column],latitude=grid.latitudes[row],
                        extent=extent,geometry=geometry,support_note=grid.resolution+'; límites de soporte entre centros, no un contorno costero.')


def components(grid: ScientificGrid, threshold: float):
    """Stable, mask-respecting discovery; no centroid or independent-cell assumption."""
    _,_,wrap=axes(grid)
    selected={i for i,v in enumerate(grid.values) if v is not None and v>=threshold}
    matching=len(selected)
    groups=[]
    for seed in range(len(grid.values)):
        if seed not in selected:continue
        selected.remove(seed)
        stack=[seed]; members=[]
        while stack:
            index=stack.pop(); members.append(index)
            r,c=divmod(index,grid.width)
            neighbors=[]
            if r:neighbors.append(index-grid.width)
            if r+1<grid.height:neighbors.append(index+grid.width)
            if c:neighbors.append(index-1)
            elif wrap:neighbors.append(index+grid.width-1)
            if c+1<grid.width:neighbors.append(index+1)
            elif wrap:neighbors.append(index-grid.width+1)
            for candidate in neighbors:
                if candidate in selected:selected.remove(candidate);stack.append(candidate)
        rep=min(members,key=lambda i:(-grid.values[i],i))
        groups.append((rep,len(members),min(grid.values[i] for i in members),grid.values[rep]))
    return matching,sorted(groups,key=lambda g:(-g[3],-g[1],g[0]))
