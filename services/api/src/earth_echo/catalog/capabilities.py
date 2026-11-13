"""Matriz de capacidades. Un fenómeno no queda implementado por un solo booleano."""

from earth_echo.catalog.load import load_catalog
from earth_echo.contracts.types import ApiModel

OutputKind = str
OutputStatus = str


class OutputCapability(ApiModel):
    kind: str
    status: str
    detail: str


class PhenomenonCapability(ApiModel):
    id: str
    name: str
    family: str
    outputs: list[OutputCapability]


class CapabilityMatrix(ApiModel):
    schema_version: str
    total: int
    phenomena: list[PhenomenonCapability]


_OVERRIDES: dict[str, dict[str, tuple[str, str]]] = {
    "F01": {
        "observation": (
            "blocked",
            "IMERG (D01) pide EARTHDATA_USERNAME y EARTHDATA_PASSWORD. No hay lluvia observada conectada.",
        ),
        "forecast": ("specified", "No hay un pronóstico de lluvia conectado. La lluvia observada no es lluvia futura."),
    },
    "F02": {
        "observation": (
            "specified",
            "No hay temperatura del aire conectada. La SST del recorte no es una ola de calor.",
        )
    },
    "F11": {
        "observation": (
            "blocked",
            "SMAP (D02) pide credencial Earthdata. Una humedad baja no está medida y no prueba una sequía.",
        )
    },
    "F12": {
        "observation": (
            "blocked",
            "GloFAS está en CDS y no hay cuenta. Un caudal no se convirtió en profundidad de inundación.",
        )
    },
    "F15": {
        "indicator": (
            "specified",
            "GWIS quedó como portal. No hay un archivo numérico de FWI. El índice no es probabilidad de ignición.",
        )
    },
    "F19": {
        "observation": (
            "partial",
            "Hay SST de CoralTemp en el Caribe occidental. No hay HotSpot ni DHW, y no confirma blanqueamiento.",
        ),
        "trend": (
            "partial",
            "Hay una tendencia de la anomalía de SST en ese recorte. No es tendencia de daño biológico.",
        ),
        "forecast": ("specified", "El outlook de blanqueamiento no está conectado."),
    },
    "F28": {
        "observation": (
            "partial",
            "Hay sismos recientes de USGS con magnitud de al menos 5. No son probabilidades de réplica.",
        ),
        "forecast": ("specified", "El producto de réplicas D22 no está ingerido."),
    },
    "F29": {
        "observation": (
            "connected",
            "Hay índice Kp planetario de SWPC. Una señal solar no fija la intensidad geomagnética local.",
        ),
        "forecast": (
            "partial",
            "Hay un Kp previsto importado de SWPC, con emisión y validez. No está validado y no es un aviso local.",
        ),
    },
    "F31": {
        "observation": ("research", "No hay transporte de la AMOC conectado."),
        "trend": ("research", "Sin serie de transporte y sin cuenta regresiva de colapso."),
        "forecast": ("research", "No hay una fecha operativa de colapso."),
    },
}

_KINDS = ("observation", "indicator", "trend", "forecast")


def capability_matrix() -> CapabilityMatrix:
    phenomena = []
    for module in load_catalog().modules:
        outputs = []
        overrides = _OVERRIDES.get(module.id, {})
        for kind in _KINDS:
            status, detail = overrides.get(
                kind,
                (
                    "specified",
                    module.missing_or_local_data,
                ),
            )
            outputs.append(OutputCapability(kind=kind, status=status, detail=detail))
        phenomena.append(
            PhenomenonCapability(
                id=module.id,
                name=module.name,
                family=module.family,
                outputs=outputs,
            )
        )
    return CapabilityMatrix(schema_version="1.0", total=len(phenomena), phenomena=phenomena)
