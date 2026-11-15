# Progreso

## Estado actual — 15 noviembre 2026, incrementos 11A–11AT

- 33IDs del catálogo con productos científicos reales para alcances explícitos;83productos,54campos (seis calculados), tres productos de indicadores calculados. MVP: anomalía diaria mundial OISST importada/base1971–2000, anomalías SST históricas por referencia congelada (9candidatos/48meses), tendencia estacional v2 con intervalos/sensibilidad y dos asociaciones exploratorias ENSO/SST y AMOC/SST. SEAS5/GloFAS/CAMS/Marine conservan sus alcances propios. No son31detectores ni cobertura mundial de todos los fenómenos. D01 sólo climatología y D17 archivo2022; ramas recientes pendientes.
- Última consulta verificada:14.885registros de observación,3.370históricos, dos registros de indicadores importados y cero señales de evento calculadas. Los lotes recientes y conteos se actualizan; contexto estático y celdas no suman observaciones. Evidencia reproducible en `data/operational/integration_evidence.json`.
- Tarea Windows de actualización activa; cadencias y recuperación en [docs/actualizacion.md](docs/actualizacion.md). Límite de almacén512MB: cuatro revisiones por producto, dos para SMOC y24para tablas de pronóstico CPC. Derivados se activan al cambiar entradas persistidas, con recuperación y backoff. Lock del hijo y plazo independiente sobreviven a muerte del lanzador. Conserva el último válido ante falla, sin salir de REAL.
- 235pruebas API/51web, contratos/TypeScript/build aprobados. Verificación nativa/SVD/API/CSV/asistente del núcleo en`data/operational/mvp_scientific_evidence.json`; métodos, límites y recorrido demostrable en`docs/mvp_cientifico.md`. Referencias originales intactas. Capturas REAL anteriores en`docs/integraciones/`; capturas nuevas del núcleo pendientes por fallo de inicialización del controlador del navegador, sin declarar QA visual aprobada. Tests de procesos reales terminan sólo sus propios hijos controlados.
- Restan cinco fuentes de datos sin primera integración: D02/D03 Earthdata, D41 GTSM/CDS/licencia, D11 GWIS sin máscara/ciclo acreditados y D18 producto regional/calificación. NASA cuenta con diagnóstico/transporte preparado y metadatos públicos auténticos, sin valores científicos autenticados. El usuario indicó continuar sin esas credenciales: SMAP/GLDAS e IMERG reciente quedan pendientes, sin sustitución demo. Variables/pasos/enlaces en [docs/accesos.md](docs/accesos.md); no se crearon cuentas o aceptaron contratos.
- También quedan ramas pendientes dentro de fuentes conectadas: Sentinel-1/5P y servicios CDSE autenticados, otras regiones Sentinel-2, huellas RGI7 oficiales, ampliaciones MODIS, otras áreas/centros CAP, campos globales/regionales adicionales y validación científica de modelos. Se declara únicamente el producto/ámbito comprobado en la [matriz de 48 fuentes y 31 fenómenos](docs/integraciones.md). Las variables reservadas de acceso no equivalen a conectores implementados. El experimento SST sigue experimental.

Prioridad expresa15/11: terminar MVP científico con anomalías, tendencias e interrelaciones verificables de series reales ya disponibles; no seguir ampliando fuentes indefinidamente ni rediseñar. Estimación funcional comunicada≈70%, distinta del33/38de primeras integraciones. Credenciales no son dependencia del MVP central seleccionado.

El historial de fases e incrementos sigue debajo; sus cifras describen cada momento, no el estado actual.

## Fase 01 — completada

El repositorio solo tenía la especificación, el catálogo, el PNG y los prompts. No había Git ni aplicación. Quedó una base que arranca, con contratos y una prueba real del globo.

### Hecho

- React, Vite y Cesium en `apps/web`, con un visor que se crea y se destruye.
- FastAPI en `services/api`, salud del proceso separada de proveedores.
- Catálogo validado sin modificar los archivos de referencia.
- Esquema JSON y tipos TypeScript generados desde Pydantic.
- Muestra pública de D21 y metadatos públicos de D02. El HDF de SMAP no se descargó.
- Un fixture demo de F11 que el modo real no devuelve.

### Evidencia

- `uv run --directory services/api pytest`: 23 pruebas pasaron.
- `npm --prefix apps/web test`: 2 pruebas pasaron, incluido el remonte sin una segunda instancia.
- `npm --prefix apps/web run typecheck` y `npm --prefix apps/web run build` terminaron sin error. El build copió workers y Natural Earth a `dist/cesium`.
- En http://127.0.0.1:5173/ el globo mostró América del Sur, el crédito «Natural Earth» y «Instancias activas: 1» antes y después de desmontar. Había un solo canvas. No hubo pedidos a `cesium.com`.
- http://127.0.0.1:8000/health respondió `checks: ["process"]`. `/providers` dejó `live_probe` en `not_performed`. D02 está `credential_required` y D21 `sample_retrieved`.
- La textura local respondió 200 en `/cesium/Assets/Textures/NaturalEarthII/tilemapresource.xml`.

### Limitaciones

- Node 22.14.0 es anterior al `>=22.17.0` que declara Cesium 1.147. El aviso no impidió la prueba en el navegador.
- jsdom quedó en 26.1.0 porque la versión 31 no arranca en este Node.
- Docker no está instalado, así que no se verificó un contenedor.
- D02 no tiene archivo científico. F11 real permanece no disponible.
- D21 no es humedad del suelo ni una conexión operativa.
- Las tres comprobaciones HTTP antiguas del catálogo (USGS, SWPC y CNEOS) no se volvieron a ejecutar como sondeo vivo. Esta fase repitió USGS y consultó CMR para SMAP.
- Los 31 fenómenos siguen especificados, no conectados ni validados.
- El PNG de referencia mide 1672×941, no 1920×1080.

## Fase 02 — completada

La pantalla principal reemplazó a la prueba técnica. Conserva el visor de la fase 01 y muestra el escenario demo de Amazonía central.

### Hecho

- Barra superior, filtros, globo, inspector y línea de tiempo con los tokens de `tokens.css`.
- Proporciones medidas sobre el PNG de 1672×941: 17,1 % / centro / 26,1 %.
- Conteos del escenario en un solo fixture. El total de fenómenos sale del catálogo cuando la API responde.
- Búsqueda, agrupación del globo y análisis completo declaran que todavía no operan.
- La línea de tiempo es un único estado en días y se refleja en la ficha.

### Evidencia

- `npm --prefix apps/web test`: 6 pruebas pasaron.
- `npm --prefix apps/web run typecheck` terminó sin error.
- En el navegador, sin overflow horizontal y con un solo visor:
  - 1920×1080, globo con América visible.
  - 1366×768, el inspector conserva la cabecera y el botón de análisis.
  - 1672×941, el tamaño nativo del PNG.
- Desmarcar Observaciones cambió el total del escenario. Acercar no creó otro visor.

### Diferencias que quedan

- El globo no tiene marcadores, huracán ni etiquetas. Eso es la fase 04.
- La textura sigue siendo Natural Earth II, no la imagen fotorrealista de la referencia. La iluminación y el encuadre fino son la fase 03.
- La serie del inspector es sintética y está marcada como demo. No es SMAP ni GLDAS.
- Los iconos son un juego propio de trazos, no una copia del set de la imagen.

## Fase 03 — completada

El área central sigue en CesiumJS. La Tierra visible usa NASA GIBS cuando responde y Natural Earth II si no.

### Hecho

- Base Blue Marble de GIBS, con crédito en pantalla, y respaldo local sin token.
- Iluminación de presentación, atmósfera contenida, sin sol, luna ni nubes estáticas.
- Encuadre de América, zoom, vista inicial y `focusRegion` para extensiones, incluida la que cruza el antimeridiano.
- Límites de altura e inclinación. El arrastre no selecciona. Los rótulos de atrás no se muestran.
- Tres marcas técnicas, no científicas. La fase 04 puede usar `addSignal`, `updateSignal` y `removeSignal`.

### Evidencia

- `npm --prefix apps/web test`: 12 pruebas, incluidas el antimeridiano, la cara oculta y el clic frente al arrastre.
- `npx tsc --noEmit` en `apps/web` terminó sin error.
- En http://127.0.0.1:5173/ el globo mostró América del Sur al centro, el norte arriba y el Atlántico al este. Se cargaron teselas de `gibs.earthdata.nasa.gov` y ninguna de `cesium.com`.
- Encuadrar acercó el norte de Sudamérica. Vista inicial volvió al preset. Tras cambiar a 1366×768 siguió habiendo un visor y el rótulo visible.
- El clic en «Ancla técnica» mostró `tech-amazonia-anchor` y aclaró que no es una medición.

### Limitaciones

- El relieve 3D no está: haría falta Cesium ion o un terreno propio.
- Blue Marble es una imagen fija, no el estado de hoy. GIBS puede no responder y entonces se ve Natural Earth II.
- Las señales ambientales sobre el globo siguen para la fase 04.

## Fase 04 — completada

La pantalla sigue en DEMO. Filtros, mapa, contadores, búsqueda, tiempo e inspector leen el mismo escenario generado.

### Hecho

- Semilla `earth-echo-demo-2026-11-13`. En el instante de referencia se ven 169 registros de apertura. El conjunto amplio agrega 1 202, con dos puntos a 179,2° y −179,2° que no se agrupan juntos.
- Cada registro tiene categoría, tipo, unidad, validez, disponibilidad y fuentes previstas. Un hueco de serie es null. No hay probabilidad.
- En «Ahora» el total es 169. En +7 días quedan 33 pronósticos y la ficha de humedad avisa que ya no está en el mapa.
- Al alejar, el encabezado separa señales y grupos. Vaciar los tipos muestra cómo recuperar resultados.
- La búsqueda distingue región y señal y encuadra la cámara. La capa de humedad se apaga y vuelve sin duplicar el crédito.
- Una sola capa ilustrativa a la vez. Las celdas sin valor son transparentes.

### Evidencia

- `npm --prefix apps/web test`: 17 pruebas, incluidas validez temporal, antimeridiano, huecos del campo y el recorrido de filtros.
- `npx tsc --noEmit` en `apps/web` terminó sin error.
- En http://127.0.0.1:5173/ la apertura mostró América, 169 señales, la ficha «Déficit de humedad» y la capa ilustrativa. Al alejar aparecieron 37 grupos sin cambiar las 169 señales. En +7 días el mapa quedó en pronósticos. La búsqueda de «Amazonía» listó la región aparte de las señales y acercó la cámara.

### Limitaciones

- El campo y las series son ilustrativos. No son SMAP, GLDAS ni un análisis.
- El conjunto amplio sigue en memoria del navegador. No hay paginación ni un proveedor real.
- Earthdata sigue faltando para el HDF de D02.

## Fase 05 — completada para un subconjunto

La primera fuente con archivo, decodificación, índice y mapa es CoralTemp. IMERG no se conectó porque no hay credencial.

### Elección

D01, NASA GPM IMERG Early (`GPM_3IMERGHHE`, versión 07), pide Earthdata o PPS. En este entorno `EARTHDATA_USERNAME` y `EARTHDATA_PASSWORD` no están definidas. No se inventó una URL de gránulo ni se mostró precipitación de demostración en su lugar. La alternativa con acceso público comprobado es D15, NOAA Coral Reef Watch CoralTemp v3.1: SST analizada (`analysed_sst`, `degree_C`), no HotSpot ni DHW.

### Hecho

- Recorte del Caribe occidental, 16,5°N–17,5°N y 67,5°O–66,5°O, cuatro análisis diarios del 8 al 11 de noviembre de 2026 a las 12:00 UTC.
- El archivo original es el NetCDF clásico devuelto por ERDDAP `noaacrwsstDaily`, 25 120 bytes, sha256 `b190912a4f0a8f94ae0b4a5fa4e5254547fef88f93518559cae80b60954af231`.
- La celda 16,525°, −67,175° del 11 de noviembre vale 29,73 °C, igual que la muestra CSV del mismo punto. El relleno −327,68 no se trata como temperatura.
- El mapa y la ficha usan el promedio del recorte. El 11 de noviembre es 29,7295 °C, activo `d15-coraltemp-v3.1-caribe-r1`, observación `d15-sst-20261111T120000Z-r1`.
- Ingerir el mismo archivo otra vez no duplica. Un checksum distinto crea la revisión 2 y conserva la 1.
- La barra tiene DEMO y REAL. En REAL, una respuesta inválida no vuelve a mostrar «Déficit de humedad».

### Evidencia

- `uv run --directory services/api pytest`: 28 pruebas.
- `npm --prefix apps/web test`: 17 pruebas. `npx tsc --noEmit` sin error.
- `GET http://127.0.0.1:8000/v1/sources/D15` respondió `available` y frescura `recent_archive`. `GET /v1/sources/D01` respondió `credential_required`.
- En http://127.0.0.1:5173/ el modo REAL mostró el recorte, la serie en °C, el checksum y la fecha 2026-11-11. Reiniciar la API no borró el índice SQLite.

### Limitaciones

- El recorte no es el producto global ni una actualización en vivo de cada visita. La cadencia diaria y la frescura salen del archivo guardado.
- No hay escala ni offset en este subconjunto. Si otro archivo los trae, la conversión ya los aplica.
- D02 y D01 siguen sin el HDF o el GeoTIFF científico. PostGIS no se incorporó: el índice de esta fase cabe en SQLite.

## Fase 06 — completada para la SST del recorte

La tendencia se calcula en la API, no en el gráfico. El caso real es la misma colección y el mismo recorte de la fase 05, con historia mensual de 2014 a 2025.

### Método, fijado antes del resultado

- Día: promedio de celdas válidas ponderado por el coseno de la latitud.
- Mes: promedio de esos días si hay al menos el 80 % de los días. Si no, el mes queda null.
- Anomalía: diferencia en °C contra la media del mismo mes en 2014–2021. No es un porcentaje. No es una normal de treinta años.
- Recta: mínimos cuadrados, en °C por año. El intervalo remuestrea los residuos en bloques de 12 meses, semilla 20261113.
- Hacen falta 96 meses y ocho años de referencia en cada mes del calendario. Si falta eso, la pendiente queda null.
- Umbral práctico de este caso: 0,02 °C por año. No es un límite de daño.
- Una serie sintética aparte comprueba una pendiente de 0,04 °C por año, un hueco que no se vuelve cero y una serie corta que no se evalúa.

### Resultado real

- 144 meses, sin huecos después de reintentar las descargas que el proxy rechazó.
- La anomalía sube 0,068 °C por año. El intervalo va de 0,024 a 0,109 y no incluye cero.
- Eso no identifica la causa ni es un pronóstico. La climatología comparte años con la recta, así que una tendencia lineal uniforme puede quedar atenuada.
- Ejecución `d707920451b5decd`. Exportación CSV en `/v1/analyses/d15-sst.csv`.

### Evidencia

- `uv run --directory services/api pytest`: 35 pruebas.
- `npm --prefix apps/web test`: 17 pruebas. `npx tsc --noEmit` sin error.
- En http://127.0.0.1:5173/, con REAL y Tendencias, el panel muestra la pendiente y la serie. El globo sigue en el recorte. DEMO dice que no calcula una tendencia.

### Limitaciones

- Una sola región y una sola variable. No hay corrección por muchas comparaciones.
- Los archivos mensuales NetCDF quedan en disco y no en Git. La serie agregada sí está en `data/real/d15/monthly_series.json`, con el checksum de cada mes.
- D01 sigue sin credencial.

## Fase 07 — completada en el alcance con datos públicos

No se marcaron los 31 fenómenos como operativos. La matriz separa observación, indicador, tendencia y pronóstico.

### Conectado

- D15 sigue siendo la SST del Caribe occidental, como campo y como agregado. No es HotSpot, DHW ni blanqueamiento. F19 queda `partial`.
- D21: 15 sismos de magnitud mayor o igual a 5, como puntos. No son probabilidades de réplica. F28 observación queda `partial` y su pronóstico sigue especificado.
- D28: índice Kp planetario, último valor 0,33 a las 2026-11-13T03:00:00. No es un campo de pines ni un aviso local. F29 observación queda `connected`; el pronóstico no.

### Bloqueado o sin archivo

- F01 y D01, F11 y D02: faltan `EARTHDATA_USERNAME` y `EARTHDATA_PASSWORD`.
- F12: GloFAS pide cuenta CDS. No se descargó caudal ni se convirtió en profundidad.
- F15: GWIS quedó como portal. No hay FWI numérico. No es probabilidad de ignición.
- F31 sigue en investigación, sin fecha de colapso.
- Ningún pronóstico del catálogo quedó `connected`.

### Operación y rendimiento

- `d21-events` vence a la hora y `d28-kp` a las tres horas. Un fallo de red conserva la instantánea y no pasa a DEMO.
- En este equipo (AMD Ryzen 7 5700, Windows 10) agrupar 1 000 puntos sintéticos tardó 0,86 ms y 10 000 tardó 4,86 ms. El total representado no cambió. No se midieron cuadros por segundo del globo, así que el objetivo de 30 FPS no se declara cumplido.

### Evidencia

- `uv run --directory services/api pytest`: 38 pruebas.
- `npm --prefix apps/web test`: 18 pruebas. `npx tsc --noEmit` sin error.
- `GET /v1/capabilities` devolvió 31 fenómenos y cero pronósticos conectados.
- En http://127.0.0.1:5173/ el modo REAL mostró «1 agregado SST · 15 sismos», el Kp y, en Histórico, la matriz.

## Fase 08 — completada sin habilidad predictiva demostrada

