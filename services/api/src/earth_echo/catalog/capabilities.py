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
            "GloFAS requiere acceso EWDS/CEMS y licencia del producto. Un caudal no se convirtió en profundidad de inundación.",
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
            "Hay sismos USGS de consulta acotada, con ventana/umbral/límite en la query conservada y revisión/magnitud nativas. No son probabilidades de réplica.",
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
            "Hay Kp previsto importado de SWPC, con validez de tres horas y recuperación separada. El feed no publica emisión/inicialización: permanecen null. No es un aviso local ni modelo validado.",
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
    if 'd24-lhasa-bc' in available:
        overrides_by_id.setdefault('F25',{})['indicator'] = ('partial','Nowcast LHASA p_landslide de Columbia Británica, malla nativa de ~1 km, versión de archivo trazable. No es deslizamiento observado ni falla garantizada de una ladera.')
    if any(p.source_id=='D16' for p in products):
        overrides_by_id.setdefault('F18',{})['forecast'] = ('partial','Probabilidades mensuales NMME de NOAA PSL sobre umbral p90, producto externo experimental con tendencia retenida y ventanas mensuales. Habilidad desigual; sin daño biológico confirmado.')
    if 'd47-cyclone-tracks' in available:
        overrides_by_id.setdefault('F06',{})['observation'] = ('partial','Trayectorias históricas/provisionales IBTrACS de sistemas con posición en los últimos 30 días. Conservan agencia, viento nativo y calidad. No hay trayectoria futura ni validación de forecasts emitidos.')
    if 'd35-cyclone-cap-areas' in available:
        overrides_by_id.setdefault('F06',{})['indicator'] = ('partial','Mensajes/áreas CAP de ciclón GDACS, incluidos estados pasados y cancelaciones. Puntaje importado, no probabilidad ni detector propio; vigencia por mensaje.')
    if any(p.source_id=='D20' for p in products):
        overrides_by_id.setdefault('F16',{})['indicator'] = ('partial','ASI FAO numérico nativo de Pampa, Cropland/Season 1: porcentaje agrícola afectado desde inicio del ciclo. Códigos especiales enmascarados; no probabilidad ni rendimiento. Vista mundial gruesa rechazada por discrepancia con píxel nativo.')
    if 'd19-desert-locust-surveys' in available:
        overrides_by_id.setdefault('F23',{})['observation'] = ('partial','Reportes RAMSES públicos de langosta del desierto, incluidos muestreos de ausencia. Consulta reciente acotada, muestra actual de Mauritania. Sin traslado a Sudamérica, número de individuos o pronóstico de migración.')
    if 'd07-ifs-wind10-24h' in available:
        overrides_by_id.setdefault('F04',{})['indicator'] = ('partial','Magnitud del viento a 10 m calculada de u/v IFS +24 h, mundial a 1°, con fórmula e insumos trazables. No aporta CAPE, cizalladura ni detección/pronóstico de tormentas o granizo.')
    if 'd07-ifs-vpd-24h' in available:
        overrides_by_id.setdefault('F15',{})['indicator'] = ('partial','VPD instantáneo sobre agua líquida calculado de T/Td IFS +24 h en dominio conservador 0–50 °C. Variable meteorológica de entorno; no FWI, humedad de combustible ni probabilidad de ignición. GWIS numérico sigue pendiente.')
    if 'd06-viirs-noaa20-sa' in available:
        overrides_by_id.setdefault('F15',{})['observation'] = ('partial','Detecciones térmicas VIIRS NOAA-20 C2 en Sudamérica, con FRP MW, tiempos UTC y calidad nativa. Low permanece en tabla y se excluye del mapa. Puede incluir volcanes/antorchas; no incendios únicos, área quemada ni probabilidad de ignición.')
    if 'd23-weekly-activity-reports' in available:
        edition=next(p for p in products if p.id=='d23-weekly-activity-reports')
        overrides_by_id.setdefault('F24',{})['observation'] = ('partial',f'Inventario GVP y reportes preliminares de actividad geolocalizados, cotejados RSS/CAP. Emisión del archivo {edition.issued_at.isoformat()}; puede estar atrasado, sin acreditar actividad mundial actual ni vigilancia instrumental continua. Categorías publicadas, sin fecha/probabilidad de erupción próxima.')
    if 'd26-rgi7-alaska-attributes' in available:
        overrides_by_id.setdefault('F26',{})['observation'] = ('blocked','Hay contexto RGI7 de áreas y puntos representativos nativos en una muestra de Alaska. No se descargaron huellas ni observaciones de lagunas, diques o vaciamientos; ese inventario no habilita observación/predicción GLOF.')
    if 'd34-amoc-monthly' in available:
        overrides_by_id.setdefault('F31',{})['observation'] = ('partial','Serie observacional procesada RAPID v2024-2, 248 medias mensuales abril 2004–noviembre 2024 en 26,5° N, con transporte AMOC/calor/agua dulce. No observación mundial o actual ni fecha de colapso; tendencia/inferencia científica siguen separadas.')
    if 'd25-s3a-chlorophyll' in available:
        overrides_by_id.setdefault('F20',{})['observation'] = ('partial','Clorofila OC4Me L3 Sentinel-3A vía NOAA, producto experimental con huecos y fechas reales. Fuente Copernicus, no sustituye OceanColor NASA D17. No confirma especie de alga, toxicidad ni un evento HAB; no hay detector o pronóstico biológico.')
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
