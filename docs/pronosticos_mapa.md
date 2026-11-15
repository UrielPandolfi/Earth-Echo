# Pronósticos consultables — entrega posterior al MVP descriptivo

## Alcance implementado en backend

El adaptador `queries/predictions.py` consulta productos locales ya calificados. No descarga por clic, no calcula probabilidades nuevas y no modifica `validated_for_use`. Usa un contrato nuevo Pydantic `contracts/predictions.py`: el antiguo `ForecastRecord` exige inicialización/emisión conocidas y una ventana, incompatibles con proveedores honestamente incompletos e instantes IFS. Los experimentos anteriores conservan sus contratos y resultados.

- Catálogo, corridas y períodos retenidos: `GET /v1/forecasts/catalog`.
- Campo de una versión: `GET /v1/forecasts/fields/{id}`.
- Consulta de la misma versión: `.../{id}/point?longitude=-67&latitude=17`; exportación exacta `.../{id}/point.csv`.
- Destacados: `.../{id}/highlights?probability_filter=0.7&limit=20`.
- Original exacto: `.../{id}/original`. No sustituye una versión retirada por la nueva.
- Kp tipado: `GET /v1/forecasts/planetary/d28-kp`; el endpoint anterior sigue disponible.

ID local SHA256 de fuente/colección/variable/inicialización/período/método/malla/contenido/SHA original/versión del adaptador. Excluye el slot rotatorio `month-1/2/3`, recuperación y procesamiento. No es ID oficial NOAA. Las revisiones existentes y su activo compartido permiten reconstruirlo tras reiniciar; se respeta su retención de cuatro revisiones y presupuesto512MB, sin duplicar campos. Si una revisión se poda se informa entrada ausente. `first_seen_at` es la mínima `ingested_at` de esa identidad en las revisiones retenidas, nunca publicación. Emisión/inicialización desconocidas permanecen null.

## Definición D16/F18

NOAA PSL/NMME `NMME_prob90_latest.nc`, **con tendencia retenida**. Probabilidad [0,1] de anomalía SST media mensual sobre el p90 específico del mes calculado con anomalías de una ventana de tres meses, referencia1991–2020. Producto externo experimental para investigación. No representa un episodio diario de cinco días, daño coralino, mortalidad ni temperatura del aire. Fuente primaria: [NOAA PSL](https://psl.noaa.gov/marine-heatwaves/). No se integraron mapas de habilidad SEDI; la probabilidad no implica confianza o habilidad local.

El filtro≥70% es sólo exploratorio, independiente del p90 científico. Destacados: componentes de cuatro vecinos por lados, unión cíclica de longitud sólo en malla mundial; no cruza máscara/tierra/huecos. Representante máximo p y empate fila norte→sur/columna oeste→este. Orden máximo p descendente, cantidad de celdas descendente e índice representante ascendente; límite aplicado después. Rango y número de celdas no son probabilidad regional. Sin envolventes o polígonos aproximados.

Celda contenedora por puntos medios de centros; oeste/sur incluidos, este/norte excluidos salvo90°N. Empates este/norte. Longitud normalizada[-180,180); celda centrada−180° partida en dos polígonos. No busca otro vecino válido. NaN nativo permanece null; probabilidad cero válida. D16 conserva1° nativo. IFS consulta nodos ya seleccionados en la vista1° desde GRIB0,25°: soporte entre centros de visualización, no media de área ni precisión costera. No interpreta el píxel de color como valor científico.

Mensual:[inicio,fin) civil UTC. Selección inicial: primer mes completo futuro, corrida más reciente retenida para ese mes. Puede haber mes en curso o archivos vencidos explícitos. Instantes vencen al pasar su hora; acumulados conservan su intervalo. La recuperación reciente no rejuvenece una corrida. Fallas del scheduler existente se muestran conservando producto REAL. Estados distinguibles: available, no_coverage, missing_input, expired, not_implemented; vencido puede conservar el valor consultable archivado.

## Comprobación científica y habilidad pendiente

Fixture auténtica en `data/samples/forecast-map`, probes h5py/struct independientes y pruebas de máscara, orientación, cero, unidades/probabilidad, bordes, antimeridiano, calendario, identidad/reinicio, contador y conservación del válido ante falla. Son comprobaciones de integración, no de habilidad.

Para Brier/calibración prospectivos hacen falta emisiones archivadas antes del período objetivo y SST mensual/umbral del proveedor con referencia1991–2020, la misma convención de tendencia y malla. OISST `anom`1971–2000 y la referencia regional2014–2021 no sustituyen esa verdad equivalente. No se calcularon esas métricas ni se usaron los nueve candidatos regionales históricos como validación mundial.

## Siguientes candidatos

| Capacidad | Estado y límite |
| --- | --- |
| D16/F18 | Adaptador probabilístico mensual; alcance oceánico y máscara nativos |
| D07 | Adaptador de campos ya retenidos; un plazo+24h, sin probabilidades de impacto |
| D28/F29 | Ventanas predicted planetarias de3h, incluidas las iniciadas sin terminar; sin mapa local |
| D22/F28 | Tabla OAF retenida; falta calificar unidad de radio/soporte publicado y verificación por magnitud/ventana. No nuevos epicentros |
| D09/D10 | Dos celdas regionales por producto, no cobertura mundial descargada |
| D12/D14 | Catálogo con estado temporal real; pueden estar vencidos, sin adaptador nuevo de esta entrega |
| RONI | Perspectivas estacionales existentes; no impactos locales |
| SST propio | Retrospectivo experimental; no supera persistencia, sin motor prospectivo nuevo |
| Earthdata | SMAP/GLDAS/IMERG reciente diferidos por el usuario; pasos en `docs/accesos.md` |

La revisión visual y el guion de interfaz se registran al cerrar el recorrido; no se declaran aprobados por pasar pruebas numéricas.
