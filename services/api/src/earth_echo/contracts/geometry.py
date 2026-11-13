"""Geometría GeoJSON en orden longitud, latitud, y extensión geográfica."""

import math
from typing import Annotated, Literal

from pydantic import Field, model_validator

from earth_echo.contracts.types import ApiModel, SpatialRole


def _finite(values: list[float], label: str) -> None:
    if not values or any(not math.isfinite(item) for item in values):
        raise ValueError(f"{label}: las coordenadas deben ser finitas.")


def _position(coordinates: list[float], label: str) -> None:
    if len(coordinates) not in (2, 3):
        raise ValueError(f"{label}: se esperan longitud, latitud y una altura opcional.")
    _finite(coordinates, label)
    longitude, latitude = coordinates[0], coordinates[1]
    if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
        raise ValueError(f"{label}: longitud o latitud fuera de rango.")


def _reject_dateline_jump(positions: list[list[float]], label: str) -> None:
    for start, end in zip(positions, positions[1:], strict=False):
        if abs(end[0] - start[0]) > 180:
            raise ValueError(
                f"{label}: hay un salto de longitud mayor a 180 grados. "
                "Dividí la geometría en un MultiPolygon o MultiLineString que no cruce el antimeridiano."
            )


class GeographicExtent(ApiModel):
    west: float
    south: float
    east: float
    north: float
    crosses_antimeridian: bool
    crs: Literal["EPSG:4326"] = "EPSG:4326"

    @model_validator(mode="after")
    def check_bounds(self) -> "GeographicExtent":
        for name, value in (("west", self.west), ("east", self.east)):
            if not math.isfinite(value) or not -180 <= value <= 180:
                raise ValueError(f"{name} debe estar entre -180 y 180.")
        if not math.isfinite(self.south) or not math.isfinite(self.north):
            raise ValueError("Las latitudes deben ser finitas.")
        if not -90 <= self.south <= self.north <= 90:
            raise ValueError("El rango de latitud es inválido.")
        if self.crosses_antimeridian and self.west <= self.east:
            raise ValueError(
                "Si la extensión cruza el antimeridiano, west debe ser mayor que east."
            )
        if not self.crosses_antimeridian and self.west > self.east:
            raise ValueError(
                "west es mayor que east. Marcá crosses_antimeridian o corregí el orden."
            )
        return self


def extent_contains(extent: GeographicExtent, longitude: float, latitude: float) -> bool:
    if not extent.south <= latitude <= extent.north:
        return False
    if extent.crosses_antimeridian:
        return longitude >= extent.west or longitude <= extent.east
    return extent.west <= longitude <= extent.east


class VerticalPosition(ApiModel):
    value: float
    unit: str = Field(min_length=1)
    datum: str = Field(min_length=1)
    direction: Literal["down", "up"]

    @model_validator(mode="after")
    def finite_value(self) -> "VerticalPosition":
        if not math.isfinite(self.value):
            raise ValueError("La posición vertical debe ser finita.")
        return self


class GeoPoint(ApiModel):
    type: Literal["Point"]
    coordinates: list[float]

    @model_validator(mode="after")
    def check(self) -> "GeoPoint":
        _position(self.coordinates, "Point")
        return self


class GeoMultiPoint(ApiModel):
    type: Literal["MultiPoint"]
    coordinates: list[list[float]]

    @model_validator(mode="after")
    def check(self) -> "GeoMultiPoint":
        if not self.coordinates:
            raise ValueError("MultiPoint necesita al menos una posición.")
        for index, position in enumerate(self.coordinates):
            _position(position, f"MultiPoint[{index}]")
        return self


class GeoLineString(ApiModel):
    type: Literal["LineString"]
    coordinates: list[list[float]]

    @model_validator(mode="after")
    def check(self) -> "GeoLineString":
        if len(self.coordinates) < 2:
            raise ValueError("LineString necesita al menos dos posiciones.")
        for index, position in enumerate(self.coordinates):
            _position(position, f"LineString[{index}]")
        _reject_dateline_jump(self.coordinates, "LineString")
        return self


