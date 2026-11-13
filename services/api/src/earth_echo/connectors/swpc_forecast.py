"""Pronóstico importado de Kp. No lo convierte en probabilidad ni en aviso local."""

from datetime import datetime, timedelta
from typing import Any

from earth_echo.connectors.public_feeds import FeedSchemaError

KP_FORECAST_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json"
VALIDITY_HOURS = 3


def parse_predicted_kp(payload: Any, issued_at: datetime) -> list[dict[str, object]]:
    if not isinstance(payload, list) or not payload or not isinstance(payload[0], dict):
        raise FeedSchemaError("El pronóstico de Kp no tiene el esquema esperado.")
    steps = []
    for item in payload:
        if item.get("observed") != "predicted":
            continue
        if "kp" not in item or "time_tag" not in item:
            raise FeedSchemaError("Una fila prevista no tiene kp o time_tag.")
        if not isinstance(item["kp"], (int, float)) or not 0 <= item['kp'] <= 9:
            raise FeedSchemaError("El Kp previsto no es numérico.")
        start = datetime.fromisoformat(str(item["time_tag"]))
        if start.tzinfo is None:
            start = start.replace(tzinfo=issued_at.tzinfo)
        if start < issued_at:
            continue
        end = start + timedelta(hours=VALIDITY_HOURS)
        lead = (start - issued_at).total_seconds() / 3600
        steps.append(
            {
                "valid_start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "valid_end": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "lead_time_hours": lead,
                "kp": float(item["kp"]),
            }
        )
    if not steps:
        raise FeedSchemaError("El archivo no trae filas predicted posteriores a la emisión.")
    return steps