Hay dos caminos distintos. Ninguno queda validado para uso operativo.

### Pronóstico importado

- Producto SWPC `noaa-planetary-k-index-forecast`, archivado el 2026-11-13T07:56:50Z.
- 17 pasos `predicted` de Kp, válidos desde 2026-11-14T00:00:00Z hasta 2026-11-16T03:00:00Z. Cada paso dura 3 horas.
- El archivo no trae la inicialización del modelo. La emisión guardada es el momento del archivo.
- Las filas `observed` y `estimated` no se publican como pronóstico. El Kp no se convierte en probabilidad ni en aviso local.
- F29, pronóstico, queda `partial`.

### Experimento propio

- Objetivo, fijado antes de puntuar: anomalía de SST del mes siguiente, en °C, en el Caribe occidental.
- Referencias: persistencia del mes de emisión y climatología de anomalía cero. La normal sigue siendo 2014-2021 y no usa la prueba.
- Análogos: 3 julios, o el mes calendario del desenlace, elegidos por la distancia del antecedente. Un vecino entra solo si su desenlace es anterior al mes de emisión.
- Prueba: 2022-01 a 2025-11. 47 casos puntuados y 0 excluidos. Evento fijado: anomalía mayor que 0,3 °C. Frecuencia 0,60.
- Error absoluto medio: análogo 0,404 °C, persistencia 0,214 °C, climatología 0,578 °C. Sesgo del análogo −0,258 °C.
- Falsas alarmas del análogo: 1. Omisiones: 15. La persistencia tuvo 2 falsas alarmas y 2 omisiones.
- No se demostró un error menor que las dos referencias. El experimento queda experimental y no validado.
- La serie no trae `available_at`. El corte oculta meses futuros en las entradas, pero esto no es un replay operativo.
- En la interfaz, junio de 2024 se guardó primero (análogo 0,562 °C, sin desenlace) y después se reveló el desenlace 1,110 °C, con error −0,548 °C.

### Evidencia

- `uv run --directory services/api pytest`: 43 pruebas.
- `npm --prefix apps/web test`: 18 pruebas. `npx tsc --noEmit` sin error.
- En http://127.0.0.1:5173/, modo REAL y Tendencias, se vieron el Kp importado, los tres errores y el desenlace revelado.

## Fase 09 — completada sin inferencia real

El asistente consulta las herramientas de las fases anteriores. No hay un runtime de Qwen en este equipo: `ollama` no está instalado y `127.0.0.1:11434` no respondió tras unos 2 segundos. La inferencia real queda pendiente. No se descargaron pesos.

### Qué puede responder

- Tendencia de SST, experimento, replay con corte, Kp importado, sismos observados y el estado de una fuente o un fenómeno.
- Si la pregunta pide la fecha del próximo terremoto, la comparación de °C con humedad, o una fuente sin credencial, la respuesta lo dice y no rellena el hueco.
- Un documento recuperado que pide validar el experimento no cambia `validated_for_use`.
- Un proveedor simulado que inserta `99.9` se descarta y queda etiquetado como `mock`, no como Qwen.

### Configuración

En `.env`, del lado del servidor: `EARTH_ECHO_LLM_BASE_URL`, `EARTH_ECHO_LLM_MODEL` y, si hace falta, `EARTH_ECHO_LLM_API_KEY`. El navegador no puede enviar otra URL. Un candidato pequeño, cuando exista el runtime, es un Qwen de alrededor de 1.5B servido en local. No se midió memoria ni latencia de un modelo porque no había ninguno cargado.

### Evidencia

- `uv run --directory services/api pytest`: 57 pruebas.
- `npm --prefix apps/web test`: 19 pruebas. `npx tsc --noEmit` sin error.
- `GET /v1/assistant/status` responde `unavailable` mientras las variables estén vacías.
- El panel se abre sobre el mapa sin cambiar la grilla. Cerrar lo devuelve al observatorio.

## Fase 10 — entrega local cerrada

La aplicación arranca con `npm run dev:api` y `npm run dev:web`. Después de reiniciar la API, `GET /health` sigue siendo solo el proceso, `GET /ready` encontró los cinco archivos locales y `GET /v1/sources/D15` respondió 200. `providers_updated` queda `not_checked`. El asistente sigue `unavailable` y el mapa abre igual.

### Recorridos

- DEMO en 1672×941, 1920×1080 y 1366×768: filtros, ficha «Déficit de humedad», pestaña Datos y el instante +7 días, que deja la observación fuera del mapa sin borrarla.
- REAL, tendencia, replay y asistente quedaron comprobados en las fases 05 a 09 y siguen en los mismos endpoints. Esta fase no los reclasificó.

### Comprobaciones

- `uv run --directory services/api pytest`: 58 pruebas.
- `npm --prefix apps/web test`: 19 pruebas. `npx tsc --noEmit` sin error.
- `npm --prefix apps/web run build`: el paquete principal pesa 4,5 MB (1,2 MB gzip) por Cesium.
- `contracts:check` coincide.
- Una copia de `data/real/feeds/d28-kp.json` se restauró en un directorio temporal con el mismo SHA-256. El archivo vivo no se tocó.
- El agrupado de 1 000 y 10 000 puntos sigue dentro del tope de la prueba. No se midieron cuadros por segundo. El equipo sigue siendo el Ryzen 7 5700 con Windows 10.

### Límites que quedan

- D01, D02 y GloFAS siguen sin credencial. Qwen no está instalado. No hay planificador ni Postgres.
- El experimento de SST no está validado.
- La composición se parece al PNG. La densidad de señales, el huracán y los conteos de la imagen no son datos de esta entrega.

La matriz, el guion y la copia están en `docs/entrega.md`.

## Backlog

## Incremento 11A — campos oceánicos y operación real

- D15: SST CoralTemp mundial (2026-11-12T12:00Z), HotSpot y DHW (2026-11-10T12:00Z), cada uno 360×180 a paso 1° por submuestreo de centros nativos 0,05°. SST: 531344 bytes; 22006 faltantes. HotSpot: 30353 faltantes; DHW: 31089. No son 64800 señales ni observaciones puntuales. Cada producto conserva el NetCDF y cotejó una celda con otra petición CSV de NOAA.
- API `/v1/products`, ficha por producto y descarga del original; modos separados. REAL abre amplio, con selector y leyenda/unidad/máscara/fecha. Se preservan historia y experimento del Caribe.
- D21/D28 actualizados realmente el 13/11 a las 22:18 UTC. USGS usa ventana/umbral/límite configurables; conserva magType, revisión y última modificación. Kp observado normaliza UTC; forecast conserva validez y deja emisión e inicialización null si el feed no las informa.
- Planificador persistente en API y `refresh:watch`, sin superposición mediante lock del SO, cadencias, reintento moderado, escritura atómica y retención de cuatro snapshots. Red caída conserva el producto y reintenta después de 15 minutos. La API debe estar encendida para esa cadencia; no es un servicio Windows instalado.
- Accesos ausentes y configuración en `docs/accesos.md`; referencias originales intactas. Los servicios de descubrimiento no se cuentan como feeds.
- Verificación: 61 pruebas API, 19 web y TypeScript pasaron. Las pruebas de scheduler incluyen cadencia, bloqueo concurrente, falla, conservación del último éxito y recuperación. Los temporales de pytest requieren `--basetemp` dentro del workspace en este entorno.
- Continúa automáticamente con NASA MODIS y ECMWF públicos. El pronóstico SST propio sigue experimental y sin habilidad adicional demostrada.

## Incremento 11B — NASA MODIS y pronóstico atmosférico

- D04 MOD13Q1: NDVI y EVI con escala 0,0001 y QA conservadora; D05 MOD11A2: temperatura superficial diurna/nocturna con escala 0,02 K y conversión probada a °C. Subconjuntos de Pampa (-35,-62) y Amazonía (-3,-60) mediante ORNL DAAC, sin cuenta; no son cobertura mundial. Las ventanas de 16/8 días permanecen intervalos, no instantes. Se conserva `proc_date`/tile porque REST no declara el número mayor de colección. Datos recientes disponibles: 16/10 (vegetación) y 24/10 (LST), no observaciones de hoy.
- La muestra inicial de ~10 km se amplía a ~40 km por región tras medir tamaño. Originales/QA/metadatos compartidos entre bandas, reproyección sinusoidal→WGS84 por vecino más cercano. Una segunda petición de banda única coteja valores y georreferenciación; aritmética decimal comprueba escala independientemente.
- D07: IFS oper fc de 0,25°, ciclo 2026-11-13 12Z, plazo +24 h. Temperatura a 2 m, rocío, lluvia acumulada 0–24 h y u/v a 10 m. Solo cinco mensajes GRIB mediante HTTP Range (~2,8 MB), sin descargar la corrida. Malla visible de 1°, original con todos sus nodos; índice de mensajes y nearest-point de ecCodes cotejan tiempo/valor. La emisión no informada queda null.
- Los campos se consultan por API y se seleccionan en el mismo inspector/globo. La franja temporal muestra el producto seleccionado, incluido el tramo futuro de IFS. Se corrigió la leyenda para que sus colores correspondan a los valores dibujados.
- MODIS se revisa diariamente; IFS cada 12 horas, con las mismas garantías de exclusión, retención y persistencia. El hash científico evita que una fecha de descarga escrita por ERDDAP aparente una revisión del dato. Almacenamiento nuevo limitado a 128 MB, conserva cuatro revisiones por producto; si alcanza el límite, conserva lo válido.
- Pruebas añadidas de unidades, QA/nubes/agua/nieve, orientación y reproyección. No se habilita un detector de ola de calor por disponer de un campo de temperatura.
- SMAP también figura en ORNL pero `/SPL3SMP_E/dates` respondió 400 en dos regiones; no se declara conectado. Su vía Earthdata y GLDAS/IMERG continúan bloqueadas por credencial.

## Incremento 11C — OISST, geología, avisos y espacio

- D13 OISST v2.1 mundial, preliminar del 12/11, NetCDF4 original de 1.526.178 bytes. Vista de 1° desde nativa 0,25°, relleno/escala/ejes decodificados. Fecha contra listado oficial y short escalado contra aritmética decimal; original conserva error de interpolación, hielo y anomalía.
- D23: inventario GVP con 1.214 volcanes del Holoceno. El endpoint correcto es `webservices.volcano.si.edu`, enlazado por Smithsonian. WFS 1.0 `hits` devolvió cero; WFS 2.0 confirmó 1.214. Coordenadas GeoJSON cotejadas con atributos nativos. WFS no informa edición: se declara, sin inventar la versión. Es contexto estático, dibujado gris, sin inferir actividad o erupciones.
- D22: OAF de USGS para `us7000txrk`, 20 probabilidades por magnitud y ventanas de día/semana/mes/año. SHA-256 y longitud coinciden con el manifiesto independiente del evento. Se conserva modelo/región/emisión/validez. No se aplica a los demás sismos.
- D27: mensajes de ambos centros NTWC/PTWC, con CAP completo, emisor, estado, cancelación, vigencia y áreas originales. Atom updated coincide con CAP sent. Sin polígono disponible no se dibuja el epicentro como área alertada. Mensajes informativos no equivalen a peligro ni a pronóstico de llegada.
- D29: 2.248 evaluaciones Sentry de objetos conocidos. La probabilidad acumulada de un objeto se contrastó con su endpoint de detalle; consultas secuenciales. Cada probabilidad tiene objeto, rango de años y definición; sin pines terrestres ni fechas de desastre.
- D48: 921 valores ONI históricos; último período ASO 2026 (01/08–01/11), anomalía 2,46 °C. Ventanas móviles de tres meses verificadas, incluido cambio de año. No se etiqueta automáticamente como diagnóstico ENSO vigente ni se sustituye RONI.
- Total en este incremento: 12 fuentes del catálogo con datos retenidos (10 en productos nuevos, más D21/D28), 22 productos nuevos y 17 campos. 37,07 MB en el almacén nuevo antes de nuevas revisiones; límite 128 MB. Los registros estáticos/orbitales no se cuentan como observaciones ambientales.
- API, inspector, búsqueda y contadores usan esos activos. Agrupación real distingue clases y los lados del antimeridiano; selección de un punto superpuesto permanece accesible. Capturas auténticas en `docs/integraciones/`. `/ready` comprueba también los originales científicos nuevos.
- Comprobación: 70 pruebas API pasaron; fixtures pequeños se extrajeron de respuestas reales (no registros DEMO), con comprobaciones específicas de OAF, Sentry, GVP, CAP y ONI. Kp volvió a descargarse a las 22:53 UTC: observado y forecast dieron `unchanged`, avanzó último éxito y se conservó última fecha de cambio.
- Continúa trabajo viable sobre GeoTIFF y subconjuntos públicos. No se declara conectado LHASA por descubrir archivos de ~190 MiB, ni MHW por encontrar un archivo que excede el tope inicial de descarga. RAPID solicita correo/consentimiento: no se envió información del usuario.

## Incremento 11D — subconjuntos grandes y actualización independiente

- D24: LHASA NRT `20261112T0000.tif`, recorte de Columbia Británica 120×120 a resolución nativa ~1 km. Eje ascendente corregido a norte→sur, 262 faltantes; máximo 0,9589964747428894 cotejado por coordenada y reproducido desde bloques originales con un lector nuevo. Se transfirió 1 MiB de un GeoTIFF mundial de 146,9 MB. Es nowcast/modelo importado, sin afirmar eventos observados ni seguridad de laderas.
- D16: NOAA PSL NMME, ciclo octubre 2026, campos de noviembre/diciembre/enero en 1° (360×179). Definición mensual p90 1991–2020 con tendencia, producto externo experimental. HDF5 original 268,9 MB; 6.067.657 bytes en 47 rangos, compartidos entre plazos, archivo de replay 8.091.521 bytes. Valor 0,27419355511665344 cotejado con `struct.unpack` sobre el chunk original, independiente de h5py. Inicialización y validez conocidas; emisión no informada queda null.
- D30: tesela pública GLO-90 de Pampa, original 4.618.020 bytes. Banda nativa 1200×1200, vista cada cinco centros (240×240), sin usar overviews promediados. WGS84 horizontal y EGM2008 vertical documentado contra Product Handbook 5.0. DSM estático incluye vegetación/construcciones; no habilita inundaciones ni terreno desnudo.
- 15 fuentes del catálogo con datos retenidos, 27 productos nuevos y 22 campos. Almacén nuevo ~59 MB, presupuesto 128 MB y cuatro revisiones. La identidad contempla cambios de método/datum y no descarta cambios nativos por ser igual la vista reducida.
- Tarea Windows `Earth Echo - Public Data Refresh` instalada, en ejecución y con revisión persistida; se inicia al iniciar sesión y funciona sin la aplicación abierta. API y worker comparten exclusión del SO. `/v1/operations/refresh` separa intento, éxito, cambio, próximo intento y revisión del worker. Instrucciones reproducibles en `docs/actualizacion.md`.
- Consulta de apertura reducida de 14.686.191 a 51.478 bytes mediante `summaries=true`; detalle bajo demanda. Leyenda y encuadre explícito conservados. Se corrigió orden de hooks al pasar entre una ficha sísmica y SST. Inspector accesible a 1100×720, ancho documental 1100 sin desborde. Capturas REAL de MHW, LHASA y ventana reducida en `docs/integraciones/`.
- Comprobación: 72 pruebas API, 20 web, contratos generados y build de producción. No se promociona ningún modelo por estas pruebas. Sigue IBTrACS; accesos autenticados pendientes afectan solo sus productos.

## Incremento 11E — trayectorias históricas de ciclones

- D47 IBTrACS v04r01: muestra inicial ACTIVE de 139 posiciones/3 sistemas, cotejada entre CSV y NetCDF. Ampliación posterior al original `last3years` de 1.508.639 bytes; consulta local de sistemas con última posición en los últimos 30 días: 15 trayectorias y 783 posiciones. El original conservado permite acceder a los valores científicos de tres años, sin cargar toda la historia en el globo.
- UTC y coordenadas nativas, longitudes normalizadas a WGS84 y original conservado por registro. Viento WMO en nudos, agencia y períodos sin armonizar; `IFLAG`, presión, naturaleza y estado provisional permanecen accesibles. En registros provisionales el viento WMO puede faltar: no se reemplaza por el viento de otra agencia ni por cero.
- Contrato de trayectorias reutiliza `GeoMultiLineString` y extensión con `crosses_antimeridian`. OLANA cruza realmente el antimeridiano: dos partes sin saltos mayores de 180°. Solo se interpola el borde para dibujar, sin inventar una observación o tiempo. El inspector conserva selección y permite encuadre explícito de cada sistema; cámara amplia al entrar en REAL.
- 16 fuentes con datos, 28 productos nuevos y 22 campos. Actualización IBTrACS diaria instalada en el mismo worker. Segunda ingestión `unchanged`, una sola revisión; ninguna probabilidad o trayectoria futura derivada de estos best tracks.
- 76 pruebas API pasaron, contratos generados y build de producción. Fixture numérico pequeño extraído de cuatro sistemas reales y CSV original conservados para verificar calidad, faltantes y cruces. Captura auténtica `real-ibtracs-antimeridiano-1672x941.jpg`.
- Continúa GDACS: API SEARCH respondió vacía; RSS público sí entregó registros. Un enlace CAP de inundación devolvió HTML; CAP de ciclón entregó geometría real. Esa diferencia no se oculta ni se convierte en área inventada.

## Incremento 11F — áreas CAP y estado operativo visible

