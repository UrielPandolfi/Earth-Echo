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

## Siguiente paso

Fase 08: pronósticos con una prueba temporal que no use el futuro, sin convertir estos sismos ni el Kp en una predicción.