class GeoMultiLineString(ApiModel):
    type: Literal["MultiLineString"]
    coordinates: list[list[list[float]]]

    @model_validator(mode="after")
    def check(self) -> "GeoMultiLineString":
        if not self.coordinates:
            raise ValueError("MultiLineString necesita al menos una línea.")
        for line_index, line in enumerate(self.coordinates):
            if len(line) < 2:
                raise ValueError(f"MultiLineString[{line_index}] necesita dos posiciones.")
            for index, position in enumerate(line):
                _position(position, f"MultiLineString[{line_index}][{index}]")
            _reject_dateline_jump(line, f"MultiLineString[{line_index}]")
        return self


def _check_ring(ring: list[list[float]], label: str) -> None:
    if len(ring) < 4:
        raise ValueError(f"{label}: un anillo cerrado necesita al menos cuatro posiciones.")
    for index, position in enumerate(ring):
        _position(position, f"{label}[{index}]")
    if ring[0] != ring[-1]:
        raise ValueError(f"{label}: el anillo debe cerrarse repitiendo la primera posición.")
    _reject_dateline_jump(ring, label)


class GeoPolygon(ApiModel):
    type: Literal["Polygon"]
    coordinates: list[list[list[float]]]

    @model_validator(mode="after")
    def check(self) -> "GeoPolygon":
        if not self.coordinates:
            raise ValueError("Polygon necesita un anillo exterior.")
        for index, ring in enumerate(self.coordinates):
            _check_ring(ring, f"Polygon[{index}]")
        return self


class GeoMultiPolygon(ApiModel):
    type: Literal["MultiPolygon"]
    coordinates: list[list[list[list[float]]]]

    @model_validator(mode="after")
    def check(self) -> "GeoMultiPolygon":
        if not self.coordinates:
            raise ValueError("MultiPolygon necesita al menos un polígono.")
        for polygon_index, polygon in enumerate(self.coordinates):
            if not polygon:
                raise ValueError(f"MultiPolygon[{polygon_index}] está vacío.")
            for ring_index, ring in enumerate(polygon):
                _check_ring(ring, f"MultiPolygon[{polygon_index}][{ring_index}]")
        return self


Geometry = Annotated[
    GeoPoint | GeoMultiPoint | GeoLineString | GeoMultiLineString | GeoPolygon | GeoMultiPolygon,
    Field(discriminator="type"),
]


class SpatialSupport(ApiModel):
    role: SpatialRole
    region_id: str | None = None
    grid_id: str | None = None
    extent: GeographicExtent | None = None
    geometry: Geometry | None = None
    vertical: VerticalPosition | None = None
    resolution_note: str | None = None

    @model_validator(mode="after")
    def check_role(self) -> "SpatialSupport":
        if self.geometry is None and self.extent is None:
            raise ValueError("El soporte espacial necesita geometría o extensión.")
        if self.role == "region_anchor":
            if self.region_id is None or not self.region_id.strip():
                raise ValueError("Un punto o área de síntesis regional debe identificar la región.")
        elif self.region_id is not None:
            raise ValueError("region_id solo corresponde al rol region_anchor.")
        if self.role == "grid_cell" and (self.grid_id is None or not self.grid_id.strip()):
            raise ValueError("Una celda debe identificar su malla.")
        if self.role not in {"grid_cell", "gridded_product"} and self.grid_id is not None:
            raise ValueError("grid_id no corresponde a este rol espacial.")
        if (
            isinstance(self.geometry, GeoPoint)
            and self.extent is not None
            and not extent_contains(
                self.extent,
                self.geometry.coordinates[0],
                self.geometry.coordinates[1],
            )
        ):
            raise ValueError("El punto queda fuera de la extensión geográfica.")
        return self
