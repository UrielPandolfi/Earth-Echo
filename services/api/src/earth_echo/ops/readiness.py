"""Archivos locales de consulta. No sondea proveedores ni declara el planeta sano."""

from pathlib import Path

from earth_echo.contracts.api_models import ReadyResponse, StoreCheck

REQUIRED_STORES = (
    ("Serie mensual de SST", "data/real/d15/monthly_series.json"),
    ("Índice del recorte D15", "data/real/d15/index.sqlite"),
    ("Sismos M>=5", "data/real/feeds/d21-events.json"),
    ("Kp observado", "data/real/feeds/d28-kp.json"),
    ("Kp previsto", "data/real/forecasts/d28-kp-forecast.json"),
)


def local_readiness(root: Path, assistant: str) -> ReadyResponse:
    stores = [
        StoreCheck(name=name, path=relative, present=(root / relative).is_file())
        for name, relative in REQUIRED_STORES
    ]
    complete = all(item.present for item in stores)
    return ReadyResponse(
        schema_version="1.0",
        process="ok",
        query_stores="ready" if complete else "incomplete",
        providers_updated="not_checked",
        assistant="configured" if assistant == "configured" else "unavailable",
        stores=stores,
        note=(
            "Listo para consultas significa que los archivos de esta entrega están en disco. "
            "No significa que los proveedores estén actualizados ni que los 31 fenómenos tengan datos."
        ),
    )