- D35: dos CAP originales de ciclones GDACS (CEMPAKA-26 v22, PENA-26 v24), con polígonos WGS84, emisor, emisión, estado, tipo, urgencia, severidad, modificaciones y referencias. Ambos mensajes declaran `Past`; no se presentan como peligro vigente ni como predicción propia. Expiración ausente permanece null; `todate` no se usa como expiración. RSS/CAP coinciden en eventid, versión, nivel y modificación.
- Los polígonos viven en el mismo adaptador Cesium y se seleccionan en el inspector. GEOS/Shapely se usa para partición geométrica al antimeridiano, sin otro mapa/servidor. Geometría inválida se rechaza en lugar de repararse sin evidencia. Pruebas de corte conservan partes cerca de ±180° y no dibujan cruces por Greenwich.
- Alcance: máximo tres CAP de ciclón por consulta, cada seis horas. No se declara conectada la inundación cuyo CAP respondió HTML, ni la API SEARCH que devolvió cuerpo vacío. Segunda ingestión real `unchanged`.
- Inspector muestra intento, descarga correcta, cambio y próximo intento separados, además de emisión y fecha científica. Se conserva la última carga de sismos/Kp si falla una consulta de interfaz. El planificador registra la finalización real de cada descarga y no anuncia conservación de un producto que nunca tuvo éxito.
- Se corrigió la asignación de las nuevas capacidades de ciclones: corresponde al ID original F06, no F04 (tormentas severas/granizo). Los 31 IDs y referencias permanecen intactos.
- 17 fuentes con datos, 29 productos nuevos, 22 campos; almacén 66.418.367 bytes. 78 pruebas API, 20 web, contratos y build pasaron. Captura REAL `real-gdacs-cap-1672x941.jpg`, con área y estado Past accesibles. Continúa trabajo numérico viable sin credenciales.

## Incremento 11G — GEBCO numérico con tipo de fuente

- D31 GEBCO_2026: recorte nativo 15 segundos de arco del Caribe (85–84° O, 17–18° N), 240×240 centros. Muestra inicial 30×30 de 7.854 bytes; ampliación tras medir. Elevaciones -5.497 a +134 m, sin faltantes declarados en el recorte. Positivo hacia arriba, nivel medio del mar nominal EPSG:5831; heterogeneidad vertical somera expresamente conservada.
- Tipo de fuente TID alineado por celda, no confianza: 91 tierra, 965 multihaz, 273 mediciones directas combinadas, 53.633 predicción guiada por gravedad y 2.638 fuentes mixtas/interpoladas. La resolución de 15 segundos no se presenta como exactitud o medición directa.
- ASCII científico OPeNDAP y metadatos retenidos, cotejados con valores binarios de los archivos mundiales. Elevación usa HDF5; TID resultó CDF-1, no HDF5. El primer intento se detuvo al alcanzar el presupuesto; se corrigió la detección explícita del formato, sin ampliar a una descarga mundial. Valores independientes: elevación -3.987 m y TID 40 con coordenadas coincidentes. Archivo local de evidencia 2.065.411 bytes frente a originales de 7,5 y 3,7 GB.
- API, campo, leyenda, calidad por celda, original e inspector disponibles. Actualización mensual en tarea Windows; repetición e idempotencia registradas. 18 fuentes con datos, 30 productos nuevos y 23 campos. No habilita profundidad de inundación, simulación costera ni navegación.
- 79 pruebas API, contratos y build de producción pasaron. Se conservan dos respuestas ASCII auténticas pequeñas para probar valores y ejes. Continúa FAO ASIS: GeoTIFF flotante y `getSamples` ya entregaron el mismo 58,5; máscara/estación/período todavía en implementación.

## Incremento 11H — ASIS agrícola numérico

- D20 FAO ASIS: `ASI_D/8457`, `ASIS.ASI-D.2026-11-D1.GS1.LC-C`, Cropland/Season 1. Se resolvieron catálogo oficial, metadatos, nombre/estación, origen nativo y exportación F32 sin renderer. Muestra inicial de Pampa de 66 kB cotejada contra getSamples (58,5 %). La ampliación mundial a 1° no coincidió con el píxel nativo por selección de overviews del servicio: se rechazó, sin publicarla como campo científico verificado.
- Producto publicado: recorte nativo ~2° de Pampa, 224×224 (~1 km), bordes alineados al origen. Valores 0–43,5 %, 10.186 faltantes; máximo 43,5 cotejado con consulta independiente al mismo OBJECTID. 251/253/254 conservados como códigos especiales y transparentes, sin asignarles significados individuales no publicados en la tabla consultada. Cero porcentual válido permanece cero.
- ASI es porcentaje de superficie agrícola afectada en unidades administrativas desde el inicio del ciclo, con VHI<35 y ponderación fenológica según FAO. No es observación independiente por celda, probabilidad, rendimiento ni humedad del suelo. La ventana 01–11 noviembre UTC identifica la edición dekadal, no el comienzo del período acumulado ni una emisión conocida.
- Original GeoTIFF, metadatos, leyenda, consulta y comprobación compartidos en un activo de 374.275 bytes. Repetición `unchanged`, una revisión, aunque la URL temporal de exportación cambia: identidad basada en el GeoTIFF completo y contexto científico. Revisión diaria en tarea instalada; acceso sin cuenta. Conserva limitación regional y estación elegida.
- 19 fuentes con datos, 31 productos nuevos y 24 campos. 81 pruebas API, contratos y build pasaron; fixture GeoTIFF auténtico comprueba rango, códigos, faltantes y coordenadas. Captura REAL de Pampa en `docs/integraciones/`.
- Continúa la búsqueda numérica de langosta del desierto y los indicadores reproducibles sobre insumos retenidos. No se declara conectada una capa por aparecer en ArcGIS.

## Incremento 11I — observaciones RAMSES de langosta del desierto

- D19 FAO Locust Hub: se siguió el WebMap oficial hasta `Ramses_Observations_Dashboard_View/0` (ítem `ed8228a11a2547178cdf4ab002464efb`, propietario `faodlis_hqfao`). El grupo genérico del Hub contenía elementos ajenos; no se usaron como evidencia. Consulta UTC de siete días, máximo 200: 49 reportes actuales de Mauritania (20 ADULT, 19 HOPPER y 10 NO LOCUST).
- Categoría biológica explícita, sin cantidad de individuos inventada. Las ausencias reportadas no son enjambres ni seguridad regional. Coordenadas GeoJSON cotejadas con atributos nativos y una consulta Esri JSON por OBJECTID; coordenadas inválidas quedan sin pin. `Obs_Date` se conserva UTC y `Observation_Time` permanece texto, sin inventar una hora de observación. Confirmación/fiabilidad son etiquetas del proveedor, no probabilidades.
- API, puntos, agrupación e inspector reutilizados. Encuadre de Mauritania solo al pulsar cobertura; selección por tabla/búsqueda accede también a registros superpuestos. Tabla paginada de 40 permite acceder a todos los registros conservados, incluyendo los más recientes; ya no se limita a los últimos cuarenta del array.
- Original y metadatos retenidos (57.292 bytes en revisión final). El ítem no declara licencia específica; se conserva esa limitación, la atribución y el enlace a condiciones FAO. No se extrapola a langostas sudamericanas ni se integra migración futura por tener observaciones. Una consulta sin reportes se coteja por count=0 sin inferir ausencia de la especie.
- Repetición final `unchanged`: tres revisiones de desarrollo antes/después, sin duplicado nuevo; identidad incluye todos los reportes y excluye solo los límites de petición variables. Cadencia diaria en tarea Windows. 20 fuentes con datos, 32 productos nuevos y 24 campos.
- 83 pruebas API, 20 web, contratos y build pasaron. Fixture GeoJSON auténtico comprueba categorías, fecha, fiabilidad y posición; captura REAL de Mauritania con reporte NO LOCUST seleccionado. Continúa con indicadores reproducibles sobre IFS retenido y accesos numéricos pendientes.

## Incremento 11J — indicadores físicos reproducibles de IFS

- Rapidez del viento a 10 m: `sqrt(u10²+v10²)`, m/s, del mismo ciclo y +24 h. VPD a 2 m: `e_s(T)-e_s(Td)`, kPa, ecuaciones 11/14 FAO-56 con a=0,6108, b=17,27, c=237,3. Dominio conservador 0≤Td≤T≤50 °C; hielo/supersaturación/faltantes permanecen ausentes, no se recortan a cero. Es instantáneo, no VPD diario, ETo, FWI, humedad del suelo o estrés de cultivo confirmado.
- Dos campos derivados a 1°, con fórmula, parámetros, unidades, intervalo, versión y SHA de entradas en contrato/API/inspector. Conservan ambos mensajes GRIB completos en el activo; lectura de originales ya retenidos, cero nuevas descargas por cálculo. Cotejo por coordenada desde el GRIB con sqrt independiente de hypot y Decimal de 40 dígitos para VPD. No se promociona el experimento SST ni otro modelo.
- Viento: 0,014074–26,680106 m/s, sin faltantes en estos componentes. VPD: 0,007750–6,429819 kPa, 27.877 centros fuera del dominio/faltantes. Repetición `unchanged`. Cadencia 12 h en tarea Windows; cálculo y descarga se etiquetan por separado.
- 20 fuentes con datos, 34 productos nuevos, 26 campos, dos calculados. Cero señales/eventos calculados; los centros de campos no inflan ese contador. Insumos de entorno parciales para F04/F15, sin detector de tormenta ni probabilidad de ignición.
- Medición previa: 71.521.479 bytes en almacén, 16.469.328 bytes de JSON actual, 31.336.860 de originales únicos actuales; 177.620.832.256 bytes libres en E:. Presupuesto ampliado a 256 MB configurable para soportar revisiones de las integraciones nuevas, manteniendo cuatro por producto y conservación del válido si llega al tope.
- 85 pruebas API, contratos y build pasaron. Prueba independiente contra ejemplo FAO publicado 24,5 °C→3,075 kPa y 15 °C→1,705 kPa; pruebas de ausencia/dominio y vector 3–4–5. RGI se resolvió por DOI/CMR pero su distribución NSIDC redirige a Earthdata: D26 requiere las mismas variables NASA, sin iniciar sesión ni crear cuenta.

## Incremento 11K — límite total de actualización por fuente

- Las comprobaciones de proveedores públicos mostraron que un timeout de socket de 25 s no limita DNS ni una respuesta que sigue enviando bytes. Cada trabajo ahora corre en un hijo con límite total de 180 s configurable entre 30 y 600 s. El padre termina/espera al hijo vencido, registra el fallo y continúa con la siguiente fuente, manteniendo exclusión del SO y estado persistente.
- No se agregaron servidores, base de datos ni colas. El hijo solo ejecuta el ID registrado; secretos heredados por entorno, sin argumentos. La última revisión válida permanece REAL. Prueba de vencimiento comprueba conservación del éxito previo y ejecución posterior de otra fuente; cadencia, bloqueo, fallo/recuperación siguen comprobados.
- 86 pruebas API pasaron. Tarea Windows reiniciada con el código nuevo; ejecución Kp real por hijo terminó `stored` a las 01:27:06 UTC del 14/11, con intento/éxito/cambio distintos y sin solapamiento. Continúa HydroATLAS: atributos nativos completos leídos y geometría comprimida obtenida; algunas geometrías originales son inválidas y requieren máscara explícita, sin reparación silenciosa ni declaración de capa ya integrada.

## Incremento 11L — cuencas HydroATLAS reales

- D32 BasinATLAS 1.0, nivel 03: 31 unidades sudamericanas (HYBAS_ID 603…), geometría, SUB_AREA y UP_AREA en km² y topología nativos. DBF tiene 292 registros/294 campos globales; los restantes atributos quedan en el original sin interpretación. COAST agrupa cuencas costeras y ENDO conserva conexiones virtuales; no se declara caudal, almacenamiento ni inundación.
- Cuatro miembros SHP/SHX/DBF/PRJ de Figshare 20087237, 31.686.187 bytes de rangos frente al ZIP de 4.276.492.333 bytes; archivo de replay 42.248.961 bytes, CRC32 y PRJ WGS84 comprobados. Áreas cotejadas por dBASE/Decimal y bbox por SHX/SHP binarios/coordenadas. Un 403 declaró ExpiredRequest: renovación única de redirección pública, sin reintentar rechazos de autorización.
- 23 originales contienen anillos que se tocan. Transformación explícita sólo para dibujo con GEOS make_valid(structure), diferencias de área planar relativa menores de 5e-15 y bbox conservada (criterios 1e-10). Simplificación topológica 0.01°: 297.382 vértices nativos a 61.330 visuales; áreas científicas intactas, calidad por unidad y originales accesibles. No se oculta esa transformación ni se usa la geometría visual para cálculos.
- API/inspector/polígonos reutilizados; cámara amplia conservada. Segunda ingestión `unchanged`, revisión mensual preparada en el mismo worker, caché nativa evita repetir 31 MB al verificar la identidad del archivo. Primer acceso dispone de límite específico de 420 s. Almacén nuevo 125.353.224 bytes, dentro de 256 MB; una caché acotada adicional de 42,3 MB.
- 21 fuentes con datos, 35 productos nuevos y 26 campos. 89 pruebas API, 20 web, contratos y build pasaron. Fixture de dos cuencas auténticas incluye anillo que se toca; pruebas de CRC/rangos/expiración y de rechazo a lectura completa. Captura REAL `real-hydroatlas-1672x941.jpg`.
- Descubrimiento adicional dejó bloqueos precisos de Sentinel (401 en activo), RGI 7 (Earthdata), RAPID (formulario de correo/consentimiento) y productos ecológicos regionales, sin convertir portales o imágenes en feeds. Continúa FIRMS NOAA-20 público: CSV regional con 15.977 registros y shapefile original ya obtenidos para cotejo.

## Incremento 11M — FIRMS NOAA-20 y escala de puntos reales

- D06: índice oficial resolvió CSV/SHP `J1_VIIRS_C2_South_America_24h`. La prueba antigua de Suomi NPP estaba vacía porque su cobertura publicada terminó 02/11/2026; no era bloqueo de toda FIRMS. NOAA-20 C2 público entregó 15.977 detecciones (12/11 03:06–13/11 18:51 UTC), datos de adquisición reales aunque el nombre diga 24h. CSV 1.343.869 bytes, ZIP 625.144; activo compartido ~2,19 MB.
- Todos los registros cotejados con geometría/DBF: FRP MW, I4/I5 K, tamaño km, UTC, satélite, versión y calidad. 15.176 nominal/high se dibujan; 801 low conservan coordenadas/FRP en tabla/original mediante máscara `map_eligible`. No es área quemada, incendio único ni probabilidad de ignición; incluye otras anomalías térmicas posibles. F15 tiene observación parcial, sin prometer FWI.
- Ingestiones repetidas `unchanged`, recuperación de red y conservación del válido comprobadas con muestras auténticas; IDs estables y sin duplicados. Archivo vacío coherente no se transforma en ausencia regional ni DEMO. Actualización 3 h registrada en tarea Windows; intento/éxito/cambio separados (último éxito verificado 01:52:24 UTC).
- La prueba visual detectó bloqueo al enviar 15.000 billboards: la agrupación anterior solo comenzaba por encima de 16.000 km, mientras la cámara inicial usa 13.200 km. REAL ahora agrupa en la vista inicial y limita a 1.500 símbolos con conservación de cantidades y selección individual. La tabla sigue permitiendo seleccionar low y puntos superpuestos. Capturas auténticas de referencia y de inspector 1100×720; 1366×768 también sin desborde. Consola de la vista corregida sin errores.
- Contadores corregidos: 22 fuentes con datos, 36 productos nuevos, 26 campos (dos calculados), 16.200 registros de observación, 1.704 históricos, dos registros de indicadores importados y cero señales calculadas. Los históricos ONI/IBTrACS ya no inflan observaciones. 31 fenómenos sigue siendo el catálogo, no detectores activos.
- Verificación reproducible `python -m earth_echo.tools.verify_integrations`: 36 detalles API idénticos al almacenamiento, originales servidos con SHA coincidente, 30 activos únicos/77.898.365 bytes, resumen 80.069 bytes; leyendas/máscaras/contadores coherentes. Evidencia en `data/operational/integration_evidence.json`; referencias originales sin cambios. No evalúa habilidad predictiva.
- 93 pruebas API (incluida ingesta offline/idempotencia/recuperación FIRMS), 21 web, contratos y build. Almacén medido 160 MB antes de otra revisión de metadatos, dentro de 256 MB. Continúa actividad volcánica publicada y otras capacidades públicas verificables; fuentes autenticadas permanecen bloqueadas sólo en su alcance.

## Incremento 11N — reportes de actividad volcánica publicados

- D23 amplía inventario con 27 reportes GVP/USGS del 8–14 octubre 2026, emitidos 15/10 07:11:08 UTC. RSS y CAP 1.1 entregaron ese archivo atrasado, mientras la página semanal muestra noviembre y su descarga automatizada respondió 403. Se integra como archivo histórico explícito; no se oculta el atraso ni se declara actividad actual.
- Categoría nativa New/Continuing Eruptive Activity, país, nombre, ID GVP, coordenadas y fuentes primarias. Cotejo de los 27 registros entre RSS/CAP. Circle CAP tiene radio cero: punto del volcán, sin área de peligro inventada. Valor/probabilidad null; no extracción de intensidades ni predicción de erupción desde narrativa.
- Fechas por registro representan emisión, período de actividad permanece texto local sin zona homogénea. Canal RSS declara una zona con una hora de diferencia frente a ítems/CAP; ambas conservadas. Originales ISO-8859-1 exactos en activo de 107.239 bytes, actualizador diario/idempotente `unchanged`, último éxito 02:07:01 UTC. No se vuelve a descargar el inventario para los reportes.
- 37 productos nuevos/22 fuentes, 26 campos, 1.731 registros históricos separados de 16.200 observaciones. Verificación de originales/API repetida: 31 activos únicos/78.005.604 bytes, resumen 82.875 bytes, referencias intactas. 94 pruebas API y build pasaron; la suite web previa de 21 sigue pasando y no cambió la lógica científica de agrupación.
- Continúa una vía pública documentada por OGGM para inventarios glaciares RGI6. La distribución oficial de RGI7 sigue requiriendo Earthdata; no se sustituirá edición silenciosamente.

