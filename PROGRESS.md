# Progreso

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

## Pendientes heredados

1. Credenciales Earthdata para IMERG y SMAP, sin caer a DEMO si fallan.
2. Un Qwen local pequeño, solo para parafrasear herramientas, si se quiere texto de modelo.
3. Una cuenta CDS si se va a leer caudal, sin convertirlo en profundidad de inundación.
4. Mantener el experimento de SST como experimental hasta que supere a la persistencia en una prueba nueva.

