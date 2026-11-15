# Pronósticos consultables — entrega posterior al MVP descriptivo

## Recorrido implementado

REAL → **Pronósticos** abre una vista propia, sin atravesar Tendencias. D16 tiene selector de meses/corridas conservadas, campo continuo con leyenda0–100%, filtro de exploración y hasta20representantes de componentes. Seleccionar capa/mes/destacado conserva cámara. Clic sobre Tierra WGS84 consulta la celda científica, no un color; clic espacial no genera coordenada. Contorno de celda y marcador de selección; mes nuevo consulta la misma posición. Respuestas anteriores se cancelan/descartan. La selección (versión/posición/filtro/tipo) se conserva localmente al volver a abrir la vista.

Inspector: **Resumen / Datos / Método y fuente**. Probabilidad y soporte/período/proveedor/experimental visibles primero; CSV exacto, fechas UTC, referencia, SHA y original accesibles en detalles. La etiqueta de un destacado se refiere a su celda representante, no a probabilidad regional. Agrupación visual acotada al alejar, con representante sobre una celda válida. Cesium usa vecino próximo para textura; la celda centrada−180° se copia en dos medios píxeles de borde, sin inventar probabilidades o suavizado. API normaliza extensión mundial desde centros a[-180,180]. La vista conserva las181latitudes nativas: filas±90° con medias celdas polares recortadas; se copian valores al píxel, sin estirar todas las filas uniformemente.

**Corrección científica detectada durante la verificación:** el conector anterior omitía las filas±90° llamándolas enmascaradas.90°S esNaN, pero90°N contiene360probabilidades reales, variables por longitud de malla. Método`psl-nmme-range-cycle-v2-polar-support` conserva ambas. Las revisiones antiguas se consultan explícitamente como recortes89°N–89°S; no se inventan sus valores faltantes. La máscara sólo acreditaNaN/_FillValue, sin atribuir una causa como hielo a cada celda.

IFS permite consultar temperatura del aire, rapidez del viento a10m y precipitación acumulada del único plazo conservado, más archivos de corridas previas. Cada variable tiene su entrada/estado; no hay secuencia de15días ni umbral de desastre. Kp tiene tarjeta planetaria, serie y ventanas UTC, sin capa geográfica. D12/D14 y otros productos muestran estado temporal de su validez, incluso en el selector técnico. **Tendencias** y **Histórico** siguen disponibles.

## API y persistencia

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

## Demo mínima y reproducción

Con API/web iniciadas según README:

1. Abrir http://127.0.0.1:5173/ → REAL → Pronósticos. Producto **Calor marino · mensual**. La primera visita selecciona automáticamente el primer mes completo futuro; no hardcodea un mes.
2. Revisar el campo/leyenda y elegir un destacado o tocar el océano. Leer probabilidad de la celda, período, NOAA y límites. Encuadre sólo con el botón explícito. En ventanas pequeñas, **Filtros** y **Detalle** abren sus columnas.
3. Cambiar mes y verificar que conserva posición pero cambia la probabilidad/versión del campo. Un clic en una celda de máscara muestra **Sin cobertura en esta posición**. El filtro afecta destacados, no el campo ni el umbral científico. Si ningún componente coincide, se informa distinto de falta de datos; no se fuerzan pines.
4. Abrir Datos y descargar CSV, luego Método y fuente/original. Elegir **Meteorología · IFS +24h** y una variable/plazo real, después **Kp · planetario**. Los archivos vencidos están identificados.
5. Recargar/reiniciar API, volver a REAL/Pronósticos y verificar versión/posición guardadas. Una versión podada no se reemplaza silenciosamente: permite elegir otra disponible. Abrir Tendencias para el MVP descriptivo anterior.

```powershell
& './services/api/.venv/Scripts/python.exe' -m earth_echo.tools.verify_forecast_map --retain
```

Guarda `data/operational/forecast_map_evidence.json` sin consultar proveedores: coteja195.480posiciones de tres campos D16 completos (360×181cada uno), API/CSV/máscaras/representantes y descarga original exacta. Cada campo tiene43.867valores/21.293NaN. En la corrida octubre2026: noviembre/diciembre/enero en−67°,17°=0,8870967626571655/0,9435483813285828/0,9112903475761414. No son constantes de la interfaz ni pronósticos actuales perpetuos.