## Incremento 11O — muestra científica RGI7 pública

- D26: la ruta oficial NSIDC de huellas RGI7 exige Earthdata. El enlace RGI6 global documentado por OGGM devolvió 404; al recorrer su índice público apareció una vía real para atributos RGI7 G/C. Se preservó la edición 7.0 y el origen académico de la copia, sin sustituir silenciosamente por v6.
- 953 registros completos iniciales de Alaska, IDs RGI2000-v7.0-G-01-00001…00953: áreas km² y puntos representativos nativos, no centroides ni polígonos. No cubren todo Alaska. src_date textual conserva la fecha de la imagen fuente sin zona; no se inventa una observación actual UTC. Área faltante permanece null, coordenadas originales accesibles y máscara visual explícita.
- Lectura de 262.144 bytes de G y 131.072 de C frente a originales de 74.734.943 y 17.449.800 bytes; activo reproducible 699.999 bytes. Primer caso cotejado entre G y complejo C coincidente: 0,239199161030735 y 0,2391991610307348 km², mismo punto -155,90940361036584 / 67,4137265. Content-Range/coherencia/replay y semántica de unidades contra guía RGI7.
- Ingestión repetida `unchanged`; revisión mensual activada en tarea Windows y comprobada a las 02:21 UTC del 14/11. Área estática no habilita lagunas, diques, vaciamientos ni predicción GLOF; F26 lo declara bloqueado. Huellas oficiales siguen pendientes de Earthdata. No se agregaron pines de evento o celdas para aparentar densidad.
- 23 fuentes con datos y 38 productos nuevos; 26 campos, dos calculados, 1.731 registros históricos y cero señales calculadas. Comprobación actual de originales/API: 32 activos únicos/78.705.603 bytes; resumen 85.986 bytes. Contador de observaciones cambió de 16.200 a 16.206 por actualizaciones automáticas reales; el inventario estático no lo incrementa. Almacén medido 182.045.422 bytes antes de esas revisiones, dentro de 256 MB.
- 96 pruebas API, 21 web, contratos y build pasaron. Se corrigieron textos heredados de D21 que todavía anunciaban la muestra inicial de 20 sismos/magnitud 5 y de D28 que sugerían emisión conocida. La matriz distingue expresamente GIBS visual y CMR descubrimiento, sin contarlos como nuevas fuentes científicas. Inspector vuelve al inicio al cambiar de producto y distingue contexto/archivo/observación; no etiqueta una fecha UTC ausente como disponible. Captura auténtica RGI7 en `docs/integraciones/real-rgi7-alaska.jpg`.

## Incremento 11P — RAPID observacional procesado, sin formulario

- D34: la ficha oficial `rapidtransportsv2024-2nc` publica una URL directa del NetCDF y el documento de edición declara datos abiertos. Acceso comprobado sin correo/cuenta/formulario. No se eludió autenticación ni se enviaron datos personales. Archivo medido 7.050.022 bytes, no el ZIP de 286 MB; un único activo compartido por tres productos.
- 248 medias mensuales abril 2004–noviembre 2024 de la sección RAPID 26,5° N: AMOC en Sv, calor en PW y agua dulce en Sv; positivo norte, negativos conservados. `Units` nativo usa mayúscula. NaN permanece null. Calendario CF gregorian/days since 1950-01-01 y cobertura comprobados. Creación 14/10/2026 sin hora/zona no se inventa como emisión UTC; no son datos de hoy.
- Todos los valores cotejados con `struct` desde dobles/offsets nativos, independiente de la lectura h5py. Media/SD muestral AMOC 17,099724647… / 3,150… Sv coinciden con 17,1±3,2 Sv oficiales a un decimal. Un intento adicional de reconstruir AMOC desde máximo de perfiles discretos 200–2000 m difirió hasta 0,001617 Sv: se documenta y no se sustituye la serie publicada ni se proclama esa reconstrucción validada. Incertidumbre separada llega sólo a 2015; no se extrapola a 2024.
- Contrato `time_series`, gráfico de los 248 meses y tabla paginada, sin pines ni malla mundial. Curvas cortadas ante valores ausentes y seis rótulos temporales como máximo, preservando todos los puntos. El aviso de producto sin geometría permanece dentro del mapa, sin superponerse a la franja temporal. Captura auténtica `real-rapid-amoc.jpg`.
- Repetición mediante planificador `unchanged`, revisión semanal de la edición fija, último éxito 05:43:51 UTC. F31 habilita observación procesada parcial; análisis de tendencias y pronóstico permanecen separados. No se infiere probabilidad/fecha de colapso, ni se promociona el experimento SST.
- 24 fuentes con datos, 41 productos nuevos, 26 campos (dos calculados), 2.475 registros históricos y cero señales calculadas. Verificación de originales/API: 33 activos únicos/85.755.625 bytes, resumen 95.668 bytes y referencias intactas. 98 pruebas API, 22 web, contratos y build pasaron. Continúa la búsqueda de distribución científica pública de clorofila NASA, sin sustituirla por imágenes o datos NOAA de otro producto.

## Incremento 11Q — clorofila Sentinel-3A científica

- D25: producto `noaacwS3AOLCIchlaDaily`, procedencia Copernicus/Sentinel-3A OLCI y procesamiento/distribución modificada NOAA. No se lo atribuyó a NASA D17 ni se declaró descargada la escena Sentinel-2 protegida. Atribución «Contains modified Copernicus Sentinel data» conservada en API/inspector/mapa.
- Muestra 4×4 de 5.508 bytes en Atlántico sur resultó completamente ausente y se mantuvo así. Ampliación posterior medida a 400×200 (0,9°, stride 24 sobre L3 nativo 0,0375°): 7.132 celdas finitas y 72.868 faltantes, baseline 10/11/2026 12:00 UTC. No relleno de nubes/tierra ni celdas convertidas en señales.
- OC4Me Experimental, mg m^-3 nativos → etiqueta mg/m³ sin cambio numérico. Rango 0,01–315,0909729; máximo cotejado con CSV independiente 315,09097. ColorBarMaximum=64,7 no se usó como máscara o recorte. Color log10 sólo para visualizar, valores científicos intactos; cero no se oculta para satisfacer esa escala. graphics es overlay, no QA; no hay flags individuales descargados ni confianza inventada.
- NetCDF y máscara consultables por API/original, leyenda con unidad/fecha/escala/resolución y captura REAL. Identidad incluye todos los valores/atributos y conserva historial de procesamiento, excluyendo sólo líneas volátiles de petición. Repetición `unchanged`; cadencia diaria en tarea Windows, último éxito comprobado 06:05:22 UTC.
- F20 tiene un insumo observacional parcial de clorofila, sin especie/toxicidad/evento HAB o pronóstico biológico. D17 NASA sigue pendiente: PFEG no respondió y el dataset global público consultado termina en 2022; no se hizo una sustitución semántica.
- La lista de 42 productos tiene desplazamiento propio y altura acotada: la leyenda queda accesible en 1280×720 sin recorrer toda la lista. Fecha UTC, unidad, resolución, escala y cantidad de huecos comprobadas en la captura REAL.
- 25 fuentes con datos, 42 productos nuevos, 27 campos (dos calculados), 2.475 registros históricos, cero señales calculadas. 100 pruebas API, 23 web, contratos y build pasaron. Evidencia de originales/API repetida: 34 activos únicos/86.108.038 bytes, resumen 99.058 bytes, referencias intactas; almacén 211.303.107 bytes dentro de 256 MB. Continúan únicamente ampliaciones con datos reales y método verificable.

## Incremento 11R — análisis descriptivo RAPID reproducible

- D34 comparte el NetCDF ya retenido: no nueva descarga ni otro activo para el análisis. Años calendario 2005–2023 fijados antes del cálculo; 2004 y 2024 parciales excluidos. Medias mensuales ponderadas por días gregorianos/bisiestos; un mes faltante deja el año null, sin interpolación. Ajuste con al menos 15 de 19 años completos, cada año válido con igual peso.
- Producto `d34-amoc-annual-trend`: 19 medias anuales en Sv y pendiente OLS descriptiva −0,8416859261676243 Sv/década. Todas las medias cotejadas con `numpy.average`; pendiente independiente por SVD `numpy.linalg.lstsq` −0,841685926167622. Fórmula, parámetros, período, versión e insumo SHA en API/inspector; etiquetas diferencian agregado calculado de observación nativa.
- F31 tiene tendencia descriptiva parcial para esa sección/período, sin inferencia de significación, causalidad, aceleración, autocorrelación corregida, intervalo, probabilidad o fecha de colapso. No habilita pronóstico ni cambia el experimento SST.
- Ejecución real del planificador e idempotencia `unchanged`, último éxito 06:21:43 UTC. Tarea Windows reiniciada y comprobada Running con trabajo semanal nuevo. Pruebas de años incompletos, bisiestos, pendiente conocida, mínima cobertura, corrupción de entrada/conservación y recuperación; muestra científica auténtica existente, sin fixture inventado de proveedor.
- 43 productos / 25 fuentes, 27 campos (dos calculados), un análisis descriptivo, 2.475 registros históricos, dos indicadores importados y cero señales de evento. Contadores y verificador distinguen estos tipos; originales únicos siguen siendo 34 / 86.108.038 bytes. API/original/valores comprobados; resumen 103.266 bytes, referencias intactas. 103 pruebas API, 24 web, contratos y build pasaron. Captura REAL `real-rapid-annual-trend.jpg`, consola sin errores.

## Incremento 11S — humedad relativa del aire desde IFS retenido

- D07: `d07-ifs-rh-24h`, humedad relativa a 2 m (%) mediante FAO-56 10/11/14, 100 e_s(Td)/e_s(T). Comparte exactamente el activo GRIB T/Td de VPD: 34 originales únicos se conservan, sin nueva descarga. No es humedad del suelo/combustible, FWI ni probabilidad.
- Dominio conservador respecto de agua líquida 0 ≤ Td ≤ T ≤ 50 °C. 36.923 centros válidos y 27.877 ausentes en la vista mundial de 1°; rango real 9,2559–98,9956 %. Hielo/supersaturación/faltantes permanecen null, sin recortar a 0/100 %. Ciclo 13/11 12Z, validez 14/11 12Z; emisión desconocida no se reemplaza por recuperación.
- Valor nativo GRIB consultado por coordenada y calculado con Decimal 40 dígitos: 88,64196419540082 %, frente a float 88,64196419540083 %. Originales y máscaras accesibles por API/inspector, método/parámetros/entradas SHA documentados. Captura REAL `real-ifs-relative-humidity.jpg`.
- Planificador real repetido `unchanged`, último éxito 06:35:25 UTC; tarea Windows Running, revisión reciente y ningún trabajo fallido en ese instante. 104 pruebas API, contratos comprobados; 24 pruebas web y build previos siguen vigentes porque este incremento no modifica código web. Referencias originales intactas.
- 44 productos / 25 fuentes, 28 campos (tres calculados), un análisis descriptivo, 2.475 registros históricos, dos indicadores importados y cero señales de evento. Verificador API/originales pasó: 34 activos / 86.108.038 bytes; resumen 106.662 bytes. Almacén medido 212.949.947 de 256.000.000 bytes.
- Se descartó otra vez la ruta pública SMAP ORNL: lista bandas pero `dates` responde 400 sin datos en Pampa y el ejemplo norteamericano, además de Amazonía previamente. No se cuenta como integración. IMERG GIS requiere PPS en esa distribución; Marine sigue requiriendo cuenta. Se conservan los bloqueos exactos en accesos. La prueba visual a 900×650 confirmó inspector accesible y ancho sin desborde, pero halló contadores/controles cubiertos por el panel; se corrige a continuación.

## Incremento 11T — paneles reducidos y controles accesibles

- La verificación a 900×650 detectó contadores/zoom/leyenda cubiertos por el inspector. En el breakpoint existente se reserva el ancho del panel para esos controles y para el mensaje de producto sin geometría. La leyenda deja además espacio a los botones de zoom. No se mueve la cámara ni se añaden puntos.
- Panel reducido con fondo opaco para que no atraviesen sus textos las etiquetas del mapa; proporciones/tokens de escritorio conservados. Botones Filtros/Detalle informan `aria-expanded`. La lista acotada de productos mantiene unidad/fecha/leyenda accesibles.
- Medición REAL 900×650: inspector x560–900, contadores hasta548, zoom516–548, leyenda12–504, ancho documental900. A1100: inspector desde760, contadores/zoom hasta748; ambos paneles abiertos conservan espacio y sin desborde. Captura auténtica `real-inspector-900x650.jpg`, consola sin errores y tamaño temporal restaurado.
- 24 pruebas web y build de producción pasaron tras el cambio. No cambió la ciencia ni se repitieron innecesariamente las 104 pruebas API ya aprobadas. Las ampliaciones restantes necesitan los accesos/productos listados arriba; no se declaran completas ni se sustituyen por imágenes o fixtures.

## Incremento 11U — cotejo completo y falla externa real de Sentinel-3

- La muestra CSV independiente se conserva tal como la devolvió el proveedor. El conector v2 exige columnas/unidades UTC/m/degrees_north/degrees_east/mg m^-3, fecha, altitud y coordenadas devueltas, antes de cotejar concentración. Rechaza una coincidencia numérica que corresponda a otra ubicación/fecha/unidad.
- Prueba de ingestión completa con NetCDF/CSV auténticos: repetición sin duplicados, falla de transporte, conservación del producto anterior y recuperación. El control mínimo de descubrimiento del test es sintético explícito; no contiene valores científicos inventados. 106 pruebas API pasaron; código web y contratos no cambiaron desde sus comprobaciones aprobadas.
- Verificación externa v2 satisfactoria 06:45:32 UTC. El siguiente intento, 06:46:19, recibió un 502 Proxy Error aun con los reintentos moderados. Se comprobó después por API que campo, original y valores válidos siguen disponibles; modo REAL sin sustitución. Tarea Windows sigue Running, reintento fijado a 07:01:19 UTC. No se afirma recuperación externa todavía; la prueba de recuperación controlada sí pasó.
- Captura auténtica `real-sentinel3-network-failure.jpg` muestra campo, antigüedad, fallo, último éxito y próximo intento. Verificador pasó después del fallo para los 44 productos y 34 originales/86.108.038 bytes; resumen 106.752 bytes y contadores coherentes. La fecha científica continúa 10/11/2026, no se actualizó por la consulta ni se ocultó la demora.

## Incremento 11V — recuperación automática y límite científico GWIS

- El planificador reintentó Sentinel-3 a las 07:01:36 UTC, después del vencimiento 07:01:19, y obtuvo `unchanged` a las 07:01:43 sin intervención ni nuevo force. Mismo SHA, fecha científica y último cambio (06:45:32); falla y recuperación originales conservadas en `refresh_recovery_evidence.json`. Capturas REAL de ambas situaciones; la tarea sigue activa.
- El proveedor GWIS publica TIFF monobanda Float32, no sólo imágenes de colores. Muestra inicial Pampa 16×16, ampliación 32×32 y vista mundial 360×180: acceso comprobado sin cuenta y sólo ~605 KB de evidencia original retenida. No se contó como integración por ese acceso.
- La vista mundial tiene 51.330 ceros, incluso sobre océano, nodata=None y máscara todo válido. No se distingue fondo de FWI=0. Un control de fondo blanco tampoco lo distingue. WCS expone otras capas, pero `ecmwf.fwi` responde CoverageNotDefined. Los recortes nominalmente alineados difieren en 192 celdas, máximo 3,09734: ciclo o remuestreo no resueltos, sin cotejo satisfactorio. No se inventó máscara ni se publicaron esos números como campo científico.
- Evidencia real en `data/samples/d11-gwis/README.md` y `evidence.json`. Se corrigió el bloqueo: tiempo real GWIS/EFFIS y archivo/estacionales EWDS son distribuciones diferentes. D11 necesita producto nativo con máscara, ciclo/validez y transformación acreditados, no una credencial ficticia para la URL pública. D18 sigue condicionado por producto regional/temporada.
- Verificador final pasó tras la recuperación: 44 productos, 25 fuentes, 34 originales / 86.108.038 bytes, resumen 106.752 bytes y referencias intactas. Se conservan instantáneas de las actualizaciones automáticas USGS/GDACS comprobadas por API. Código científico y web no cambiaron desde las suites aprobadas (106/24); sólo evidencia y descripción precisa de accesos. La matriz conserva los 48 IDs y todas las capacidades de los 31 fenómenos sin fingir cobertura completa.

## Incremento 11W — ERA5 estable mundial por ARCO público

