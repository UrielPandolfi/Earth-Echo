"""WGS84 display paths; boundary interpolation does not create observations."""
from earth_echo.contracts.geometry import GeoMultiLineString,GeographicExtent

def split_dateline(positions: list[list[float]]) -> GeoMultiLineString:
    parts=[]; line=[positions[0]]
    for start,end in zip(positions,positions[1:]):
        jump=end[0]-start[0]
        if abs(jump)>180:
            unwrapped=end[0]-360 if jump>180 else end[0]+360
            edge=-180. if jump>180 else 180.
            fraction=(edge-start[0])/(unwrapped-start[0])
            latitude=start[1]+fraction*(end[1]-start[1])
            boundary=[edge,latitude]
            if line[-1]!=boundary: line.append(boundary)
            if len(line)>=2: parts.append(line)
            line=[[-edge,latitude]]
        if line[-1]!=end: line.append(end)
    if len(line)>=2: parts.append(line)
    # Stationary published centres still form a valid time-ordered path.
    if not parts: parts=[[positions[0],positions[-1]]]
    return GeoMultiLineString(type='MultiLineString',coordinates=parts)

def path_extent(positions: list[list[float]]) -> GeographicExtent:
    lons=sorted({p[0] for p in positions}); lats=[p[1] for p in positions]
    if len(lons)==1: west=east=lons[0]
    else:
        gap=max(range(len(lons)),key=lambda i:(lons[(i+1)%len(lons)]-lons[i])%360)
        west,east=lons[(gap+1)%len(lons)],lons[gap]
    return GeographicExtent(west=west,east=east,south=min(lats),north=max(lats),crosses_antimeridian=west>east)
