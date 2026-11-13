"""Lectores de USGS y SWPC. No pronostican réplicas ni tormentas."""

import json
from datetime import datetime, timezone
from typing import Any

USGS_QUERY = (
    "https://earthquake.usgs.gov/fdsnws/event/1/query"
    "?format=geojson&minmagnitude=5&limit=20&orderby=time"
)
SWPC_KP_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"


class FeedSchemaError(ValueError):
    pass


def parse_usgs_events(payload: dict[str, Any]) -> list[dict[str, Any]]:
    features = payload.get("features")
    if not isinstance(features, list):
        raise FeedSchemaError("El GeoJSON de USGS no trae features.")
    events = []
    for feature in features:
        if not isinstance(feature, dict):
            raise FeedSchemaError("Una feature de USGS no es un objeto.")
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates")
        properties = feature.get("properties") or {}
        if not isinstance(coordinates, list) or len(coordinates) < 2:
            raise FeedSchemaError("Un sismo no tiene longitud y latitud.")
        magnitude = properties.get("mag")
        if not isinstance(magnitude, (int, float)):
            raise FeedSchemaError("Un sismo no tiene magnitud numérica.")
        epoch_ms = properties.get("time")
        if not isinstance(epoch_ms, (int, float)):
            raise FeedSchemaError("Un sismo no tiene hora.")
        moment = datetime.fromtimestamp(epoch_ms / 1000, timezone.utc).replace(microsecond=0)
        depth = coordinates[2] if len(coordinates) > 2 and isinstance(coordinates[2], (int, float)) else None
        events.append(
            {
                "id": str(feature.get("id") or ""),
                "longitude": float(coordinates[0]),
                "latitude": float(coordinates[1]),
                "depth_km": None if depth is None else float(depth),
                "magnitude": float(magnitude),
                "time": moment.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "place": str(properties.get("place") or ""),
            }
        )
        if not events[-1]["id"]:
            raise FeedSchemaError("Un sismo no tiene identificador.")
    return events


def parse_planetary_kp(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, list) or not payload or not isinstance(payload[0], dict):
        raise FeedSchemaError("El Kp de SWPC no tiene el esquema de objetos esperado.")
    rows = []
    for item in payload:
        if "Kp" not in item or "time_tag" not in item:
            raise FeedSchemaError("Falta Kp o time_tag.")
        value = item["Kp"]
        if not isinstance(value, (int, float)):
            raise FeedSchemaError("Kp no es numérico.")
        rows.append(
            {
                "time": str(item["time_tag"]).replace(" ", "T"),
                "kp": float(value),
                "station_count": item.get("station_count") if isinstance(item.get("station_count"), int) else None,
            }
        )
    return rows


def loads_json(raw: bytes) -> Any:
    if raw.lstrip()[:1] in {b"<", b""}:
        raise FeedSchemaError("La respuesta parece HTML, no JSON.")
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as error:
        raise FeedSchemaError("El JSON no se pudo leer.") from error
