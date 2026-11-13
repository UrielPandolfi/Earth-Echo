"""Normaliza la muestra local de USGS ComCat (D21) a un activo y una observación."""

import json
from datetime import datetime, timezone
from pathlib import Path

from earth_echo.contracts.geometry import GeographicExtent, GeoPoint, SpatialSupport, VerticalPosition
from earth_echo.contracts.records import (
    AssetRecord,
    AvailabilityUnknown,
    MissingValue,
    ObservationRecord,
    PresentValue,
    Provenance,
    Quality,
    InstantSpan,
)
from earth_echo.contracts.types import Sha256
from earth_echo.catalog.load import file_sha256
from earth_echo.paths import repo_root

SAMPLE_DIR = Path("data/samples/d21-usgs")
LICENSE_URL = "https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits"


def sample_paths() -> tuple[Path, Path]:
    root = repo_root()
    return root / SAMPLE_DIR / "event.geojson", root / SAMPLE_DIR / "retrieval.json"


def _instant(epoch_millis: int) -> datetime:
    return datetime.fromtimestamp(epoch_millis / 1000, tz=timezone.utc)


def build_usgs_records(
    feature: dict,
    *,
    product_version: str | None,
    ingested_at: datetime,
    checksum: Sha256,
    byte_size: int,
) -> tuple[AssetRecord, ObservationRecord]:
    geometry = feature["geometry"]
    if geometry.get("type") != "Point":
        raise ValueError("La muestra USGS esperada es un Point GeoJSON.")
    coordinates = [float(item) for item in geometry["coordinates"]]
    longitude, latitude = coordinates[0], coordinates[1]
    properties = feature["properties"]
    feature_id = str(feature["id"])
    asset_id = f"asset-d21-{feature_id}"
    magnitude = properties.get("mag")
    magnitude_type = properties.get("magType")
    if magnitude is None:
        measurement = MissingValue(status="missing")
        native_unit = None
    else:
        if magnitude_type in (None, ""):
            raise ValueError("Una magnitud presente necesita magType. No se asume una escala.")
        measurement = PresentValue(status="present", value=float(magnitude), unit=str(magnitude_type))
        native_unit = str(magnitude_type)
    vertical = None
    if len(coordinates) == 3:
        vertical = VerticalPosition(
            value=float(coordinates[2]),
            unit="km",
            datum="profundidad USGS del evento",
            direction="down",
        )
    spatial = SpatialSupport(
        role="observation_location",
        extent=GeographicExtent(
            west=longitude,
            south=latitude,
            east=longitude,
            north=latitude,
            crosses_antimeridian=False,
        ),
        geometry=GeoPoint(type="Point", coordinates=coordinates),
        vertical=vertical,
        resolution_note="Epicentro informado por USGS. La tercera coordenada es la profundidad, no una altura elipsoidal.",
    )
    observed = InstantSpan(kind="instant", start=_instant(int(properties["time"])))
    availability = AvailabilityUnknown(status="unknown")
    quality = Quality(
        flags=[
            f"usgs_status:{properties.get('status')}",
            f"usgs_pager_alert:{properties.get('alert')}",
            f"usgs_tsunami_flag:{properties.get('tsunami')}",
            "provider_fields_are_not_earth_echo_status",
        ],
        summary=(
            "La alerta PAGER y la bandera de tsunami son campos del proveedor. "
            "No son un estado de salud de Earth Echo ni un pronóstico. "
            "El campo updated no se usó como instante de disponibilidad."
        ),
    )
    provenance = Provenance(
        source_ids=["D21"],
        asset_ids=[asset_id],
        collection_id="usgs-fdsnws-event",
        product_version=product_version,
        license_url=LICENSE_URL,
        native_unit=native_unit,
        retrieval="viability_sample",
        note=(
            "Muestra pública de un evento con limit=1. "
            "No es una conexión operativa, no alimenta un fenómeno de humedad y no es un pronóstico."
        ),
    )
    asset = AssetRecord(
        schema_version="1.0",
        id=asset_id,
        data_mode="real",
        source_id="D21",
        collection_id="usgs-fdsnws-event",
        product_version=product_version,
        variable_id="V20",
        native_unit=native_unit,
        spatial=spatial,
        observed=observed,
        issued_at=None,
        availability=availability,
        ingested_at=ingested_at,
        quality=quality,
        checksum_sha256=checksum,
        byte_size=byte_size,
        original_locator=SAMPLE_DIR.joinpath("event.geojson").as_posix(),
        science_file_retrieved=True,
        provenance=provenance,
    )
    observation = ObservationRecord(
        schema_version="1.0",
        id=f"obs-d21-{feature_id}",
        data_mode="real",
        asset_id=asset_id,
        variable_id="V20",
        phenomenon_id=None,
        measurement=measurement,
        spatial=spatial,
        observed=observed,
        issued_at=None,
        availability=availability,
        ingested_at=ingested_at,
        quality=quality,
        product_version=product_version,
        provenance=provenance,
    )
    return asset, observation


def load_usgs_records() -> tuple[AssetRecord, ObservationRecord]:
    event_path, retrieval_path = sample_paths()
    payload = json.loads(event_path.read_text(encoding="utf-8"))
    retrieval = json.loads(retrieval_path.read_text(encoding="utf-8"))
    features = payload.get("features") or []
    if len(features) != 1:
        raise ValueError("La muestra D21 debe contener exactamente un evento.")
    checksum = file_sha256(event_path)
    if checksum != retrieval["sha256"]:
        raise ValueError("El SHA-256 del GeoJSON no coincide con la ficha de recuperación.")
    metadata = payload.get("metadata") or {}
    return build_usgs_records(
        features[0],
        product_version=str(metadata["api"]) if metadata.get("api") is not None else None,
        ingested_at=datetime.fromisoformat(str(retrieval["retrieved_at"]).replace("Z", "+00:00")),
        checksum=checksum,
        byte_size=event_path.stat().st_size,
    )


def load_usgs_observation() -> ObservationRecord:
    return load_usgs_records()[1]


def load_usgs_asset() -> AssetRecord:
    return load_usgs_records()[0]
