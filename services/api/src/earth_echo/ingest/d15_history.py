"""Serie mensual histórica del mismo recorte y la misma colección CoralTemp."""

import calendar
import json
from pathlib import Path

from earth_echo.catalog.load import file_sha256
from earth_echo.connectors.crw_sst import (
    DATASET_ID,
    PRODUCT_VERSION,
    REQUEST_EAST,
    REQUEST_NORTH,
    REQUEST_SOUTH,
    REQUEST_WEST,
    decode_subset,
    fetch_month,
)
from earth_echo.paths import repo_root
from earth_echo.science.series import (
    METHOD_ID,
    METHOD_VERSION,
    PRACTICAL_CHANGE_PER_YEAR,
    month_mean,
    weighted_mean,
)

HISTORY_START = 2014
HISTORY_END = 2025
REFERENCE_START = (2014, 1)
REFERENCE_END = (2021, 12)
ANALYSIS_START = (2014, 1)
ANALYSIS_END = (2025, 12)


def history_dir() -> Path:
    return repo_root() / "data" / "real" / "d15" / "history"


def series_path() -> Path:
    return repo_root() / "data" / "real" / "d15" / "monthly_series.json"


def month_file(year: int, month: int) -> Path:
    return history_dir() / f"coraltemp-v3.1-caribe-{year:04d}-{month:02d}.nc"


def download_history() -> None:
    for year in range(HISTORY_START, HISTORY_END + 1):
        for month in range(1, 13):
            target = month_file(year, month)
            if target.is_file() and target.stat().st_size > 1000 and target.read_bytes()[:3] == b"CDF":
                continue
            print(f"pidiendo {year}-{month:02d}", flush=True)
            try:
                fetch_month(year, month, target)
            except Exception as error:
                print(f"falló {year}-{month:02d}: {error}", flush=True)
                if target.is_file() and target.read_bytes()[:3] != b"CDF":
                    target.unlink()
                continue
            print(f"{year}-{month:02d} {target.stat().st_size}", flush=True)


def build_monthly_series() -> dict[str, object]:
    assets: list[dict[str, object]] = []
    daily: dict[tuple[int, int], list[float | None]] = {}
    for year in range(HISTORY_START, HISTORY_END + 1):
        for month_number in range(1, 13):
            path = month_file(year, month_number)
            if not path.is_file() or path.read_bytes()[:3] != b"CDF":
                continue
            decoded = decode_subset(path)
            latitudes = decoded["latitudes"]
            days = decoded["days"]
            width = int(decoded["width"])
            if not isinstance(latitudes, list) or not isinstance(days, list):
                continue
            assets.append(
                {
                    "year": year,
                    "month": month_number,
                    "sha256": file_sha256(path),
                    "bytes": path.stat().st_size,
                    "collection_id": DATASET_ID,
                    "product_version": PRODUCT_VERSION,
                }
            )
            for day in days:
                if not isinstance(day, dict):
                    continue
                moment = day["time"]
                values = day["values"]
                if not hasattr(moment, "year") or not isinstance(values, list):
                    continue
                mean, _present = weighted_mean(values, [float(item) for item in latitudes], width)
                key = (int(moment.year), int(moment.month))
                daily.setdefault(key, []).append(mean)
    months = []
    cursor_year, cursor_month = ANALYSIS_START
    while (cursor_year, cursor_month) <= ANALYSIS_END:
        expected = calendar.monthrange(cursor_year, cursor_month)[1]
        observed = daily.get((cursor_year, cursor_month), [])
        value = month_mean(observed, expected)
        months.append(
            {
                "year": cursor_year,
                "month": cursor_month,
                "value": None if value is None else round(value, 4),
                "present_days": sum(item is not None for item in observed),
                "expected_days": expected,
            }
        )
        cursor_month += 1
        if cursor_month == 13:
            cursor_month = 1
            cursor_year += 1
    return {
        "schema_version": "1.0",
        "data_mode": "real",
        "method_id": METHOD_ID,
        "method_version": METHOD_VERSION,
        "source_id": "D15",
        "collection_id": DATASET_ID,
        "product_version": PRODUCT_VERSION,
        "variable_id": "V15",
        "region_id": "caribe-occidental",
        "region": {
            "west": REQUEST_WEST,
            "south": REQUEST_SOUTH,
            "east": REQUEST_EAST,
            "north": REQUEST_NORTH,
            "crosses_antimeridian": False,
        },
        "aggregation": (
            "Cada día es el promedio de las celdas válidas ponderado por el coseno de la latitud. "
            "Cada mes es el promedio de esos días si hay al menos el 80 % de los días del mes. "
            "Un día o un mes ausente queda en null y no se reemplaza por cero."
        ),
        "reference": {"start": list(REFERENCE_START), "end": list(REFERENCE_END)},
        "analysis": {"start": list(ANALYSIS_START), "end": list(ANALYSIS_END)},
        "practical_change_per_year": PRACTICAL_CHANGE_PER_YEAR,
        "assets": assets,
        "months": months,
    }


def write_monthly_series() -> Path:
    payload = build_monthly_series()
    target = series_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target
