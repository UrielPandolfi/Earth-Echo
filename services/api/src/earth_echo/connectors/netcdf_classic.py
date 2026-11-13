"""Lector mínimo de NetCDF clásico (CDF-1) para un subconjunto ya descargado.

No descarga ni interpreta HDF5. Sirve para el NetCDF-3 que devuelve ERDDAP
en la extensión `.nc` de este recorrido.
"""

import struct
from pathlib import Path

NC_BYTE = 1
NC_CHAR = 2
NC_SHORT = 3
NC_INT = 4
NC_FLOAT = 5
NC_DOUBLE = 6
NC_DIMENSION = 10
NC_VARIABLE = 11
NC_ATTRIBUTE = 12

_TYPE_SIZE = {
    NC_BYTE: 1,
    NC_CHAR: 1,
    NC_SHORT: 2,
    NC_INT: 4,
    NC_FLOAT: 4,
    NC_DOUBLE: 8,
}


class NetCdfError(ValueError):
    pass


class ClassicNetCdf:
    def __init__(self, path: Path) -> None:
        self.path = path
        blob = path.read_bytes()
        if blob[:3] != b"CDF" or blob[3] != 1:
            raise NetCdfError("El archivo no es NetCDF clásico CDF-1.")
        self._blob = blob
        self._pos = 4
        self.record_count = self._i32()
        self.dimensions = self._dimensions()
        self.attributes = self._attributes()
        self.variables = self._variables()

    def values(self, name: str) -> list[float]:
        variable = self.variables[name]
        nc_type = variable["type"]
        if nc_type == NC_DOUBLE:
            code, size = "d", 8
        elif nc_type == NC_FLOAT:
            code, size = "f", 4
        else:
            raise NetCdfError(f"{name} no está guardada como número de punto flotante.")
        count = 1
        for dim in variable["dimensions"]:
            count *= self.dimensions[dim]
        start = int(variable["offset"])
        end = start + count * size
        if end > len(self._blob):
            raise NetCdfError(f"{name} se sale del archivo.")
        return [float(item) for item in struct.unpack(f">{count}{code}", self._blob[start:end])]

    def _i32(self) -> int:
        value = struct.unpack_from(">i", self._blob, self._pos)[0]
        self._pos += 4
        return value

    def _name(self) -> str:
        length = self._i32()
        if length < 0 or self._pos + length > len(self._blob):
            raise NetCdfError("Nombre de NetCDF inválido.")
        raw = self._blob[self._pos : self._pos + length]
        self._pos += length
        self._pos += (4 - (length % 4)) % 4
        return raw.decode("ascii")

    def _dimensions(self) -> dict[str, int]:
        tag = self._i32()
        if tag == 0:
            if self._i32() != 0:
                raise NetCdfError("La lista de dimensiones ausente está mal formada.")
            return {}
        if tag != NC_DIMENSION:
            raise NetCdfError("No se encontró la lista de dimensiones.")
        count = self._i32()
        found: dict[str, int] = {}
        for _ in range(count):
            name = self._name()
            found[name] = self._i32()
        return found

    def _attributes(self) -> dict[str, object]:
        tag = self._i32()
        if tag == 0:
            if self._i32() != 0:
                raise NetCdfError("La lista de atributos ausente está mal formada.")
            return {}
        if tag != NC_ATTRIBUTE:
            raise NetCdfError("No se encontró la lista de atributos.")
        count = self._i32()
        found: dict[str, object] = {}
        for _ in range(count):
            name = self._name()
            nc_type = self._i32()
            length = self._i32()
            found[name] = self._values(nc_type, length)
        return found

    def _values(self, nc_type: int, length: int) -> object:
        size = _TYPE_SIZE.get(nc_type)
        if size is None or length < 0:
            raise NetCdfError("Tipo o longitud de atributo no soportados.")
        raw_size = size * length
        raw = self._blob[self._pos : self._pos + raw_size]
        self._pos += raw_size
        self._pos += (4 - (raw_size % 4)) % 4
        if nc_type == NC_CHAR:
            return raw.decode("ascii", errors="replace").rstrip("\x00")
        if nc_type == NC_DOUBLE:
            values = struct.unpack(f">{length}d", raw)
            return values[0] if length == 1 else list(values)
        if nc_type == NC_FLOAT:
            values = struct.unpack(f">{length}f", raw)
            return values[0] if length == 1 else list(values)
        if nc_type == NC_INT:
            values = struct.unpack(f">{length}i", raw)
            return values[0] if length == 1 else list(values)
        if nc_type == NC_SHORT:
            values = struct.unpack(f">{length}h", raw)
            return values[0] if length == 1 else list(values)
        return raw

    def _variables(self) -> dict[str, dict[str, object]]:
        tag = self._i32()
        if tag == 0:
            if self._i32() != 0:
                raise NetCdfError("La lista de variables ausente está mal formada.")
            return {}
        if tag != NC_VARIABLE:
            raise NetCdfError("No se encontró la lista de variables.")
        count = self._i32()
        names = list(self.dimensions)
        found: dict[str, dict[str, object]] = {}
        for _ in range(count):
            name = self._name()
            dim_count = self._i32()
            dim_ids = [self._i32() for _ in range(dim_count)]
            attributes = self._attributes()
            nc_type = self._i32()
            self._i32()
            offset = self._i32()
            found[name] = {
                "dimensions": [names[item] for item in dim_ids],
                "attributes": attributes,
                "type": nc_type,
                "offset": offset,
            }
        return found