- D08: se encontró y comprobó la distribución pública ARCO de Google Research, atribuida a C3S/ECMWF. HTTPS anónimo sin Google/CDS/cuenta/facturación. Una hora estable de temperatura del aire a 2 m: 30/06/2026 00 UTC, seleccionada desde `valid_time_stop`; no se usó ERA5T ni la fecha de publicación global como hora del dato.
- Bloque completo 721×1440 en K, comprimido 1.875.445 bytes, más ejes/metadatos. ZIP reproducible exacto de 1.892.564 bytes con URL/SHA/generación por activo; no GRIB original ni colección de petabytes. Doble decodificación C-Blosc1/numcodecs y C-Blosc2 coincidente byte a byte, con presupuesto de descompresión previo al codec. v3 es edición del store; formato Zarr 2 comprobado.
- Se detectó una distinción crítica de calendario: cobertura calificada desde 1940, pero eje CF reservado comienza en 1900. Índice real 1.108.824 y coordenada horaria nativa comprobados; no se calculó el índice desde `valid_time_start`. Latitud/longitud completas, unidades y calendario proleptic_gregorian verificados.
- Vista mundial 1° por stride 4 de centros del activo 0,25°, longitudes normalizadas/ordenadas. 64.800 celdas válidas, rango −68,63265…40,01577 °C en esta hora, cero ausentes; el decodificador conserva NaN como null. Centro −35,5°,−61,5°: 7,498193359375 °C por float/Decimal independientes. El ZIP conserva todos los valores ARCO pertinentes.
- Es archivo de reanálisis modelo/observaciones, no sensor, SST, LST ni forecast. Una hora no habilita serie/climatología, tendencia o detector térmico. No se asignó incertidumbre o habilidad por pasar software; sin ensemble/QA por celda descargados. Capacidad F02 conserva esa distinción; experimento SST sin promoción.
- Ingestión real repetida `unchanged`, último éxito 07:27:00 UTC. Trabajo semanal incorporado a la tarea Windows, reiniciada y Running. Fixture auténtico; pruebas de NaN, unidades alteradas, rechazo ERA5T, descompresión acotada, cambios científicos frente a actualización ajena de ERA5T, idempotencia/falla/recuperación. 110 pruebas API y contratos pasaron; código web no cambió desde 24 pruebas/build aprobados. Captura REAL `real-era5-arco.jpg`.
- 26 fuentes / 45 productos, 29 campos (tres calculados), un análisis descriptivo, sin aumento artificial de observaciones por las celdas. Verificador API/originales pasó: 35 activos / 88.000.602 bytes, resumen 110.161 bytes, referencias intactas. Almacén 218.180.923 bytes antes de otra actualización automática, dentro de 256 MB. Continúan las otras rutas públicas viables, sin asumir que credencial faltante bloquea todo un proveedor.

## Incremento 11X — tres percentiles GRACE asimilados globales

- D33: el archivo NASA/NDMC enlazado en Drought.gov publica NetCDF/TIFF sin cuenta. Se descargó un lote real global, edición 030 Catchment: agua subterránea somera, zona radicular y humedad superficial, todos percentiles (%), no humedad volumétrica ni nivel/altura de agua.
- NetCDF 2.170.345 bytes más tres TIFF; ZIP original compartido 4.855.802 bytes. 864.000 nodos y máscaras de cada variable coinciden exactamente entre h5py/NetCDF y rasterio/TIFF. TIFF Float32 con nodata −999, WGS84 y paso 0,25°; latitud NetCDF ascendente invertida para cotejar. No se descargó otra vez el mismo archivo para distintos fenómenos.
- Referencia CF nativa 10/11/2026 00 UTC coincide con begin_date; cell_methods=time: point y time_increment=7. No se inventó media semanal ni emisión UTC desde historia de creación sin zona/Last-Modified. Input nativo termina en 2019-08: se conserva la advertencia de que no acredita fecha de última observación GRACE asimilada. Referencia global 1948–2012 atribuida a Drought.gov; no se recalculó ni se atribuyó una climatología no embebida al archivo.
- Producto terrestre −60…90°, océano/Antártida ausentes y Groenlandia enmascarada. Vista 360×150 a 1° por vecino más cercano con empate sur/oeste explícito, sin promediar percentiles. Cada capa tiene 14.556 valores visuales y 39.444 ausentes; ceros válidos se conservan. Valores completos en originales. Paleta/leyenda invertidas coherentemente: rojo bajo percentil, azul alto; no probabilidad de evento ni estado saludable.
- F11/F14/F16 reciben indicadores modelados parciales con ámbito/fecha/referencia. SMAP observado sigue bloqueado y no se sustituye por este producto. El forecast CONUS 30/60/90 días no queda integrado por las capas globales. No hay tendencia nueva ni validación predictiva por software.
- Ingestión repetida `unchanged`, último éxito 07:46:45 UTC; revisión diaria de publicación semanal en tarea Windows reiniciada/Running. Pruebas con archivo auténtico: unidades/calendario alterados rechazados, desacuerdo TIFF impide publicar, cero preservado, activo compartido, idempotencia y falla/recuperación. 114 pruebas API, 25 web, contratos y build aprobados. Captura REAL `real-grace-groundwater.jpg`; leyenda con unidad larga se separa sin superposición.
- 27 fuentes / 48 productos, 32 campos (tres calculados) y un análisis descriptivo, sin inflar observaciones con celdas/modelos. Verificador de API/originales pasó: 36 activos / 92.856.404 bytes, resumen 120.918 bytes, referencias intactas. Almacén medido 225.803.085 bytes dentro de 256 MB; límites de retención conservan el válido ante presión de almacenamiento. Continúan accesos numéricos públicos viables.
- Durante la pausa del usuario se ejecutaron actualizaciones reales de FIRMS, USGS, OAF, Kp/forecast e IFS. Comprobación posterior: 9.228 observaciones, 36 originales actuales / 91.889.336 bytes, resumen 120.906 bytes; todos consultables y referencias intactas. Kp conserva el válido ante un fallo DNS y tiene reintento. La actualización IFS expuso que sus derivados no vencen al cambiar las entradas: se corrige en el siguiente incremento, junto con el margen de almacenamiento tras medir recursos.

## Incremento 11Y — cálculos dependientes de revisiones y margen medido

- Se corrigió la demora entre una nueva corrida IFS y sus campos físicos derivados. Dependencias fijas IFS y RAPID, sin sistema de plugins: hashes de cada entrada `current.json` persistida, no de su última descarga. Un nuevo original/corrección activa cálculo en el mismo escaneo o el siguiente, aun sin vencer la cadencia de respaldo.
- Checkpoint de intento se guarda antes de I/O y checkpoint satisfactorio sólo al completar. Entrada fallida/ausente idéntica respeta 15 minutos; entrada nueva permite un intento. Detecta publicación sobreviviente a un reinicio aunque falte el éxito del trabajo fuente. Tres pruebas cubren cambio/no cambio, mismo escaneo, reinicio, fallo, ausencia y reparación; también se comprobó rechazo por presupuesto sin alterar el producto válido.
- Comprobación real sin force: se reinició la tarea Windows autorizada; el watcher recalculó IFS a las 10:54:05–10:54:07 UTC desde los originales ya descargados. Viento/VPD/RH ahora usan inicialización 14/11 00 UTC y validez 15/11 00 UTC. Todos los SHA de entradas coinciden con los actuales; comprobaciones independientes GRIB/Decimal pasaron (viento 5,109304929269748 m/s, VPD 0,10692404773459963 kPa, RH 85,36422308744842 % en sus respectivos centros de prueba). RAPID dio unchanged sin duplicar activo. Evidencia `refresh_dependency_evidence.json`.
- Medidos 236.336.230 bytes de almacén y 177.279.176.704 bytes libres en E:, límite predeterminado ampliado de 256 a 512 MB; siguen cuatro revisiones y rango configurable 32 MB–2 GB. No se borró historia ni se amplió a colecciones mundiales completas. Configuración/documentación coherentes.
- 117 pruebas API, contratos regenerados/comprobados y build web con TypeScript pasaron; web conserva sus 25 pruebas aprobadas. Verificador API/originales: 48 productos, 27 fuentes, 36 activos actuales / 92.049.005 bytes, resumen 120.910 bytes. Actualización automática reciente FIRMS/USGS/Kp explica 10.477 observaciones; no creció el conteo por campos calculados. Tarea Running, referencias intactas y experimento SST sin promoción.

## Incremento 11Z — climatología mundial IMERG Final V07B

- Se comprobó una distribución numérica pública NASA de D01, sin cuenta: un único campo de precipitación media anual, junio 2000–mayo 2023, mm/año. Es referencia histórica de Final V07B, no colección Early reciente ni lluvia futura. F01 mantiene observación actual bloqueada; no se fabrica anomalía/detector a partir de esta capa.
- NetCDF ZIP 17.903.213 bytes y TIFF ZIP 26.383.365 bytes, ~44,3 MB en total; no se descargaron los archivos mensuales/diarios de cientos de MB/GB. Todos los 6.480.000 nodos y máscaras coinciden entre h5py/rasterio. Relleno −9999,9, 24.418 ausentes nativos, cero válido conservado. Vista 1° por submuestreo explícito de centros 0,1°, desplazamiento −0,05° al sur/oeste; 360 ausentes. Centro nativo −35,55°,−61,55°: 1.020,9791870117188 mm/año.
- Se detectaron defectos reales del proveedor: título NetCDF con literal runname[run] y WorldFile con *** en el paso vertical. Se conservaron sin corregir en los originales/manifiesto. WorldFile excluido de georreferenciación; CRS/transform TIFF y ejes CF sí coinciden y todas las celdas cotejan tras transponer/invertir. TIFF sin tag nodata usa la máscara explícita NetCDF/documentación, sin confundir cero con ausencia. Primer intento automático rechazó correctamente el WorldFile; tras resolver el método la ingestión real finalizó 11:12:53 UTC.
- Campo persistido/servido/visible en REAL, cámara amplia y período histórico. Reprocesamiento local de metadatos reutilizó el mismo activo, sin nueva descarga: stored y luego unchanged, sin duplicar bytes. Pruebas con ambos ZIP auténticos verifican unidades alteradas, desacuerdo nativo, máscara, cero, idempotencia y falla/recuperación. 120 pruebas API pasaron; siete pruebas IMERG/GRACE repetidas tras extraer su contenedor común y separar construcción de producto de acceso. 25 web/build/TypeScript aprobados. Captura `real-imerg-climatology.jpg`.
- Revisión mensual de edición fija en tarea Windows reiniciada y Running; conserva período/creación y bloquea cambios de edición no revisados. 49 productos, 28 fuentes, 33 campos; siguen 10.477 observaciones y cero señales calculadas. Verificador: 37 originales / 136.337.515 bytes, resumen 124.410 bytes y referencias intactas. El dato histórico no se rejuvenece por descargarlo en 2026.
- Se examinaron otras vías sin inflar conexiones: GRACE forecast CONUS sólo PNG/PDF en el directorio revisado; GLDAS GDS HTTP 410; NASA MODIS PFEG falló conexión, otras réplicas retiradas/ambiguas. Vibrio AOML sí tiene variable numérica experimental, pero Risk Level/To be Completed no define especie ni significado suficiente para equipararla al producto regional del catálogo. Metadatos auténticos en `data/samples/access-alternatives/`; ningún riesgo/probabilidad inventado. Credenciales se comprobaron por presencia, nunca se imprimieron secretos: siguen ausentes.

## Incremento 11AA — contornos glaciares históricos y acceso al inspector

- D26: se siguió el índice público OGGM/GLIMS y se descargó sólo el ZIP Andes del Sur RGI 6.0: 25.220.396 bytes, cinco miembros/50.594.728 bytes expandidos. No requiere cuenta. Se identifica como edición anterior de 2017, sin renombrarla RGI7, sustituir atributos de Alaska o omitir que RGI7 es la versión recomendada y sus huellas oficiales siguen pendientes.
- 38 glaciares Status=0 con Area≥50 km² y punto representativo en [-74,5,-72] × [-51,-48]. Selección cartográfica explícita, no detector ni toda Patagonia; límites completos sin simplificar/recortar. 23.488 vértices y anillos interiores conservados. Seis contactos de anillo se normalizan sólo para dibujar, con conservación relativa de área planar 1e-10/bbox 1e-10°. Función compartida con HydroATLAS; una reparación material se rechaza y el original permanece intacto.
- Todos los IDs/áreas de los 15.908 registros regionales coinciden DBF/CSV de hipsometría; suma 29.429,080 km² y conteo coinciden con tabla 6 del informe técnico RGI6. Cada contorno seleccionado se cotejó además con SHP/SHX binarios independientes, incluidas todas sus coordenadas. PRJ WGS84/CRC32 comprobados. Perito Moreno RGI60-17.00312 tiene 263,322 km² nativos; BgnDate=20009999/EndDate=20030531 conservados como época de imágenes, sin inventar UTC.
- Ingestión automática real stored a las 11:24:16 UTC. Trabajo mensual activado en la tarea Windows reiniciada/Running. API, original, 38 regiones y tabla del inspector disponibles. Pruebas con ZIP auténtico: desacuerdo CSV/DBF, CRS inválido, rechazo de topología material, idempotencia y falla/recuperación; GLOF permanece bloqueado. Se corrigieron expectativas heredadas de D01: fuente conectada para climatología, observación reciente y endpoint legado siguen bloqueados y el asistente nombra las variables exactas.
- La comprobación visual encontró que 250 km de altura mínima impedía inspeccionar un contorno pequeño. Se permite 25 km para encuadre/zoom explícitos; preset REAL amplio de 13,2 Mm permanece igual. El registro seleccionado pasa al inicio del inspector y reinicia scroll al cambiar; atributos nativos desplegables. Capturas auténticas `real-rgi60-wide.jpg`, `real-rgi60-perito-moreno.jpg` y `real-rgi60-inspector-900x650.jpg`: área/atributos accesibles, sin overflow horizontal (900 px de documento/viewport), controles sin superposición. Se restauró tamaño normal y vista amplia al acabar la prueba.
- 124 pruebas API, 27 web, contratos/build/TypeScript aprobados. Verificador API/originales: 50 productos, 28 fuentes, 38 activos actuales / 161.557.911 bytes y resumen 128.170 bytes. Siguen 10.477 observaciones, 2.475 registros históricos y cero eventos calculados; geometrías de contexto no inflan esos conteos. Almacén 313.057.102 bytes dentro de 512 MB. El lock rechazó correctamente una verificación durante actualización; tras finalizar pasó. Nueva revisión automática LHASA retenida, referencias intactas y SST sin promoción.

## Incremento 11AB — atributos glaciares mundiales y símbolos legibles

- D26: acceso anónimo comprobado al CSV global RGI7 distribuido por OGGM, 74.734.943 bytes. Los 274.531 IDs son únicos, coordenadas/áreas válidas y las sumas Decimal de las 19 regiones coinciden con las estadísticas publicadas independientemente por RGI: 706.744,049467246904673 km² nativos. El ZIP sin pérdida de 24.903.281 bytes conserva todos los atributos, comparación oficial y manifiesto; no se descargaron geometrías mundiales.
- Vista acotada de 1.851 puntos representativos nativos de glaciares ≥50 km², 16 regiones con selección, extensión que declara cruce del antimeridiano. No son centroides, celdas rasterizadas, eventos ni totalidad del inventario dibujada. Glaciares menores permanecen en el original completo. Double Glacier RGI2000-v7.0-G-01-01334 conserva 132,44631153716037 km². Época fuente sin zona queda literal y tiempo UTC null; RGI6/7 no se comparan como tendencia.
- Ingestión automática real 11:47:39–11:48:02 UTC, revisión mensual activada. Tres pruebas con archivo auténtico verifican estadísticas independientes alteradas, coordenada inválida, activo sin pérdida, repetición idempotente y falla/recuperación sin perder el válido. El overlay operativo ahora detecta revisiones sin reiniciar la API y se escribe atómicamente; una prueba comprueba ese cambio de estado.
- La verificación visual halló etiquetas polares superpuestas. Se priorizan símbolos en pantalla mediante sus rectángulos y profundidad, manteniendo seleccionado primero y evitando controles. Esto sólo oculta símbolos que se taparían: no fusiona registros, cambia conteos geográficos ni inventa densidad. Todos siguen en la tabla/inspector. Dos pruebas comprueban solapamiento, prioridad, límite de pantalla y conservación de entradas.
- Capturas REAL `real-rgi7-global-wide.jpg` y `real-rgi7-selected-900x650.jpg`: vista mundial sin acercamiento automático, consulta por ID, selección accesible al inicio del inspector y documento de 900 px sin desborde. Tamaño normal restaurado. 128 pruebas API y 29 web, contratos/TypeScript/build aprobados. Verificador final pasó: 51 productos, 28 fuentes, 39 originales actuales / 186.461.192 bytes y resumen 132.045 bytes; 10.475 observaciones, 2.475 históricos y cero eventos calculados. Referencias originales intactas, GLOF pendiente y SST experimental.

## Incremento 11AC — Sentinel-2 óptico real y NDVI reproducible

