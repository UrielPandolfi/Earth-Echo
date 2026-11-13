"""Capas reales ya guardadas. No crea pines a partir de una malla."""

import json
from datetime import datetime, timezone

from earth_echo.contracts.types import ApiModel
from earth_echo.ingest.feeds import feeds_dir


class QuakeFeature(ApiModel):
    id: str
    longitude: float
    latitude: float
    depth_km: float | None
    magnitude: float
    magnitude_type: str | None = None
    review_status: str | None = None
    updated_at: str | None = None
    time: str
    place: str


class QuakeLayer(ApiModel):
    schema_version: str
    layer_id: str
    source_id: str
    geometry_kind: str
    unit: str
    retrieved_at: str | None
    count: int
    note: str
    features: list[QuakeFeature]


class KpLayer(ApiModel):
    schema_version: str
    layer_id: str
    source_id: str
    geometry_kind: str
    unit: str
    retrieved_at: str | None
    latest_time: str | None
    latest_kp: float | None
    count: int
    note: str


def _read(name: str) -> dict | None:
    path = feeds_dir() / f"{name}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def quake_layer() -> QuakeLayer:
    payload = _read("d21-events")
    if payload is None:
        return QuakeLayer(
            schema_version="1.0",
            layer_id="d21-events",
            source_id="D21",
            geometry_kind="points",
            unit="magnitud",
            retrieved_at=None,
            count=0,
            note="No hay una instantánea de sismos. No se usó el escenario DEMO.",
            features=[],
        )
    features = [QuakeFeature.model_validate(item) for item in payload.get("events", [])]
    return QuakeLayer(
        schema_version="1.0",
        layer_id="d21-events",
        source_id="D21",
        geometry_kind="points",
        unit="magnitud",
        retrieved_at=payload.get("retrieved_at"),
        count=len(features),
        note=str(payload.get("note") or ""),
        features=features,
    )


def kp_layer() -> KpLayer:
    payload = _read("d28-kp")
    rows = payload.get("rows", []) if payload else []
    latest = rows[-1] if rows else None
    return KpLayer(
        schema_version="1.0",
        layer_id="d28-kp",
        source_id="D28",
        geometry_kind="global_index",
        unit="Kp",
        retrieved_at=None if payload is None else payload.get("retrieved_at"),
        latest_time=None if latest is None else latest.get("time"),
        latest_kp=None if latest is None else latest.get("kp"),
        count=len(rows),
        note=(
            "No hay una instantánea de Kp. No se usó el escenario DEMO."
            if payload is None
            else str(payload.get("note") or "")
        ),
    )


def freshness_age_hours(retrieved_at: str | None, now: datetime | None = None) -> float | None:
    if not retrieved_at:
        return None
    moment = datetime.fromisoformat(retrieved_at.replace("Z", "+00:00"))
    current = now or datetime.now(timezone.utc)
    return (current - moment).total_seconds() / 3600
