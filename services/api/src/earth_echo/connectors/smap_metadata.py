"""Activo de metadatos SMAP (D02). No lee el HDF ni inventa humedad."""

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from earth_echo.catalog.load import file_sha256
from earth_echo.contracts.geometry import GeographicExtent, SpatialSupport
from earth_echo.contracts.records import (
    AssetRecord,
    AvailabilityUnknown,
    IntervalSpan,
    Provenance,
    Quality,
)
from earth_echo.contracts.types import Sha256
from earth_echo.paths import repo_root

SAMPLE_DIR = Path("data/samples/d02-smap")
_VERSION = re.compile(r"\bV(\d{3})\b")


def sample_paths() -> tuple[Path, Path]:
    root = repo_root()
    return root / SAMPLE_DIR / "cmr-granule.json", root / SAMPLE_DIR / "retrieval.json"


def parse_cmr_box(value: str) -> GeographicExtent:
    parts = value.split()
    if len(parts) != 4:
        raise ValueError("El recuadro CMR debe tener sur, oeste, norte y este.")
    south, west, north, east = (float(item) for item in parts)
    return GeographicExtent(
        west=west,
        south=south,
        east=east,
        north=north,
        crosses_antimeridian=west > east,
    )


def exclusive_end(start: datetime, provider_end: datetime) -> datetime:
    """Convierte el fin inclusivo de un día CMR al fin exclusivo del contrato."""
    next_midnight = datetime(start.year, start.month, start.day, tzinfo=timezone.utc) + timedelta(days=1)
    if start.date() == provider_end.astimezone(timezone.utc).date() and (next_midnight - provider_end) <= timedelta(seconds=2):
        return next_midnight
    if provider_end <= start:
        raise ValueError("El intervalo del gránulo no tiene fin posterior al inicio.")
    return provider_end


def build_smap_asset(
    entry: dict,
    *,
    ingested_at: datetime,
    checksum: Sha256,
    byte_size: int,
) -> AssetRecord:
    boxes = entry.get("boxes") or []
    if len(boxes) != 1:
        raise ValueError("La muestra CMR esperada tiene un solo recuadro.")
    start = datetime.fromisoformat(str(entry["time_start"]).replace("Z", "+00:00"))
    provider_end = datetime.fromisoformat(str(entry["time_end"]).replace("Z", "+00:00"))
    end = exclusive_end(start, provider_end)
    version_match = _VERSION.search(str(entry.get("dataset_id", "")))
    product_version = version_match.group(1) if version_match else None
    granule_id = str(entry["id"])
    spatial = SpatialSupport(
        role="gridded_product",
        grid_id="EASE-Grid-9km",
        extent=parse_cmr_box(str(boxes[0])),
        resolution_note=(
            "Extensión geográfica informada por CMR. La malla del producto es EASE; "
            "este recuadro no convierte cada celda en un punto ni confirma una medición."
        ),
    )
    observed = IntervalSpan(
        kind="interval",
        start=start,
        end=end,
        bounds="start_inclusive_end_exclusive",
    )
    quality = Quality(
        flags=["metadata_only", "science_hdf_not_retrieved"],
        summary=(
            f"CMR informó time_end {entry['time_end']}. "
            f"El contrato guarda un fin exclusivo en {end.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')}. "
            "No se leyó el HDF, así que no hay valor de humedad ni unidad confirmada en el archivo científico. "
            f"granule_size de CMR: {entry.get('granule_size')} (megabytes según la documentación de CMR)."
        ),
    )
    provenance = Provenance(
        source_ids=["D02"],
        asset_ids=[f"asset-d02-{granule_id}"],
        collection_id="SPL3SMP_E",
        product_version=product_version,
        license_url=None,
        native_unit=None,
        retrieval="viability_sample",
        note=(
            "Metadatos públicos de un gránulo. El archivo científico sigue protegido por Earthdata. "
            f"Concepto de colección: {entry.get('collection_concept_id')}. "
            "variable_id V08 proviene del catálogo del producto, no de un valor leído."
        ),
    )
    return AssetRecord(
        schema_version="1.0",
        id=f"asset-d02-{granule_id}",
        data_mode="real",
        source_id="D02",
        collection_id="SPL3SMP_E",
        product_version=product_version,
        variable_id="V08",
        native_unit=None,
        spatial=spatial,
        observed=observed,
        issued_at=None,
        availability=AvailabilityUnknown(status="unknown"),
        ingested_at=ingested_at,
        quality=quality,
        checksum_sha256=checksum,
        byte_size=byte_size,
        original_locator=SAMPLE_DIR.joinpath("cmr-granule.json").as_posix(),
        science_file_retrieved=False,
        provenance=provenance,
    )


def load_smap_asset() -> AssetRecord:
    granule_path, retrieval_path = sample_paths()
    payload = json.loads(granule_path.read_text(encoding="utf-8"))
    retrieval = json.loads(retrieval_path.read_text(encoding="utf-8"))
    entries = payload["feed"]["entry"]
    if len(entries) != 1:
        raise ValueError("La muestra D02 debe contener un solo gránulo.")
    checksum = file_sha256(granule_path)
    if checksum != retrieval["sha256"]:
        raise ValueError("El SHA-256 de los metadatos CMR no coincide con la ficha de recuperación.")
    return build_smap_asset(
        entries[0],
        ingested_at=datetime.fromisoformat(str(retrieval["retrieved_at"]).replace("Z", "+00:00")),
        checksum=checksum,
        byte_size=granule_path.stat().st_size,
    )