- Se descubrió la distribución pública Earth Search/Element84 C1, sin cuenta AWS/CDSE; el XML 401 de otra ruta no bloquea esta vía. Escena Sentinel-2B 11/11/2026 14:12:34.012553 UTC, baseline05.13, producto SAFE/versión/SHA completos. Sensing XML y STAC coinciden a 1ms; generación no se transforma en emisión de forecast.
- Primera ventana mayor rechazada por presupuesto. Tras medir, ventana Pampa ~7×7km: 730×666 DN por banda a10m, SCL20m; cada activo limitado a8MB/16 rangos de512KiB. Descarga automática real 12:19:50–12:20:28 UTC, 6.291.456 bytes de rangos y XML/STAC; un ZIP compartido de6.448.096B para rojo/NIR/NDVI. No archivos completos de cientos de MB ni redescargas por fenómeno.
- XML/TIFF/STAC coinciden en CRS32720, forma/transformación y rho=(DN−1000)/10000; offset aplicado una vez, sin asumir harmonización pre-C1. Cada DN de las tres ventanas se cotejó rasterio frente a lector independiente struct/zlib/predictor del primer IFD nativo. Vista80×60 WGS84 a0,001° por píxel contenedor, sin overviews AVERAGE o interpolar huecos. Todos los valores nativos pertinentes permanecen reproducibles desde rangos retenidos.
- Sólo SCL4/5, DN0 ausente; 720 celdas visuales enmascaradas. Reflectancias negativas recuperadas conservadas; NDVI limita componentes≥0/suma>0 y tiene721 ausentes. Fórmula/parámetros/versión/entradasSHA documentados; NDVI0,3320825515947467 coincide con Decimal40 desde DN. Es indicador espectral local de una pasada, no tendencia, estrés confirmado, humedad o probabilidad. F16 parcial, modelos sin promoción.
- Repetición real 12:22:50 UTC unchanged: mismo ítem y lote completo, sólo descubrimiento, sin descargar/cambiar activo, fecha de pasada o recuperación original. Inspector lo llama consulta satisfactoria, no descarga/cálculo nuevos. Cuatro pruebas con fixture auténtico cubren valores/QA/negativos/UTC/CRS, metadatos incompatibles/harmonización, dominio, idempotencia y falla/recuperación; 132 API, 29 web, contratos/TypeScript/build pasaron.
- Capturas REAL `real-sentinel2-wide.jpg`, `real-sentinel2-ndvi.jpg`, `real-sentinel2-900x650.jpg`: selección mantiene vista amplia; sólo Encuadrar cobertura acerca. Inspector900×650 accesible y documento900px sin overflow; tamaño/preset amplio restaurados. Verificador pasó:54 productos/28fuentes,36campos/4calculados, dos productos de indicadores calculados (NDVI y RAPID, se solapan con campos),40activos actuales/192.919.013B,resumen144.364B. Siguen10.475observaciones,2.475históricos,dosregistrosindicadoresimportados,ceroeventos. Referencias intactas; almacén351.792.191B/512MB.

## Incremento 11AD — NASA OceanColor histórico mundial

- Se encontró otra colección pública NOAA/PIFSC con identidad nativa NASA/GSFC OBPG, Aqua/MODIS, OCI L3 Mapped, DOI y versión2018.1QLP. Es distinta de las réplicas ambiguas o retiradas examinadas antes. Último campo31/05/2022 12UTC, archivo diario A2022151; se integra como histórico y no acredita NASA reciente, R2022 Science Quality o detección HAB.
- Sólo267.976B de NetCDF, 360×180 centros cada24 de la malla4,64km, y dos CSV de cotejo; ZIP280.008B con descubrimiento/URL/manifiesto. Todos los ejes/valores/NaN coinciden entre decodificador ClassicNetCdf/struct y netCDF4 independiente. Longitudes0…360 reordenadas con sus valores a WGS84; comportamiento compartido opcional sin cambiar CRW/Sentinel3.
- 60.677 ausentes,4.123 centros válidos, rango0,0174087677…37,1842269897mg/m³; valor mayor que colorbar30 conservado. Máscara NaN/rango nativo0,001…100, sin inventar flags L2 por celda desde su listado documental. Un máximo y un ausente coinciden con CSV independiente, incluidas unidades/fecha/coordenadas. Se corrigió una comprobación inicialmente demasiado estricta: CSV emite decimales cortos Float32 y se coteja exactamente a esa precisión nativa, sin tolerancias geográficas arbitrarias.
- Ingestión real16:10:47UTC y revisión automática16:12:57 unchanged. Metadatos de presentación corregidos posteriormente sin modificar valores/fecha; nueva revisión histórica acotada. Revisión mensual de edición fija; cambio inesperado de fecha/versión exige calificación y conserva válido. Tres pruebas con archivo auténtico cubren unidades/versión/tiempo/WGS84/máscara, idempotencia y falla/recuperación; suite completa135API pasó. Web/contratos no cambiaron y conservan29pruebas/build aprobados.
- El verificador detectó API404: el proceso original de noviembre13 seguía sirviendo rutas anteriores sin recarga. Se identificaron PID/argumentos antes de detener sólo ese proceso Earth Echo; se inició API actual en localhost con recarga limitada a src, ventana oculta. /v1/products y todos los originales pasaron luego. Tarea de descargas independiente continúa Running; no se perdió ningún dato ni se cambió REAL a DEMO.
- Captura auténtica `real-nasa-aqua-archive.jpg`, globo amplio/fecha2022/leyenda log y huecos visibles, un canvas y sin overflow1280px. Verificador final:55productos/29fuentes,37campos/4calculados,41activos actuales/193.199.021B,resumen147.957B. Observaciones10.476,históricos2.475,dosindicadoresimportados,ceroeventos; campo histórico no infla registros. Referencias intactas; retención automática FIRMS mantuvo cuatro revisiones y redujo almacenamiento. Continúa pronóstico oficial ENSO numérico como próximo trabajo viable.

## Incremento 11AE — pronósticos oficiales ENSO/RONI

- D48: se siguieron los enlaces del boletín CPC a tres tablas HTML numéricas oficiales, sin imágenes/OCR o cuenta. Edición noviembre 2026, RONI ERSSTv6/base 1991–2020. No se mezclan con ONI o pronóstico IRI tradicional. issued_at/initialized_at=null porque no se proporciona día/hora UTC de las tablas; inicio de validez civil no es emisión.
- 27 probabilidades de fase, 81 de intensidad y 63 valores de percentiles, para nueve trimestres solapados OND 2026…JJA 2027. Ventanas UTC [01/10/2026,01/09/2027), incluidas estaciones ya iniciadas. FMA: fase 0/2/98%; DJF: 79% de RONI≥2°C; OND p50=2,5°C y JJA p50=−0,25°C. Percentiles sin probabilidad de evento; cero publicado aproximado conservado, no ausente.
- Todos los números cotejados HTMLParser frente a extracción independiente de TD. Sumas de cuatro clases frías/cuatro cálidas/neutral coinciden exactamente con fase en cada estación, total 100% sin renormalización. Percentiles monotónicos, meses/umbrales/edición/definición comprobados; mezcla o discrepancia rechaza actualización. Un ZIP compartido de 31.348 B conserva cuatro HTML, SHA/manifiesto.
- Revisión automática diaria, primer éxito programado 16:31:10 UTC unchanged. Retención específica de 24 revisiones para estas tres perspectivas por su horizonte de nueve estaciones; mantiene presupuesto global 512 MB y eliminación sólo de activos sin referencias. Cuatro pruebas auténticas verifican ventanas/definiciones/números, incoherencias, idempotencia/falla/recuperación y retención compartida. 139 API, 31 web, contratos/TypeScript/build pasaron; no valida habilidad predictiva.
- Inspector existente reutilizado para tablas, sin pines ENSO. Inicio de validez, dato y emisión se etiquetan explícitamente; base temporal accesible. A 900×650, fase cabe en 324 px e intensidad desplaza 434 dentro de 309 px, por teclado comprobado (scrollLeft=40), sin overflow documental. Capturas REAL `real-cpc-enso-phase.jpg`, `real-cpc-enso-phase-900x650.jpg`, `real-cpc-enso-strength-900x650.jpg`; tamaño normal restaurado y globo amplio.
- Verificador: 58 productos / 29 fuentes, 42 originales actuales / 193.230.369 B, resumen 161.036 B. Siguen 37 campos, cuatro calculados, dos productos de indicadores calculados, 10.476 observaciones, 2.475 históricos y cero eventos. Almacén 347.525.338 B; referencias intactas. F17 recibe pronóstico externo parcial definido, SST sigue experimental. El HTML RONI retenido contiene además historia observada que se integra a continuación con decodificación propia.

## Incremento 11AF — historia RONI compatible y activo reutilizado

- Se decodificó la historia publicada ERSSTv6/base 1991–2020 de la misma página retenida como definición del pronóstico, sin otra descarga/activo inicial. 77 años centrales 1950–2026, 924 posiciones: 921 valores y tres temporadas no publicadas en null. MAM 2026 publica 0,0 válido; ASO 2026=2,0°C es último trimestre. Se mantienen ONI y RONI separados, sin diagnóstico automático de episodio, regresión o probabilidad.
- Año nativo del mes central convertido explícitamente a intervalo civil UTC: DJF 1950=[01/12/1949,01/03/1950), ASO 2026=[01/08/2026,01/11/2026). No medianoche de una emisión inventada. Últimos valores son estimaciones revisables hasta dos meses, según CPC. No son muestras mensuales independientes.
- Tabla visible con ID heredado roni-v5-table2: versión científica tomada del encabezado/definición v6, no del nombre HTML. La tabla oculta está vacía. El cierre opcional del último tr antes de tbody se maneja correctamente para conservar 2026; todos los años/valores/vacíos se cotejaron contra extracción independiente del HTML. Años duplicados, versión distinta, valor inválido o trimestre no finalizado se rechazan.
- Producto inicial procesado localmente desde el ZIP compartido: recuperación original 16:27:01 UTC, ingestión 16:45:49. Revisión conjunta externa 16:47:55 unchanged; descripciones aclaradas en revisión posterior 16:50:58. Cuatro productos comparten las cuatro lecturas del mismo trabajo diario, con checksums científicos propios. Historia conserva cuatro revisiones y las tres perspectivas,24, bajo presupuesto global.
- Tres pruebas auténticas adicionales y prueba visual evitan perder último año, rellenar ausencias, fechar mal DJF o mostrar historia como forecast. Suite completa142 API y32 web, contratos/TypeScript/build pasaron. Captura REAL `real-roni-history.jpg`: gráfico histórico, huecos conservados, un canvas y documento1280px sin desborde. Sin tabla de pronóstico en esa selección.
- Verificador:59 productos/29 fuentes, mismos42 originales actuales/193.230.369 B (ningún activo duplicado por la historia), 3.399 registros históricos incluidos tres null, 10.476 observaciones y cero eventos. Resumen~165KB; almacén~350MB. Referencias intactas y SST sigue experimental. Se examina ahora la alternativa de acceso estacional sin cuenta antes de dar por imprescindible CDS.

## Incremento 11AG — SEAS5 mensual real por distribución pública

- D09: acceso sin cuenta a Open-Meteo para uso local no comercial, separado del cliente/dataset CDS C3S. `models=ecmwf_seas5` explícito evita la mezcla predeterminada EC46. Cuatro series de medias de ensemble, temperatura a2m y precipitación total mensual, para una celda nativa O320 Pampa y otra Amazonía; siete meses noviembre2026…mayo2027. No cobertura regional/mundial descargada, miembros individuales, probabilidades o calibración.
- Inicialización01/11/2026 00UTC y disponibilidad del dominio mensual05/11 12:06UTC separadas de recuperación/emisión; emisión ECMWF no publicada queda null. Metadata mensual idéntica antes/después, espera≥10min desde modificación. La respuesta de valores no tiene ID de corrida: esa limitación de asociación temporal se declara, sin fingir una corrida individual acreditada por GRIB.
- Todos los28 números, fechas, unidades, coordenadas/elevación y ausencias cotejados JSON/CSV. Celda O320 verificada además con raíces de Legendre640 y estructura de anillos, tolerancia de precisión Float32<4e−5°. Pampa noviembre19,2°C y108,5mm. La precipitación ya integra tprate×segundos reales del mes×1000 en el proveedor: no mm/día ni doble conversión. Meses de28/29/30/31d tratados por calendario; null y cero diferentes.
- Un ZIP compartido2.802B para cuatro productos, URLs/SHA/método versionados. Ingestión real17:18:07UTC stored y repetición17:23:53 unchanged; recuperación original y cuatro revisiones iniciales conservadas. Tarea Windows reiniciada Running; se marcó sólo este trabajo vencido una vez para comprobar tick autónomo:17:27:35–17:27:41 unchanged y siguiente intento15/11 17:27:41UTC. Fallo/recuperación controlados no pierden datos ni cambian a demo. Cuota: cuatro peticiones pequeñas por revisión diaria, proveedor secuencial con reintentos comunes.
- Gráfico e inspector reutilizados, leyenda sin Observado cuando toda la serie es forecast, inicialización explícita, atribución enlazada junto a los datos; no pines de celdas ni acercamiento. Capturas REAL `real-seas5-monthly.jpg` y `real-seas5-monthly-900x650.jpg`: inspector340px, documento900px, un canvas. Se recuperó Vite local detenido, sin cambiar red/puerto o agregar otro servidor; tamaño normal restaurado.
- 146 pruebas API,34 web, contratos/TypeScript/build aprobados. Una nueva prueba visual detectó que los tests del inspector compartían DOM: limpieza explícita entre casos, sin alterar el comportamiento del producto. Verificador API/originales pasó:63 productos/30fuentes,43 activos actuales/193.233.171B,resumen181.877B;37campos/4calculados,10.476observaciones,3.399históricos,ceroeventos calculados. Almacén344.029.401B/512MB, retención automática FIRMS/feeds actualizados. Referencias intactas; SST experimental. Sigue la calificación pública GloFAS, CAMS y física Marine antes de asumir imprescindibles sus cuentas.

## Incremento 11AH — GloFAS distribuido con alcance y época explícitos

- D10: se calificó la distribución pública Open-Meteo, sin cuenta para uso local no comercial. Dos celdas0,05° en entorno Rosario/Manaus, primeros siete plazos diarios del dominio;51miembros00control+01…50 y medias,728valores/máscaras cotejados JSON/CSV. No se les atribuye estación de aforo, río principal, cuenca completa o descarga mundial. La media2,3m³/s de Manaus no se llama caudal del Amazonas.
- Se revisó código oficial y se corrigió identificador API `forecast_v4`, distinto de dominio metadata`glofas_forecast_v4`. El producto rolling puede completar huecos con intermedio/estacional; no expone ID de corrida por valor o versión operativa menor. Se conserva familia v4 y referencia de inicialización/disponibilidad en atributos; initialized_at/issued_at=null, sin fingir corrida aislada4.0/4.1. Limitar a primeros7 días y cotejar meta antes/después no elimina esa incertidumbre, declarada en API/inspector/matriz.
- Definición primaria CEMS dis24 verificada: tiempo nativo es **fin** de las24h promediadas. Etiqueta15/11 corresponde a[14/11 00UTC,15/11 00UTC), conjunto[14/11,21/11). m³/s, no volumen ni profundidad. Media51 recalculada con Decimal y cota documentada de redondeo/suma Float32; primera Rosario30.973,22/control30.973,21, diferencia preservada. Todos los miembros siguen accesibles en API/original; gráfico sólo siete medias, sin concatenarlos ni generar probabilidades.
- Al pedir elevation=nan, JSON omite elevación y CSV publicaNaN. Dos intentos de ingestión rechazaron correctamente esa diferencia estructural; tras conservar ambas como null pasó el cotejo local y la descarga real17:39:19UTC stored. Ensemble incompleto queda missing, incluso si proveedor publica media parcial, cuyo literal se retiene en atributos; cero físico válido. Un ZIP5.541B compartido y dos revisiones iniciales, sin duplicar activos por fenómeno.
- Actualizador existente reiniciado Running. Se venció sólo ese trabajo una vez para comprobar tick autónomo17:43:02–17:43:08UTC unchanged, siguiente15/11 17:43:08. Cinco pruebas auténticas nuevas cubren media alterada en ambos formatos, unidades, época, coordenadas, corrida cambiante, máscara, idempotencia y fallo/recuperación. Helpers exclusivamente de transporte compartidos con SEAS5; decodificadores científicos siguen separados.
- Capturas REAL `real-glofas-discharge.jpg` y `real-glofas-discharge-900x650.jpg`: selección mantiene globo amplio y atribución; inspector340px/documento900px sin overflow. Se distinguieron fechas diarias y se dejó espacio a cifras grandes: extremo derecho del texto996,1px y primer punto1005,6px, sin superposición. Se reducen etiquetas visibles, nunca muestras. Tamaño normal restaurado.
- 151 API,35 web, contratos/TypeScript/build aprobados. Verificador65productos/31fuentes,44activos actuales/193.238.712B,resumen190.804B;37campos/4calculados,10.476observaciones,3.399históricos y ceroeventos calculados. Almacén344.096.698B/512MB. F12 recibe forecast parcial de caudal; aforos, umbrales/probabilidad/profundidad siguen no disponibles. Referencias originales intactas, SST experimental. Continúa CAMS numérico público con superficie y columna separadas.

## Incremento 11AI — composición atmosférica CAMS mundial

