"""Consulta del subconjunto real ya ingerido. No llama al proveedor."""

from datetime import datetime, timedelta, timezone
from typing import Literal

from earth_echo.connectors.crw_sst import PRODUCT_VERSION, decode_subset
from earth_echo.contracts.geometry import GeographicExtent
from earth_echo.contracts.records import ObservationRecord
from earth_echo.contracts.types import ApiModel, UnavailableReason, UtcDateTime
from earth_echo.ingest.d15_sst import default_store
from earth_echo.storage.sst_store import SstStore

Freshness = Literal["within_cadence", "recent_archive", "historical"]


class SstField(ApiModel):
    schema_version: Literal["1.0"]
    observation_id: str
    unit: Literal["°C"]
    width: int
    height: int
    west: float
    south: float
    east: float
    north: float
    minimum: float | None
    maximum: float | None
    missing_cells: int
    values: list[float | None]


class RealSourceView(ApiModel):
    schema_version: Literal["1.0"]
    source_id: Literal["D01", "D15"]
    data_mode: Literal["real"]
    status: Literal["available", "unavailable"]
    reason_code: UnavailableReason | None = None
    reason: str | None = None
    collection_id: str | None = None
    product_version: str | None = None
    cadence: str | None = None
    freshness: Freshness | None = None
    latest_observation: UtcDateTime | None = None
    latest_ingest: UtcDateTime | None = None
    checksum_sha256: str | None = None
    byte_size: int | None = None
    asset_id: str | None = None
    coverage: GeographicExtent | None = None
    observations: list[ObservationRecord] = []


def freshness_for(observed: datetime, now: datetime) -> Freshness:
    age = now - observed
    if age <= timedelta(hours=36):
        return "within_cadence"
    if age <= timedelta(days=7):
        return "recent_archive"
    return "historical"


def d01_blocked() -> RealSourceView:
    return RealSourceView(
        schema_version="1.0",
        source_id="D01",
        data_mode="real",
        status="unavailable",
        reason_code="credential_required",
        reason=(
            "IMERG Early (GPM_3IMERGHHE, versión 07) pide Earthdata o PPS. "
            "Definí EARTHDATA_USERNAME y EARTHDATA_PASSWORD en el archivo .env de la raíz. "
            "Esta consulta no se completó con DEMO ni con Coral Reef Watch."
        ),
        collection_id="GPM_3IMERGHHE",
        product_version="07",
        cadence="30 minutos",
    )


def d15_view(store: SstStore | None = None, now: datetime | None = None) -> RealSourceView:
    active = store or default_store()
    if not active.database.is_file():
        return RealSourceView(
            schema_version="1.0",
            source_id="D15",
            data_mode="real",
            status="unavailable",
            reason_code="insufficient_data",
            reason="No hay una ingestión local de CoralTemp. Ejecutá la ingestión del subconjunto archivado.",
            collection_id="noaacrwsstDaily",
            product_version=PRODUCT_VERSION,
            cadence="1 día",
        )
    observations = active.current_observations()
    if not observations:
        return RealSourceView(
            schema_version="1.0",
            source_id="D15",
            data_mode="real",
            status="unavailable",
            reason_code="insufficient_data",
            reason="La ingestión no dejó observaciones vigentes.",
            collection_id="noaacrwsstDaily",
            product_version=PRODUCT_VERSION,
            cadence="1 día",
        )
    latest = observations[-1]
    asset = active.asset(latest.asset_id)
    moment = now or datetime.now(timezone.utc)
    return RealSourceView(
        schema_version="1.0",
        source_id="D15",
        data_mode="real",
        status="available",
        collection_id="noaacrwsstDaily",
        product_version=PRODUCT_VERSION,
        cadence="1 día",
        freshness=freshness_for(latest.observed.start, moment),
        latest_observation=latest.observed.start,
        latest_ingest=latest.ingested_at,
        checksum_sha256=asset.checksum_sha256 if asset else None,
        byte_size=asset.byte_size if asset else None,
        asset_id=latest.asset_id,
        coverage=latest.spatial.extent,
        observations=observations,
    )


def d15_field(observation_id: str, store: SstStore | None = None) -> SstField | None:
    active = store or default_store()
    if not active.database.is_file():
        return None
    record = active.observation(observation_id)
    if record is None or record.observed.kind != "instant":
        return None
    path = active.asset_path(record.asset_id)
    if path is None or not path.is_file():
        return None
    decoded = decode_subset(path)
    days = decoded["days"]
    if not isinstance(days, list):
        return None
    day = next(
        (
            item
            for item in days
            if isinstance(item, dict)
            and isinstance(item.get("time"), datetime)
            and abs((item["time"] - record.observed.start).total_seconds()) < 1
        ),
        None,
    )
    if not isinstance(day, dict):
        return None
    values = day["values"]
    width = int(decoded["width"])
    height = int(decoded["height"])
    if not isinstance(values, list) or len(values) != width * height:
        return None
    north_first: list[float | None] = []
    for row in range(height - 1, -1, -1):
        north_first.extend(values[row * width : (row + 1) * width])
    present = [item for item in north_first if isinstance(item, float)]
    return SstField(
        schema_version="1.0",
        observation_id=record.id,
        unit="°C",
        width=width,
        height=height,
        west=float(decoded["west"]),
        south=float(decoded["south"]),
        east=float(decoded["east"]),
        north=float(decoded["north"]),
        minimum=min(present) if present else None,
        maximum=max(present) if present else None,
        missing_cells=int(day["missing_count"]),
        values=north_first,
    )