IFS en−67,5°,17,5°:29,067483520507835°C y5,774885849059489m/s para16/11/2026 00UTC;0,244140625mm en[15/11 00,16/11 00)UTC. Conversiones cotejadas con ecCodes/GRIB original; rapidez por norma de componentes. Se corrigió una etiqueta de referencia heredada del viento que mencionabaVPD; se republicó desde los mismos GRIB, sin descarga ni cambio de valores/modelo. SWPC tiene17ventanas16/11 00–18/11 03UTC en la instantánea comprobada; incluye ventanas iniciadas sin terminar si el proveedor las declara predicted. Las fechas cambian con las actualizaciones, no con este texto.

Se reinició el árbol real de la API y se comprobaron las identidades D16 retenidas con sus inicializaciones, emisiones desconocidas, recuperaciones, primeras capturas, períodos y SHA sin alteraciones: seis antes de la corrección polar y nueve en el cierre posterior, incluidas las tres nuevas revisiones. `--prior-catalog archivo.json` permite repetir la comparación con un catálogo guardado antes del reinicio. La revisión de derivados IFS usa el job existente; el scheduler conserva sus locks, reintentos, cadencias y presupuesto512MB.

El primer intento de actualización D16 encontró un bloqueo real de socket del sandbox; conservó el anterior REAL con estado de falla. La ejecución autorizada posterior se recuperó17:18:11–17:19:22UTC. El proveedor había cambiado el ETag del mismo ciclo octubre; se retuvo el nuevo subconjunto acotado, SHA`bf7711589cf1ede99698645a7b1c594e26a10ed16694e7f25cd9106568a9eeb1`, sin descargar toda la historia. Se añadió reutilización del archivo de rangos cuando coinciden ETag fuerte/tamaño: repetición17:20:51–17:20:56→unchanged, sin duplicar revisiones y conservando recuperación/procesamiento de la versión. No se convierte esa recuperación nueva en una emisión.

Regresión final:244API/60web, contratos y build aprobados.25pruebas API enfocadas y ocho de exploración frontend comprueban los límites/caché/polos, coordenadas fraccionales, cambio rápido de mes/respuesta vieja, cero/máscara, detalle/CSV y recorridos IFS/Kp sin geometría planetaria. Son pruebas de software/fidelidad, no habilidad científica.

**Revisión visual pendiente:** CUA y Computer Use por node_repl fallan al inicializar el kernel con `failed to write kernel assets: The system cannot find the path specified. (os error 3)`, también tras reset. Se investigó la alternativa disponible; no hay capturas nuevas1920×1080/ventana reducida ni se declara QA visual aprobada. Web/API siguen funcionando y las capturas anteriores no se presentan como evidencia de esta entrega.

## Mapa de capacidades y siguientes candidatos

| Capacidad | Estado y límite |
| --- | --- |
| D16/F18 | Adaptador probabilístico mensual; alcance oceánico y máscara nativos |
| D07 | Adaptador de campos ya retenidos; un plazo+24h, sin probabilidades de impacto |
| D28/F29 | Ventanas predicted planetarias de3h, incluidas las iniciadas sin terminar; sin mapa local |
| D22/F28 | Pronóstico OAF en REAL → Pronósticos. El mapa muestra el centro declarado; el radio 10 no trae unidad y no se dibuja. Un evento reciente, no el catálogo mundial |
| D09/D10 | Dos celdas regionales por producto, no cobertura mundial descargada |
| D12/D14 | Catálogo con estado temporal real; pueden estar vencidos, sin adaptador nuevo de esta entrega |
| RONI | Perspectivas estacionales existentes; no impactos locales |
| SST propio | Retrospectivo experimental; no supera persistencia, sin motor prospectivo nuevo |
| Earthdata | SMAP/GLDAS/IMERG reciente diferidos por el usuario; pasos en `docs/accesos.md` |

No se incorporaron proveedores ni credenciales nuevos, no se entrenó un modelo propio y no cambió el estado experimental de SST. Las referencias originales siguen intactas.