- D12: muestra pública real de una celda Sahara cotejada antes de ampliar; primera franja90centros midió34.701B JSON/6.013B CSV. Luego450centros mundiales en cinco bloques, cuatro campos y un plazo+24h: PM2,5/PM10 superficiales, fracción de polvo aermr06 yAOD550 en columna. Malla del distribuidor0,4°, vista explícita12° (30×15centros), sin promediar, interpolar espacialmente, conservar extremos entre centros o convertir celdas en eventos. Todos los1800valores/máscaras/coordenadas cotejados JSON/CSV y retícula independiente.
- Se revisó código oficial del distribuidor y parámetro ECMWF210006: dust mapea sólo fracción0,9–20μm, nivel137, con conversión de densidad fija1,223803kg/m³. Se etiqueta esa aproximación, no polvo total/PM10 equivalente. PM ya viene convertido kg/m³×1e9; AOD550 adimensional de toda la columna, unidad API vacía normalizada a1. Sin doble conversión, flags inventados o AQI. Cero válido preservado; edición sin ausentes. Rango de vista PM2,5=0…120,6;PM10=0…175,6;polvo=0…249μg/m³;AOD=0,02…1,24, no máximos de toda la malla nativa.
- `domains=cams_global` evita mezcla europea; las variables solicitadas no pertenecen al producto de gases invernadero. Plazo15/11/2026 00UTC, inicialización del dominio14/11 00UTC, disponibilidad09:45:18, emisión/ciclo químico no publicados. Metadata estable antes/después y antigüedad≥10min; API sin ID de corrida por valor, asociación temporal inferida declarada. Plazo+24h alineado a3h evita interpolación temporal de polvo; PM/AOD del distribuidor horarios. No habilidad predictiva local acreditada.
- Ingestión autónoma real17:57:36–18:01:42UTC stored. Un ZIP23.145B/12archivos compartido por cuatro productos, método/URLs/SHA y atribución accesibles. Repetición18:03:16 unchanged con sólo dos consultas metadata: original y fecha de recuperación conservados, decodificación/cotejo repetidos sin descargar450centros. En fallo conserva válido/REAL. Cuatro pruebas auténticas nuevas cubren georreferenciación, fechas/unidades, formatos, cambios de corrida, máscara/cero, negativos, deduplicación, actualización por metadata y fallo/recuperación.
- Presupuesto persistente Open-Meteo compartido con SEAS5/GloFAS: reserva antes deI/O ponderada por ubicaciones/variables/duración y dos intentos posibles;500/min,4500/h,9000/día, metadata exenta. Bloques90, espera individual≤60s y timeoutCAMS420s ajustable30…600. Reserva sobrevive reinicios/fallas, se poda a24h y no se devuelve al fallar. Dos pruebas comprueban ventanas, persistencia, cuotas horaria/diaria y reloj que retrocede. Estado de cuota ignorado porGit, sin secretos ni otro servicio.
- La cuota del revisor automático impidió temporalmente reiniciar tarea/verificar; esas acciones no se ejecutaron entonces. Tras restablecerse, se reinició la tarea existente, estadoRunning, y pasó el verificador. No se omitió revisión ni se aceptaron contratos/cuentas/pagos. Capturas auténticas `real-cams-pm25-global.jpg`, `real-cams-aod-global.jpg` y `real-cams-aod-900x650.jpg`: globo amplio, atribución visible, inspector340px, documento900px/un canvas; tamaño normal restaurado. El control del navegador se recuperó reinicializando sólo su sesión de herramientas tras la pausa.
- 157 API,35 web, contratos/TypeScript/build aprobados. Verificador69productos/32fuentes,45activos actuales/193.397.171B,resumen214.355B;41campos/4calculados,11.029observaciones,3.399históricos y ceroeventos calculados. Almacén347.764.039B/512MB. Cambios automáticos FIRMS/GDACS/USGS/Kp explican evolución de registros/bytes, no los camposCAMS. Referencias intactas, SST experimental. Continúa física oceánica Copernicus Marine por alternativa pública, cuya identidad numérica debe comprobarse antes de declarar D14 conectado.

## Incremento 11AJ — física oceánica SMOC nativa y dos normas

- D14: acceso anónimo HEAD/Range a NetCDF CMEMS nativo, no imágenes ni broker. Primero Caribe73×73centros, luego los mismos cuatro chunks permiten cuadrante5–90°N/180–0°O sin nueva descarga científica: vista180×85 cada12centros1/12°. Cuatro componentes utotal/vtotal yuo/vo separan total(euleriana+oleaje+marea) de euleriana. m/s, profundidad Float32 0,494025m;10.875centros válidos/4.425missing por campo. Cero/negativos válidos, sin flags adicionales ni extremos entre centros garantizados.
- Todos los8.812.800Float32 retenidos cotejados bit a bit: h5py frente a chunks crudos zlib/deshacer shuffle. Ejes CF completos con fórmula1/12°, sin desplazamiento de media celda; tiempos1950/gregorian cotejados timedelta/netCDF4. Punto nativo(-88°,18°)utotal−0,1220703125; centro visible(-86,5°,18,5°)−0,3271484375m/s. El primer punto elegido para test en(-88,5°,18,5°) era tierra/relleno: se conserva null y se agregó cotejo del relleno, sin reemplazar por cero.
- Fecha CF15/11/2026 00:30UTC de media horaria, sin time_bounds. Inicialización/emisión null: R20261114 sólo identifica día de producción, Last-Modified sólo distribución. Interfaz/timeline usan «Fecha de validez» para coordenada sin extremos acreditados. No se inventa intervalo. Dos normas calculadas fuera de UI, sqrt(mean(u)²+mean(v)²), máscara conjunta/cero válido y cotejo Decimal50; no media de rapidez instantánea ni modelo entrenado. D14 no habilita por sí sola HAB, oxígeno, Vibrio, transporteAMOC, trayectorias o inundación costera.
- ZIP compartido8.681.591B/68bloques/8.858.558B de rangos necesarios de un objeto922.430.398B. ETag multipart fuerte con If-Match conserva versión, sin afirmar SHA del archivo completo. Primer intento ocho componentes alcanzó120s: sólo cuatro quedaron calificadas; después de medir se asignó240s/16MiB/128peticiones a esta ruta y timeouttrabajo300s ajustable30…600. No descarga mundial/3D completa ni marea/Stokes numéricos acreditados. Original consolidado21:29:14UTC, publicación autónoma21:44:34–21:44:39 stored; repetición real21:57:43–21:57:47 unchanged con sólo HEAD, misma recuperación/ZIP y sin revisiones duplicadas.
- Revisión diaria bajo exclusión/retención comunes, falla/reinicio conservan válido/REAL; cuenta Marine sólo para otras distribuciones. TareaWindows reiniciada Running. Ocho pruebas auténticas nuevas cubren datos/ejes/época/máscara, norma, cambios de unidad/escala/calendario/profundidad/versión, deduplicación y falla/recuperación. Suite165API/36web, contratos/TypeScript/build aprobados. Capturas REAL `real-smoc-native-u.jpg`, `real-smoc-native-norm.jpg`, `real-smoc-native-900x650.jpg`: globo amplio, inspector340px/documento900px/un canvas, sin pines de celdas ni acercamiento automático; tamaño normal restaurado.
- Verificador75productos/33fuentes,46activos actuales/202.078.762B,resumen240.880B;47campos/6calculados,11.029observaciones,3.399históricos y ceroeventos calculados. Almacén359.885.391B/512MB. Referencias originales intactas, SST experimental. Quedan cinco IDs de datos sin primera integración(D02,D03,D11,D18,D41), además de ampliar coberturas/capacidades; ese conteo no mide avance predictivo del observatorio. Continúa temperatura/altura marina nativa y alternativas públicas pendientes.

## Incremento 11AK — temperatura potencial marina nativa

- D14 añade thetao a profundidad real0,494025m, sin cuenta. Encabezado372.347B/3rangos y muestra Caribe(-88°,18°)=29,254053115844727°C comprobados antes de ampliar al área del mismo chunk2.184.629B: vista45×22centros5–27°N/90–45°O,817válidos/173missing. No otra descarga científica para ampliar. Rango seleccionado25,2707557678…32,5151519775°C; no máximos globales. Malla1/12°/vista1°, coordenadas Float32 nativas con redondeo≤2,1e−5°, sin desplazamiento/mezcla espacial.
- Es temperatura potencial del agua, no SST de piel, aire u observación. Campo instantáneo según título, area:mean espacial; CF673848horas desde1950-01-01/gregorian=15/11/2026 00UTC, cotejo timedelta/netCDF4/nombre. Inicialización/emisión null, sin atribuirles R o Last-Modified.829.440Float32 de seis profundidades incluidas en un chunk cotejados bit a bit h5py/zlib crudo; sólo primera publicada y todas reproducibles en original. Relleno/no finito/fuera de valid_min−10…40°C→null, negativos dentro de rango válidos, sin QA inventada. Sin anomalía contra otros productos/MHW o pronóstico biológico.
- ZIP auténtico2.639.100B,21bloques/2.731.643B de rangos de objeto865.185.403B; SHA/manifiesto/ETag fuerte/versionado. Recuperación consolidada22:01:51UTC, ingestión22:04:01; tareaWindows existente reiniciada Running e hizo su primer tick autónomo22:06:39–22:06:46 unchanged, sin duplicar activo/revisión ni mover recuperación. Siguiente intento15/11 22:06:46. Límites8MiB/64peticiones/120s, timeoutMarine300s compartido, falla conserva REAL válido. Credenciales relevantes rechecadas sólo por presencia: todas ausentes; no se imprimieron secretos ni aceptaron contratos.
- Cinco pruebas auténticas verifican definición/unidad/escala, tiempo/profundidad/ejes/máscara, idempotencia/versionado y fallo/recuperación. Suite170API/37web, contratos/TypeScript/build aprobados. Inspector muestra consulta y recuperación separadas. Capturas REAL `real-marine-thetao.jpg` y `real-marine-thetao-900x650.jpg`; selección mantiene globo amplio, inspector340px/documento900px/un canvas. Se corrigió desborde de nombre científico con ajuste de palabras: sidebar204px de contenido/204px de ancho, sin scroll horizontal. Tamaño normal restaurado.
- Verificador76productos/33fuentes,47activos actuales/204.717.862B,resumen244.586B;48campos/6calculados,11.029observaciones,3.399históricos y ceroeventos calculados. Almacén362.566.223B/512MB. Referencias intactas, SST experimental. Sigue altura del mar nativa; no se la confundirá con GTSM D41 o profundidad de inundación.

## Incremento 11AL — altura del mar y componentes MOL nativos

- D14 añade cuatro campos externos: altura total CF sobre geoide, componente dinámica sin marea/presión, barómetro inverso y marea oceánica. Acceso público sin cuenta, primera muestra Caribe(-88°,18°):0,1396484375;0,1435546875;−0,0224609375;−0,060546875m respectivamente. Los mismos chunks cubren5–90°N/180–0°O; vista180×85centros1° de malla1/12°,10.875válidos/4.425missing por campo. Relleno−9999/no finito→null; cero y negativos válidos. Sin pines de celdas, máximos costeros o cobertura mundial descargada.
- 13.219.200Float32 de seis componentes cotejados bit a bit h5py/chunks crudos zlib+deshacer shuffle. Total contra suma de cinco componentes en1.565.400centros conjuntos, cota explícita de cuantización/Float32 y muestra Decimal50: residual máximo0,0016661137342453003m permitido, sin alterar originales para forzar igualdad. Offsets estérico0,009179115295410156m/masa0,06963543593883514m del estado inicial20161005 quedan en manifiesto/original, sin publicarlos como nuevos indicadores/tendencia global.
- Ejes también cuantizados por productor a1/1024°, cotejo de fórmula+cuantización bit a bit. Última longitud179,9169921875 excede valid_max previo179,9167022705078: se conserva nativa, sin generar coordenadas desde atributo. Depth auxiliar0,494140625m cuantizada, no altitud de sensor. Media horaria con CF00:30UTC15/11/2026, sin time_bounds; inicialización/emisión null, sin inventarlas desde R/Last-Modified. Geoide no se convierte a datum MSL/LAT local o profundidad de inundación. MOL D14 no se cuenta como GTSM D41, tsunami o aviso.
- Un ZIP6.652.699B/54bloques/6.970.479B de rangos de objeto469.785.711B compartido por cuatro productos, ETag fuerte/If-Match y SHA del subconjunto. Recuperación consolidada22:13:09UTC, ingestión22:16:00; tareaWindows reiniciada Running, tick autónomo22:18:36–22:18:40 unchanged con sólo HEAD, conserva recuperación y revisiones. Diario, siguiente15/11 22:18:40. Límites12MiB/96peticiones/240s, timeoutMarine300s. Falla/recuperación comprobadas, retención/exclusión comunes, sin crear cuentas o aceptar términos.
- Seis pruebas auténticas nuevas cubren referencia/unidades/precisión/época/ejes/máscara, cierre alterado/missing/cero, deduplicación y falla/recuperación. Suite176API/38web, contratos/TypeScript/build aprobados. Capturas REAL `real-marine-mol-total.jpg` y `real-marine-mol-900x650.jpg`, globo amplio e inspector reutilizado. Ventana900px, inspector340px/contenido324px sin desborde/un canvas; tamaño normal restaurado.
- Verificador80productos/33fuentes,48activos actuales/211.370.561B,resumen260.205B;52campos/6calculados,11.029observaciones,3.399históricos y ceroeventos calculados. Almacén370.537.086B/512MB. Referencias intactas, SST experimental. Sigue calificación de productos ecológicos NOAA D18; contar una variable física no habilita pronóstico ecológico.

## Incremento 11AM — corrientes mundiales y recuperación de procesos

- SMOC conserva los seis IDs y amplía al dominio oceánico mundial80°S–90°N/180°O–180°E, vista360×170centros1° desde1/12°. Una hora/capa; ninguna otra hora, variable, trayectoria o capacidad biológica inventada. Se midieron16chunks=29.274.477B antes de ampliar; reutilizando68bloques previos se descargaron21.757.952B adicionales/166peticiones en290,1s. No el objeto922MB/colección3D.35.268.480Float32 cotejados bit a bit, incluidos hemisferios sur/oriental;6.135.334nodos válidos nativos por componente.
- Vista61.200centros exactos,42.615válidos/18.585missing por campo, conserva cero/negativos y máscara. Normas de vector medio total0…2,180754151044396/euleriana0…2,1304863062080313m/s; extremos nativos no se atribuyen a la vista. Profundidad0,494025m, CF00:30UTC15/11, inicialización/emisión null y definición de media sin extremos inventados permanecen. Método globalv2; el fixture/decoder regionalv1 siguen reproducibles y claramente históricos, sin reducir catálogo.
- ZIP30.534.597B/234bloques/30.616.510B de rangos compartido por seis productos; recuperación consolidada22:37:58UTC, ingestión22:39:05. Límites medidos40MiB/320rangos/540s y `EARTH_ECHO_SMOC_GLOBAL_TIMEOUT_SECONDS=600`, separado de otros Marine300s. Dos revisiones SMOC bajo presupuesto512MB; prueba de retención conserva originales compartidos hasta que ningún campo los necesita. Revalidación real22:54:34–22:54:41 unchanged sin descargar campos ni mover recuperación. TareaWindows reiniciada Running; sólo ese trabajo vencido una vez para comprobar tick autónomo22:56:32–22:56:39 unchanged, siguiente15/11 22:56:39.
- La prueba de muerte del lanzador detectó que terminar sólo el proceso padre no garantiza liberación inmediata del hijo/lock Windows. Cada hijo registrado ahora tiene lock independiente, normalizaciónUTC y temporizador propio de salida; el padre cancela sólo su árbol creado y limita limpieza, sin espera ilimitada si falla terminación. Se probó proceso real, bloqueo con padre ausente, muerte del lanzador, deadline propio/código124, cancelación de árbol y recuperación. El sandbox impedía taskkill de hijos propios; las comprobaciones nativas autorizadas pasaron, sin debilitar controles o tocar procesos ajenos.184pruebasAPI/38web, contratos/TypeScript/build aprobados; ninguna promoción predictiva.
- Capturas REAL `real-smoc-global-u.jpg`, `real-smoc-global-norm.jpg`, `real-smoc-global-900x650.jpg`. Se esperó carga detallada para comprobar leyenda/valores, sin tomar sólo resumen como campo. Vista amplia preservada, sin pines de celdas; inspector340px/contenido324px, documento900px/un canvas, sin desborde. Tamaño normal restaurado. Fuente mundial no equivale a31detectores; contadores siguen separados.
- D18: vía forecast GCOOS enlazada por NCCOS rechazó conexión. HABSOS sí devolvió diez muestras reales Karenia brevis/cellsL, todas0/QA1. No se publican o cuentan: falta semántica acreditada de CELLCOUNT_QA y convención de hora de colección. Metadatos/JSON/XML vacía, URLs/SHA/fechas y bloqueo en `data/samples/d18-habsos` (18.784B); ni clorofila, salinidad o temperatura sustituyen pronóstico ecológico. No se pidió una credencial inexistente para resolver el problema científico.
- Verificador80productos/33fuentes,48activos actuales/233.842.474B,resumen260.218B;52campos/6calculados,14.836observaciones,3.399históricos y ceroeventos calculados. Actualizaciones autónomas IFS/OISST/Sentry/FIRMS/USGS explican cambios de registros/bytes. Almacén434.265.899B/512MB (fixtures/caché de desarrollo fuera de ese presupuesto). Se borraron tres carpetas temporales de pruebas; nueve quedaron por ACL, sin cambiar permisos. Referencias originales intactas, SST experimental. Continúan variables Marine pendientes y preparación de accesos NASA; D02/D03/D11/D18/D41 siguen sin primera integración cerrada.

## Incremento 11AN — salinidad práctica nativa y lectura de perfiles compartida

