"""Subconjunto público de CoralTemp v3.1. No descarga el NetCDF global."""

import math
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from earth_echo.connectors.netcdf_classic import ClassicNetCdf
from earth_echo.science.sst import celsius_or_missing

DATASET_ID = "noaacrwsstDaily"
PRODUCT_VERSION = "3.1"
VARIABLE = "analysed_sst"
DISCOVERY_URL = "https://coastwatch.noaa.gov/erddap/info/noaacrwsstDaily/index.json"
GRIDDAP = "https://coastwatch.noaa.gov/erddap/griddap/noaacrwsstDaily.nc"
REQUEST_WEST = -67.5
REQUEST_SOUTH = 16.5
REQUEST_EAST = -66.5
REQUEST_NORTH = 17.5
TIME_START = "2026-11-08T12:00:00Z"
TIME_END = "2026-11-11T12:00:00Z"
MAX_BYTES = 2_000_000
TIMEOUT_SECONDS = 30
SOURCE_PAGE = "https://coralreefwatch.noaa.gov/product/5km/index_5km_sst.php"


class CrwError(RuntimeError):
    pass


def subset_url() -> str:
    return (
        f"{GRIDDAP}?{VARIABLE}"
        f"[({TIME_START}):({TIME_END})]"
        f"[({REQUEST_SOUTH}):({REQUEST_NORTH})]"
        f"[({REQUEST_WEST}):({REQUEST_EAST})]"
    )


def logical_asset_key() -> str:
    return (
        f"D15|{DATASET_ID}|{PRODUCT_VERSION}|{VARIABLE}|{TIME_START}|{TIME_END}|"
        f"{REQUEST_WEST}|{REQUEST_SOUTH}|{REQUEST_EAST}|{REQUEST_NORTH}"
    )


def fetch_subset(destination: Path) -> None:
    """Baja solo el recorte reciente. Un reintento si el tiempo se agota."""
    _fetch(subset_url(), destination, MAX_BYTES, TIMEOUT_SECONDS)


def fetch_month(year: int, month: int, destination: Path) -> None:
    last_day = __import__("calendar").monthrange(year, month)[1]
    url = (
        f"{GRIDDAP}?{VARIABLE}"
        f"[({year:04d}-{month:02d}-01T12:00:00Z):({year:04d}-{month:02d}-{last_day:02d}T12:00:00Z)]"
        f"[({REQUEST_SOUTH}):({REQUEST_NORTH})]"
        f"[({REQUEST_WEST}):({REQUEST_EAST})]"
    )
    _fetch(url, destination, 500_000, 90)


def fetch_year(year: int, destination: Path) -> None:
    url = (
        f"{GRIDDAP}?{VARIABLE}"
        f"[({year}-01-01T12:00:00Z):({year}-12-31T12:00:00Z)]"
        f"[({REQUEST_SOUTH}):({REQUEST_NORTH})]"
        f"[({REQUEST_WEST}):({REQUEST_EAST})]"
    )
    _fetch(url, destination, 4_000_000, 180)


def _fetch(url: str, destination: Path, max_bytes: int, timeout: int) -> None:
    last_error: Exception | None = None
    for _ in range(2):
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(_read_limited(url, max_bytes, timeout))
            return
        except TimeoutError as error:
            last_error = error
        except URLError as error:
            reason = getattr(error, "reason", error)
            if isinstance(reason, TimeoutError):
                last_error = error
                continue
            raise CrwError("Coral Reef Watch no respondió.") from error
    raise CrwError("Coral Reef Watch no respondió a tiempo.") from last_error


def _read_limited(url: str, max_bytes: int = MAX_BYTES, timeout: int = TIMEOUT_SECONDS) -> bytes:
    request = Request(url, headers={"User-Agent": "EarthEcho/0.1"})
    with urlopen(request, timeout=timeout) as response:
        content_type = str(response.headers.get("Content-Type", ""))
        chunks: list[bytes] = []
        total = 0
        while True:
            block = response.read(65_536)
            if not block:
                break
            total += len(block)
            if total > max_bytes:
                raise CrwError("La respuesta supera el tamaño máximo pedido.")
            chunks.append(block)
    body = b"".join(chunks)
    ensure_netcdf(content_type, body)
    return body


