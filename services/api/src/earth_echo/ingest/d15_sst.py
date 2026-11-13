"""Ingestión idempotente del subconjunto CoralTemp. No corre dentro de una petición."""

import shutil
from datetime import datetime, timezone
from pathlib import Path

from earth_echo.catalog.load import file_sha256
from earth_echo.connectors.crw_sst import (
    DATASET_ID,
    DISCOVERY_URL,
    PRODUCT_VERSION,
    SOURCE_PAGE,
    logical_asset_key,
    decode_subset,
)
from earth_echo.contracts.geometry import GeographicExtent, GeoPoint, SpatialSupport
from earth_echo.contracts.records import (
    AssetRecord,
    AvailabilityUnknown,
    InstantSpan,
    ObservationRecord,
    PresentValue,
    MissingValue,
    Provenance,
    Quality,
)
from earth_echo.paths import repo_root
from earth_echo.storage.sst_store import SstStore

SAMPLE_RELATIVE = "data/samples/d15-crw/coraltemp-v3.1-caribe-20261108-20261111.nc"
STORE_RELATIVE = "data/real/d15"


def sample_file() -> Path:
    return repo_root() / SAMPLE_RELATIVE


def default_store() -> SstStore:
    return SstStore(repo_root() / STORE_RELATIVE)


def ingest_file(source: Path, store: SstStore, *, ingested_at: datetime | None = None) -> dict[str, int | str]:
    decoded = decode_subset(source)
    checksum = file_sha256(source)
    moment = ingested_at or datetime.now(timezone.utc)
    logical_key = logical_asset_key()
    existing = store.latest_asset(logical_key)
    if existing is not None and str(existing["checksum"]) == checksum:
        return {"status": "unchanged", "revision": int(existing["revision"]), "observations": _current_count(store)}
    revision = 1 if existing is None else int(existing["revision"]) + 1
    asset_id = f"d15-coraltemp-v3.1-caribe-r{revision}"
    relative = f"assets/{checksum}.nc"
    target = store.root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.is_file():
        shutil.copyfile(source, target)
    west = float(decoded["west"])
    south = float(decoded["south"])
    east = float(decoded["east"])
    north = float(decoded["north"])
    extent = GeographicExtent(
        west=west,
        south=south,
        east=east,
        north=north,
        crosses_antimeridian=False,
    )
    asset = AssetRecord(
        schema_version="1.0",
        id=asset_id,
        data_mode="real",
        source_id="D15",
        collection_id=DATASET_ID,
        product_version=PRODUCT_VERSION,
        variable_id="V15",
        native_unit="degree_C",
        spatial=SpatialSupport(
            role="gridded_product",
            grid_id="CoralTemp-v3.1-0.05deg",
            extent=extent,
            resolution_note=(
                "Celdas de 0,05 grados del recorte. Una celda no es una medición puntual. "
                "El archivo guardado es el subconjunto de ERDDAP, no el NetCDF global."
            ),
        ),
        observed=InstantSpan(kind="instant", start=_first_time(decoded)),
        issued_at=None,
        availability=AvailabilityUnknown(status="unknown"),
        ingested_at=moment,
        quality=Quality(
            flags=["daily_analysis", "gap_free_product"],
            summary="CoralTemp v3.1, SST analizada en degree_C. No incluye HotSpot, DHW ni daño biológico.",
        ),
        checksum_sha256=checksum,
        byte_size=source.stat().st_size,
        original_locator=relative,
        science_file_retrieved=True,
        provenance=Provenance(
            source_ids=["D15"],
            collection_id=DATASET_ID,
            product_version=PRODUCT_VERSION,
            license_url=SOURCE_PAGE,
            native_unit="degree_C",
            retrieval="live",
            note=f"Descubrimiento en {DISCOVERY_URL}. Unidad canónica °C, sin factor de escala en este subconjunto.",
        ),
    )
    observations = []
    days = decoded["days"]
    if not isinstance(days, list):
        raise RuntimeError("La decodificación no trajo días.")
    for day in days:
        if not isinstance(day, dict):
            continue
        observations.append(_observation_from_day(day, asset_id, revision, moment, extent))
    store.add_revision(
        asset=asset,
        logical_key=logical_key,
        revision=revision,
        relative_path=relative,
        observations=[(item[0], item[1], item[2]) for item in observations],
    )
    return {"status": "stored", "revision": revision, "observations": len(observations)}


def _first_time(decoded: dict[str, object]) -> datetime:
    days = decoded["days"]
    if not isinstance(days, list) or not days or not isinstance(days[0], dict):
        raise RuntimeError("El subconjunto no tiene tiempos.")
    moment = days[0]["time"]
    if not isinstance(moment, datetime):
        raise RuntimeError("El tiempo decodificado no es una fecha.")
    return moment


def _observation_from_day(
    day: dict[str, object],
    asset_id: str,
    revision: int,
    ingested_at: datetime,
    extent: GeographicExtent,
) -> tuple[str, str, ObservationRecord]:
    moment = day["time"]
    if not isinstance(moment, datetime):
        raise RuntimeError("Falta el tiempo de la observación.")
    stamp = moment.strftime("%Y%m%dT%H%M%SZ")
    observation_id = f"d15-sst-{stamp}-r{revision}"
    logical = f"{logical_asset_key()}|{stamp}|r{revision}"
    mean = day["mean"]
    valid_count = int(day["valid_count"])
    missing_count = int(day["missing_count"])
    measurement: PresentValue | MissingValue
    if isinstance(mean, float):
        measurement = PresentValue(status="present", value=round(mean, 4), unit="°C")
    else:
        measurement = MissingValue(status="missing")
    record = ObservationRecord(
        schema_version="1.0",
        id=observation_id,
        data_mode="real",
        asset_id=asset_id,
        variable_id="V15",
        phenomenon_id=None,
        measurement=measurement,
        spatial=SpatialSupport(
            role="region_anchor",
            region_id="caribe-occidental",
            extent=extent,
            geometry=GeoPoint(type="Point", coordinates=[round((extent.west + extent.east) / 2, 4), round((extent.south + extent.north) / 2, 4)]),
            resolution_note=(
                f"Promedio aritmético de {valid_count} celdas válidas. "
                f"{missing_count} celdas quedaron fuera por relleno o por fuera del rango. "
                "No es una medición en el centro del recorte."
            ),
        ),
        observed=InstantSpan(kind="instant", start=moment),
        issued_at=None,
        availability=AvailabilityUnknown(status="unknown"),
        ingested_at=ingested_at,
        quality=Quality(
            flags=["regional_mean", "fill_excluded"],
            summary=(
                "SST superficial del mar de CoralTemp v3.1. "
                "No es anomalía, no es HotSpot y no confirma blanqueamiento."
            ),
        ),
        product_version=PRODUCT_VERSION,
        provenance=Provenance(
            source_ids=["D15"],
            asset_ids=[asset_id],
            collection_id=DATASET_ID,
            product_version=PRODUCT_VERSION,
            native_unit="degree_C",
            retrieval="live",
            note="La unidad canónica es °C. Este subconjunto no trae scale_factor.",
        ),
    )
    return logical, moment.strftime("%Y-%m-%dT%H:%M:%SZ"), record


def _current_count(store: SstStore) -> int:
    return len(store.current_observations())
