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

_KINDS = ("observation", "indicator", "trend", "forecast", "experimental_model")


def capability_matrix() -> CapabilityMatrix:
    from earth_echo.storage.products import all_products
    products = all_products()
    available = {p.id for p in products}
    overrides_by_id = {key:dict(value) for key,value in _OVERRIDES.items()}
    if 'd15-sst-global' in available:
        overrides_by_id['F19']['observation'] = ('partial','SST CoralTemp de cobertura oceánica mundial submuestreada a 1°. La SST no confirma blanqueamiento; historia y tendencia solo en el recorte del Caribe.')
    if {'d15-dhw-global','d15-hotspot-global'} <= available:
        overrides_by_id['F19']['indicator'] = ('partial','HotSpot y DHW numéricos importados de NOAA con máscara. Indicadores de estrés térmico observado, sin daño biológico confirmado.')
    if any(p.source_id=='D04' for p in products):
        overrides_by_id.setdefault('F16',{})['observation'] = ('partial','NDVI/EVI MODIS en subconjuntos de Pampa/Amazonía, con QA y compuesto de 16 días. No mide rendimiento ni identifica causa del estrés.')
    if any(p.source_id=='D05' for p in products):
        overrides_by_id.setdefault('F02',{})['observation'] = ('partial','MODIS LST diurna/nocturna en subconjuntos locales. Es temperatura superficial de cielo despejado; sigue faltando una observación de temperatura del aire para detectar olas de calor.')
    if 'd07-ifs-2t-24h' in available:
        for fid in ['F02','F03']:
            overrides_by_id.setdefault(fid,{})['forecast'] = ('partial','IFS externo mundial de temperatura del aire a 2 m, plazo +24 h; no es un detector de ola de calor/frío ni de helada agrícola.')
    if 'd07-ifs-tp-24h' in available:
        overrides_by_id['F01']['forecast'] = ('partial','Precipitación determinista IFS acumulada 0–24 h, mundial, m convertidos a mm. Sin percentiles de extremo ni probabilidad calibrada.')
    overrides_by_id.setdefault('F19',{})['experimental_model'] = ('experimental','Experimento de anomalía mensual SST del Caribe, sin habilidad adicional frente a persistencia. No pronostica daño de coral.')
    if 'd13-oisst-global' in available:
        overrides_by_id.setdefault('F18',{})['observation'] = ('partial','SST diaria mundial OISST v2.1, preliminar; sin climatología diaria y duración no se diagnostica una ola de calor marina.')
    if 'd48-oni-history' in available:
        overrides_by_id.setdefault('F17',{})['indicator'] = ('partial','Historia ONI de CPC, media móvil de tres meses en Niño 3.4. No es diagnóstico operativo de fase ni pronóstico local; no se sustituye RONI.')
    if 'd23-holocene-inventory' in available:
        overrides_by_id.setdefault('F24',{})['observation'] = ('partial','Inventario geográfico GVP del Holoceno: contexto estático. No hay precursores ni predicción de erupciones.')
    if 'd27-tsunami-messages' in available:
        overrides_by_id.setdefault('F27',{})['observation'] = ('partial','Mensajes Atom/CAP de NTWC/PTWC con emisor, cancelación, vigencia y ámbito originales. No cubren todos los centros ni se infiere llegada desde el epicentro.')
    if 'd22-oaf-recent' in available:
        overrides_by_id['F28']['forecast'] = ('partial','OAF oficial de USGS para un evento reciente con producto publicado: probabilidades por magnitud y ventana, modelo/región definidos. Sin hora/lugar garantizados de la réplica.')
    if 'd29-sentry' in available:
        overrides_by_id.setdefault('F30',{})['forecast'] = ('partial','Evaluación orbital Sentry para objetos conocidos, con probabilidad acumulada y años de posibles impactos. No fecha/lugar terrestre ni cobertura de objetos no descubiertos.')
    phenomena = []
    for module in load_catalog().modules:
        outputs = []
        overrides = overrides_by_id.get(module.id, {})
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