def ensure_netcdf(content_type: str, body: bytes) -> None:
    if "html" in content_type.lower() or body.lstrip()[:1] == b"<":
        raise CrwError("La respuesta parece HTML de autenticación o de error, no un NetCDF.")
    if not body.startswith(b"CDF"):
        raise CrwError("La respuesta no es un NetCDF clásico.")


def round_coordinate(value: float) -> float:
    return round(value, 3)


def decode_subset(path: Path) -> dict[str, object]:
    dataset = ClassicNetCdf(path)
    variable = dataset.variables[VARIABLE]
    attributes = variable["attributes"]
    if not isinstance(attributes, dict):
        raise CrwError("La variable SST no tiene atributos.")
    if attributes.get("units") != "degree_C":
        raise CrwError("La unidad nativa no es degree_C. No se convirtió.")
    if attributes.get("standard_name") != "sea_surface_temperature":
        raise CrwError("La variable no es sea_surface_temperature.")
    fill = attributes.get("_FillValue")
    valid_min = attributes.get("valid_min")
    valid_max = attributes.get("valid_max")
    scale = attributes.get("scale_factor", 1.0)
    offset = attributes.get("add_offset", 0.0)
    if not isinstance(valid_min, (int, float)) or not isinstance(valid_max, (int, float)):
        raise CrwError("El producto no declara el rango válido de SST.")
    latitudes = [round_coordinate(item) for item in dataset.values("latitude")]
    longitudes = [round_coordinate(item) for item in dataset.values("longitude")]
    times = [
        datetime.fromtimestamp(item, timezone.utc).replace(microsecond=0)
        for item in dataset.values("time")
    ]
    raw = dataset.values(VARIABLE)
    expected = len(times) * len(latitudes) * len(longitudes)
    if len(raw) != expected:
        raise CrwError("La malla decodificada no coincide con las dimensiones.")
    days: list[dict[str, object]] = []
    width = len(longitudes)
    height = len(latitudes)
    for index, moment in enumerate(times):
        start = index * width * height
        slab = raw[start : start + width * height]
        values: list[float | None] = [
            celsius_or_missing(
                item,
                fill_value=float(fill) if isinstance(fill, (int, float)) else None,
                valid_min=float(valid_min),
                valid_max=float(valid_max),
                scale_factor=float(scale),
                add_offset=float(offset),
            )
            for item in slab
        ]
        present = [item for item in values if item is not None]
        days.append(
            {
                "time": moment,
                "values": values,
                "valid_count": len(present),
                "missing_count": len(values) - len(present),
                "minimum": min(present) if present else None,
                "maximum": max(present) if present else None,
                "mean": sum(present) / len(present) if present else None,
            }
        )
    half = 0.025
    return {
        "latitudes": latitudes,
        "longitudes": longitudes,
        "width": width,
        "height": height,
        "west": min(longitudes) - half,
        "south": min(latitudes) - half,
        "east": max(longitudes) + half,
        "north": max(latitudes) + half,
        "days": days,
        "fill_value": fill,
    }


def cell_value(decoded: dict[str, object], moment: datetime, latitude: float, longitude: float) -> float | None:
    latitudes = decoded["latitudes"]
    longitudes = decoded["longitudes"]
    days = decoded["days"]
    if not isinstance(latitudes, list) or not isinstance(longitudes, list) or not isinstance(days, list):
        return None
    day = next((item for item in days if isinstance(item, dict) and item["time"] == moment), None)
    if not isinstance(day, dict):
        return None
    values = day["values"]
    if not isinstance(values, list):
        return None
    try:
        row = latitudes.index(round_coordinate(latitude))
        column = longitudes.index(round_coordinate(longitude))
    except ValueError:
        return None
    width = int(decoded["width"])
    found = values[row * width + column]
    return float(found) if isinstance(found, (int, float)) and math.isfinite(float(found)) else None