- D14 incorpora so a0,494025m, un instante15/11/2026 00UTC, sin cuenta. Colección/edición/nombre real resueltos por índice S3 público acotado antes de pedir encabezado. Muestra(-88°,18°)=29,603078842163086 en unidad nativa1e-3, unit_longPractical Salinity Unit. No reescala0,001/1000 o conversión a salinidad absoluta g/kg/densidad/oxígeno. Fuente modelada externa, no observación de muestra ni pronóstico de Vibrio/HAB/hipoxia.
- Un chunk2.126.409B contiene seis capas,829.440Float32 cotejados bit a bit h5py/zlib crudo. Primera publicada; todas retenidas/reproducibles. Misma área del chunk permite vista45×22centros1° desde1/12°,5–27°N/90–45°O, sin nueva descarga científica:817válidos/173missing,13,318762779…37,742168427. Cero dentro de rango nativo0…50 válido; relleno/no finito/fuera de rango→null. Ejes Float32, profundidad/calendarioCF1950 y tiempo instantáneo conservados; inicialización/emisión null.
- Temperatura y salinidad comparten sólo lectura/comprobación de perfiles en marine_profiles, con dos definiciones científicas explícitas y calificadas, sin registro abierto de plugins. El refactor reproduce byte a byte el ZIP anterior thetao; no descarga/edición nueva por cambiar código. Cada variable mantiene su unidad/rango/método/archivo. Seis pruebas auténticas nuevas cubren datos/ejes/época/máscara, definición práctica/unidad/escala/dominio cero, idempotencia y falla/recuperación controlada. Suite190API/39web, contratos/TypeScript/build aprobados.
- ZIP2.505.720B/20bloques/2.539.917B de rangos de objeto682.017.165B, SHA/manifiesto/ETag fuerte. Recuperación consolidada23:11:00UTC, ingestión23:14:31; tareaWindows reiniciada Running, tick autónomo23:18:43–23:18:46 unchanged por HEAD/cache, conserva recuperación y una revisión. Diario, siguiente15/11 23:18:46.8MiB/64rangos/120s, timeoutMarine300s, lock/retención/errores comunes. La verificación esperó a una actualización MODIS acotada en curso, sin interrumpirla o caer a demo.
- Capturas REAL `real-marine-salinity.jpg` y `real-marine-salinity-900x650.jpg`: unidad1e-3/leyenda, fecha/profundidad/atribución/QA accesibles en inspector; globo amplio sin acercamiento automático o pines de celdas. Inspector340px/contenido324px, documento900px/un canvas, sin desborde; tamaño normal restaurado.
- Verificador81productos/33fuentes,49activos actuales/236.348.194B,resumen263.891B;53campos/6calculados,14.838observaciones,3.399históricos y ceroeventos calculados. Almacén438.506.997B/512MB. Referencias intactas, SST experimental. Se solicitó por vía asíncrona configurar Earthdata localmente, sin pedir secretos por chat; trabajo público continuó. Siguiente: resolver acceso NASA actual y alternativas públicas concretas, sin confundir datos de ejemplo de otra misión/versión con SMAP SPL3SMP_E.

## Incremento 11AO — preparación NASA sin simular integración

- Metadatos CMR reales exactos: SMAP SPL3SMP_E006 del13/11/2026 y GLDAS_NOAH025_3H2.1 del31/07/2026 21UTC. Retenidos8.828B con SHA/URLs/UTC en `data/samples/nasa-access`. Cabecera/valores no descargados por falta de credenciales; no productos nuevos, no aumento de fuentes conectadas. No se confunde sufijo SMAP_001 con versión1 ni tiempo CMR con intervalo científico.
- Earthaccess0.19.0/uv.lock, login environment/persist=False, sin netrc/interactivo. Transporte por rangos validado antes de login, redirecciones NASA/S3 restringidas, Bearer retirado en S3 firmado, ETag fuerte/If-Match/206/Content-Range, límites, caché/replay y errores saneados. Se corrigió token vacío del ejemplo que SDK priorizaba sobre usuario/contraseña. CLI120s, máximo128KiB para cabecera; aun si funciona informa header_only, nunca conectado.
- Veinte pruebas finales NASA controladas cubren versiones/tiempos auténticos, ausencia de credenciales, SDK/secretos, token vacío, destinos/redirecciones, rangos ignorados/cambiados/comprimidos, fallas transitorias/401, idempotencia de lectura y no publicación. Suite completa209casos pasó antes del último caso/corrección NASA;20NASA finales posteriores pasaron. Verificador81productos/33fuentes/53campos,49activos/236.278.650B y referencias intactas. No se promovió evidencia predictiva.
- Alternativa ORNL fixed-sites no respondió dentro de límites; no valores obtenidos. El usuario confirmó continuar sin credenciales y priorizar capacidades centrales. Pasos exactos Earthdata documentados, sin cuentas/contratos/servicios contratados. Siguiente: anomalías y asociaciones sobre series persistidas, con versiones/referencia/unidades/soporte y demostración en interfaz existente.

## Incremento 11AP — anomalías históricas SST con referencia congelada

- Prioridad MVP científico del usuario. Implementado etiquetado mensual mediana/MAD con referencia2014–2021 y evaluación separada2022–2025, mínimo8años por mes,≥80%días, regla publicada|M|>3,5.48meses evaluables/9candidatos cálidos/0fríos/0no evaluables. Sin ajuste de umbral al resultado, probabilidades, daño, causalidad, alertas actuales o promoción del experimento predictivo SST.
- Cotejo independiente de los144agregados con todos los NetCDF reales/NumPy: hashes/tamaños, fechas/CF, variable/unidad/máscara, medias cos(lat)/días. Se detectó que selección nearest de extremos ERDDAP produjo21×21celdas0,05°, huella≈1,05°, no exactamente la caja1° solicitada. El nuevo producto declara bordes nativos16,50–17,55N/67,50–66,45O, manteniendo441celdas y valores originales. No se editó una referencia para aparentar ajuste.
- Producto persistido `d15-sst-seasonal-departures`, entrada agregada54.762B/SHA dba09d3d2a7bb9e4ecaf9b3fc99045b43de4e2867bc153125ac719885b258d60 con144checksums. Muestras temporales sin pines, categorías y score nulo anteMAD0/huecos/referencia insuficiente. API tipada `/v1/analyses/d15-anomalies`, contratos regenerados; resumen separa candidatos/evaluados/ausentes/entrada obsoleta. Inspector Tendencias reutiliza gráfico/tabla/atribución/entrada descargable. Mantiene diseño/globo amplio.
-215pruebas API/41web aprobadas, contratos/TypeScript/build. Pruebas incluyen no fuga de referencia, cero/huecos/MAD0, corrupción de entrada, persistencia idempotente, indisponibilidad explícita, conservación del anterior con advertencia y fingerprint de archivo. API local devolvió48/9y huella/método correctos. Captura nueva pendiente por fallo del controlador del navegador al inicializar sus archivos; no se fabricó evidencia visual. Las capturas REAL anteriores siguen disponibles.
- Trabajo diario y por cambio de entrada `d15-sst-anomalies`, lock/plazo/retención comunes. Una ejecución temprana detectó discrepancia de huella y falló sin publicar; tras corregir la comprobación, guardó correctamente15/11 05:25:54UTC. Verificador82productos/33fuentes/53campos/3indicadores calculados,50activos236.333.412B, referencias intactas. El conteo9 pertenece al análisis estadístico, no a eventos de desastre calculados. Método/limitaciones en `docs/mvp_cientifico.md`. Continúa asociación exploratoria ENSO/SST y AMOC/SST sobre entradas ya retenidas.

## Incremento 11AQ — conexiones exploratorias sobre series ya retenidas

- Dos pares predefinidos, desfase0 sin selección del máximo: RONI/SST Caribe2014–2025,48trimestres; RAPID-AMOC/SST Caribe2014–2023,40trimestres. JFM/AMJ/JAS/OND sin solapamiento; media igual de tres medias mensuales SST/AMOC, RONI trimestral publicado. Variables/unidades/ámbitos distintos. Relectura nativa CPC/RAPID con hashes y cotejo144meses SST; ninguna descarga externa nueva.
- Pearson crudo y de residuos tras cuatro interceptos estacionales+pendiente lineal de ambas series, sobre soporte común; todos los residuos y correlaciones cotejados contra NumPy/diseño explícito/SVD. Mínimo32pares/6años por trimestre, eje denso/huecos conservados, correlación indefinida→null. Bootstrap circular emparejado de residuos,1000réplicas, semilla fija, bloques4y8mostrados sin elegir el favorable. Intervalos95% aproximados condicionales a ajustes, sin p-valor, atribución causal o evidencia predictiva. Se declara acoplamiento matemático posible al restar media tropical RONI que incluye Caribe.
- Resultados reales: RONI rcrudo−0,051256/ajustado0,244073; AMOC0,571922/0,189734. Ambos intervalos incluyen cero, en ambas longitudes; no demuestra ausencia de conexión física. Valores/ventanas/unidades/residuos/SHA/método y limitaciones exportables enAPI`/v1/analyses/associations` yCSVpor par. Inspector existente Tendencias suma Conexiones exploratorias con dispersión temporal y sensibilidad; no rediseño o pines.
- Informe tipado persistido atómicamente, identidad científica3c24395926cda7cb72605bdfa3d855491031f46b326c788382c39a8724e46147, hasta4revisiones/2MBpor informe y presupuesto512MB conjunto con productos. Revisión diaria/por dependencia después de entradas; falla conserva anterior y consulta avisa obsolescencia. Capacidad Asociación añadida a31filas, parcial sóloF17/F19/F31en este alcance; sin convertir todo el catálogo en detectores.
-220API/43web, contratos/TypeScript/build aprobados. Casos conocidos comprueban que señal estacional/tendencia compartida no se presenta como asociación residual; huecos, degeneración, referencia nativa, idempotencia, CSV, falla/obsolescencia y ausencia de DEMO. Verificador MVP reprodujo cálculos originales/API/CSV y guardó`data/operational/mvp_scientific_evidence.json`; verificador general82productos/33fuentes/referencias intactas. Anomalías ejecutadas automáticamente05:30:36–05:30:38UTC→unchanged, preservando recuperación/revisión. TareaWindows Running. Capturas nuevas siguen pendientes por inicialización fallida del controlador de navegador; no se declara QA visual nueva aprobada. Siguiente: mejorar/revisar ajuste de tendencia SST y cerrar estabilidad/demostración del MVP, sin sumar fuentes.

## Incremento 11AR — tendencia estacional con bloques calendario y contrato generado

- Nuevo método v2 ajusta SST absoluta contra doce interceptos de mes calendario+pendiente común; anomalías2014–2021 quedan sólo como representación gráfica.144meses2014–2025, pendiente0,06815495338°C/año; intervalo condicional95%/12meses0,02665672194…0,10905991707 y sensibilidad24meses0,02615383366…0,11051116545. Dependencia residual adyacente0,84370387165 se muestra como diagnóstico, sin prueba automática de supuestos o extrapolación. Código/experimento v1 intactos, siguen experimentales.
- Bootstrap1000réplicas por longitud, bloques calendario completos/semilla fija/máscara original, mínimo96meses/6años por mes y8inicios elegibles. No se concatenan meses a través de huecos; puede existir pendiente evaluada con intervalo null si no hay bloques completos. Intervalos aproximados condicionales al ajuste y supuestos; sin toda incertidumbre observacional, causalidad, fecha de desastre o probabilidad. Regla práctica0,02°C/año sigue siendo parámetro descriptivo, sin umbral de daño.
- TrendView trasladado a contratos Pydantic y tipos/esquema generados. SHA de entrada y huella real vinculados; caché por hash/método/corte≤16vistas. CSV incorpora unidad/referencia/método/versión/ejecución/SHA y respeta corte año/mes. Corte futuro no extiende datos. Región sin cobertura ya no muestra intervalos o diagnósticos ajenos. Inspector declara coordenadas del recorte al sur de Puerto Rico, manteniendo ID regional heredado; gráfico llama a la línea componente lineal. Anomalías/asociaciones permanecen accesibles si falla sólo la consulta de tendencia.
-225API/45web y contratos/TypeScript/build aprobados. Casos conocidos de estacionalidad/pendiente, huecos, bloques ausentes, constante/cero, serie corta, SVD, corte/CSV y regiones; verificador MVP confirmó SVD/API/CSV y guardó parámetros/resultados. Se mantuvo el aviso explícito «No es un pronóstico» también en el asistente. TareaWindows reiniciada Running sin trabajos en curso para cargar análisis nuevos; asociaciones ejecutadas automáticamente05:44:36–05:44:39UTC→unchanged. Capturas pendientes por controlador de navegador, sin bloquear comprobaciones independientes. Siguiente: anomalía diaria OISST ya incluida en el original retenido, para completar recorrido actual además del histórico; sin nueva fuente o descarga duplicada.

## Incremento 11AS — anomalía diaria mundial del original OISST compartido

- Se publicó la variable anom ya presente en el NetCDF D13, sin nueva fuente/HTTP o climatología propia. Base NOAA1971–2000/short escala0,01, fill−999dentro de rango−1200…1200enmascarado antes de escala;1.036.800posiciones netCDF4/HDF5 cotejadas,691.150válidas. Fecha real13/11/2026 12UTC, preliminar, recuperación fuente preservada. Unidad°C y definición distintas de score histórico/regional/temperatura del aire o pronóstico.
- Vista mundial360×180medias1°, bloques4×4cos(lat) con mínimo8/16válidos.64.800medias/conteos cotejados con bucle/Math.fsum independiente.43.467visibles/21.333ausentes;−5,989118855799…7,892959049414°C. Centros exactos/huella−180…180,−90…90, sin saltos de celda en antimeridiano. Nulos transparentes, cero válido, soporte conservado y original0,25°SST/anom/err/ice accesible. No celdas convertidas a señales o eventos MHW.
- Mismo checksum/ruta1.529.198B compartido por SST/anomalía; fixture auténtica acotada/metadata/README para reproducción, SHA verificado. Colores/leyenda centrados en cero, límites simétricos y rango científico separado, sin cambiar valores. Contrato valida escala lineal finita/no invertida; leyenda sin valores no inventa0. Inspector existente/unidad/QA/fecha/atribución/último procesamiento; botón desde anomalías históricas abre campo/inspector sin encuadrar cámara o cambiar aDEMO.
-229API/49web, contratos/TypeScript/build y verificador nativo/MVP aprobados. Tests incluyen fill dentro de valid_range, cero, agregación/soporte, validación de colores, leyenda ausente, persistencia/activo único, ausencia/corrupción y selección explícita independiente de historia. Trabajo `d13-current-anomaly` diario/por entrada, sin HTTP propio, primera publicación06:07:40UTC. Verificador83productos/33fuentes/54campos/50activos,236.336.986Boriginales actuales, resumen270.802B, referencias intactas. Almacén científico productos+análisis462.688.235B/512MB; fixtures/caché de desarrollo aparte. Continúa acceso del asistente a los resultados centrales, manteniendo resúmenes verificados y bloqueo de resultados futuros en replay.

## Incremento 11AT — asistente científico verificable y cierre de comprobaciones

- Asistente consulta resultados persistidos de anomalías históricas/campo diario, asociaciones y tendencia AMOC enSv/década. Conserva unidades, períodos, alcance, incertidumbre, SHA y enlaces de datos. Nuevos resúmenes/capacidadesF17/F19/F31 usan plantilla verificada, sin llamar al proveedor de texto opcional (`not_used` explícito) para evitar reinterpretar correlaciones como causas. Corte de replay bloquea datos completos y llamada al modelo; no revela resultados posteriores. Request/reply Pydantic incorporados al bundle, frontend generado y enlaces de trazabilidad locales.
- La pendiente AMOC se comunica como descriptiva2005–2023/26,5N, sin intervalo calculado, atribución o fecha de colapso. Resumen sísmico respeta la consulta real, sin umbral fijo5ni convertir fuente ausente en cero sismos. Inspector de anomalía diaria informa falla de descarga de fuente aunque derivación local sea correcta, conservando fechas/REAL. Se conserva comportamiento previo del resto del asistente y experimento SST experimental.
-235API/51web, contratos/TypeScript/build aprobados. Pruebas protegen plantillas sin llamada al modelo, unidades y resultados reales, intervalos/causalidad, replay, alcance sísmico/ausencia y avisos de fuente aguas arriba. Verificador MVP ejecutado por API local comprobó originales completos/cálculos/SVD/JSON/CSV y preguntas reales del asistente/replay, con cero nuevas descargas. Verificador general83productos/33fuentes/54campos/50activos y referencias originales intactas. La nueva anomalía diaria pasó un tick autónomo06:20:31–06:20:33UTC→unchanged, sin nueva recuperación/revisión; tareaWindows Running tras cargar los trabajos nuevos.
- Guía de recorrido en`docs/mvp_cientifico.md`, entrega/matriz/progreso actualizados. Bloqueo restante de cierre visual: controlador de navegador no inicializa sus archivos (`system cannot find the path specified`), repetido tras recuperación de sesión; no se fabricaron capturas o sustituyó por renders. Se conservan pruebas numéricas/API/frontend ejecutadas y capturas anteriores. Earthdata permanece pendiente por decisión expresa; no se crearon cuentas, aceptaron contratos o ampliaron fuentes durante el núcleoMVP. Las otras cinco fuentes pendientes y validación predictiva de modelos siguen separadas de estas capacidades descriptivas.

Cierre operativo 2026-11-15T06:40:19.131280+00:00: instantánea de51metadatos de feeds/pronósticos/productos actualizados autónomamente, incluida retención de revisiones. Se capturó bajo lock del actualizador después de verificar API/originales; sin cambiar métodos, referencias, estado científico o los archivos de auditoría del usuario. Los originales compartidos siguen en el almacén local y las fixtures auténticas conservadas.

## Pendientes heredados

1. Credenciales Earthdata para IMERG y SMAP, sin caer a DEMO si fallan.
2. Un Qwen local pequeño, solo para parafrasear herramientas, si se quiere texto de modelo.
3. Una cuenta ECMWF/EWDS y aceptación manual por producto para la ruta nativa GloFAS/hindcasts; dos celdas rolling v4 ya están conectadas por distribución pública, sin convertir caudal en profundidad.
4. Mantener el experimento de SST como experimental hasta que supere a la persistencia en una prueba nueva.

