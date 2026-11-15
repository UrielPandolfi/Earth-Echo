# Auditoría funcional después de la fase 10

Revisión del 13 de noviembre de 2026, por la tarde, sobre el código y los archivos locales. No se agregó ninguna capacidad. No se volvió a descargar CoralTemp, USGS ni SWPC: las horas de ingestión son las que ya estaban en disco.

Referencias usadas: `Earth_Echo_Especificacion.md` (12 de noviembre de 2026), `Earth_Echo_Catalogo.json`, `Earth Echo Global Environmental Observatory.png` (1672×941) y `GET /v1/capabilities`.

La especificación dice que se puede construir un observatorio mundial de observaciones, señales, tendencias y pronósticos, y que la primera versión puede tener un globo real y varias capas. También dice que una capa global no garantiza un pronóstico local, y que ningún modelo propio quedó evaluado en ese documento. El estado de abajo es más estrecho que esa visión.

## 1. Capturas

Resolución pedida al navegador: 1672×941, la del PNG. Comprobado con `innerWidth` e `innerHeight`.

| Vista | Archivo |
| --- | --- |
| DEMO, instante «Ahora», ficha «Déficit de humedad» | [docs/auditoria/demo-1672x941.png](auditoria/demo-1672x941.png) |
| REAL, recorte de SST y panel izquierdo | [docs/auditoria/real-1672x941.png](auditoria/real-1672x941.png) |
| Misma vista REAL; el diálogo de trazabilidad se abrió encima | [docs/auditoria/real-trazabilidad-1672x941.png](auditoria/real-trazabilidad-1672x941.png) |

El inspector REAL estaba en el DOM: «SST del Caribe occidental», 2026-11-08 12:00:00 UTC, promedio 29,7327 °C, 441 celdas, probabilidad no disponible. «Ver trazabilidad» abrió el activo `d15-coraltemp-v3.1-caribe-r1`, checksum `b190912a4f0a8f94ae0b4a5fa4e5254547fef88f93518559cae80b60954af231`, 25120 bytes, colección `noaacrwsstDaily`. El texto del diálogo dice que no es el escenario DEMO.

### Diferencias con el PNG

La composición de tres columnas, la barra y la franja de tiempo se parecen. El resto no es la imagen.

- El PNG muestra un planeta lleno de pines, números y un huracán. DEMO muestra 169 señales agrupadas, sobre todo en América, y el conteo «169 señales · 31 fenómenos». El 31 es el catálogo, no 31 capas vivas.
- Los filtros DEMO contaron 50, 51, 9, 25, 25 y 9. El PNG muestra 384, 327, 146, 218, 93 y 22. Esos números de la imagen no están en el código como datos.
- DEMO dibuja una sola capa ilustrativa, humedad del suelo, con una rampa y huecos transparentes. No está el campo multicolor continuo de América del Sur ni las tres capas a la vez.
- La ficha de apertura dice que el valor −0,041 m³/m³ es ilustrativo. No dice «riesgo en evaluación» ni muestra lluvia y vegetación relacionadas como mediciones.
- En REAL la cámara se fue sola al recorte de 1° del Caribe. Se ve un rectángulo de SST y un punto. No se ve el enjambre mundial de la referencia. Los 15 sismos están cargados, pero quedan fuera de ese encuadre.
- REAL cambia la franja de tiempo a cuatro fechas, 2026-11-08 a 2026-11-11. No ofrece el horizonte −30 / +30 del PNG.
- La base geográfica cargó con el crédito de NASA GIBS Blue Marble y Cesium. El PNG no muestra esa atribución.
- El análisis de tendencia no está en la ficha de apertura. Está en la sección Tendencias.

## 2. Los cinco archivos de `/ready`

`GET /ready`, leído en esta revisión, respondió `query_stores: ready` y `providers_updated: not_checked`. El asistente figuró `unavailable`. Los cinco archivos:

| Archivo | Tamaño | Qué es |
| --- | --- | --- |
| `data/real/d15/monthly_series.json` | 54762 bytes | 144 promedios mensuales de SST, enero 2014 a diciembre 2025, todos presentes. Enero 2014: 26,8884 °C. Diciembre 2025: 28,0296 °C. También guarda el método `ols-monthly-anomaly-block-bootstrap-v1` y 144 checksums. |
| `data/real/d15/index.sqlite` | 36864 bytes | Un activo NetCDF y cuatro observaciones diarias del 8 al 11 de noviembre de 2026. |
| `data/real/feeds/d21-events.json` | 3796 bytes | 15 sismos de magnitud ≥ 5. Recuperado el 2026-11-13T07:45:49Z. El más reciente del archivo es `us7000txxl`, magnitud 5,0, 2026-11-13T01:12:46Z, 85 km al oeste de Mwene-Ditu. |
| `data/real/feeds/d28-kp.json` | 5683 bytes | 58 valores de Kp, del 2026-11-06T00:00:00 al 2026-11-13T03:00:00. Último Kp: 0,33. Misma hora de recuperación que los sismos. |
| `data/real/forecasts/d28-kp-forecast.json` | 3641 bytes | 17 pasos previstos de Kp, emitidos al archivarlos el 2026-11-13T07:56:50Z, válidos del 2026-11-14T00:00:00Z al 2026-11-16T03:00:00Z. `validated_for_use` es falso. |

`/ready` no mira los 144 NetCDF mensuales de `data/real/d15/history/`. Esos archivos están en disco (144) y no entran en Git. Si faltaran, la serie JSON podría seguir presente y `/ready` seguiría en `ready`.

### Fuentes conectadas

Solo D15, D21 y D28 están `connected` en `data/operational/source_integration.json`. D01 y D02 siguen en `credential_required`.

| Fuente | Variable | Dónde | Resolución | Período en disco | Última observación | Ingestión |
| --- | --- | --- | --- | --- | --- | --- |
| D15 CoralTemp v3.1, `analysed_sst` | Temperatura superficial del mar, °C | Recuadro pedido: oeste −67,5, sur 16,5, este −66,5, norte 17,5. Malla realizada: 21×21 centros, paso 0,05°. | La ficha del producto es de 5 km; este archivo es ese paso de 0,05° dentro de 1°. | Diario: 2026-11-08 a 2026-11-11, 12:00Z. Mensual: 2014-01 a 2025-12. | Diaria: 2026-11-11T12:00:00Z. Mensual: diciembre 2025. | Diaria: 2026-11-13T06:37:46Z. La serie mensual se armó con los NetCDF ya bajados; no se repitió la descarga en esta revisión. |
| D21 USGS | Magnitud y lugar de sismos M≥5 | Los 15 eventos caen donde USGS los ubicó. No es una malla mundial. | Puntos del catálogo | Ventana de la instantánea, 10 al 13 de noviembre de 2026 | 2026-11-13T01:12:46Z | 2026-11-13T07:45:49Z |
| D28 SWPC, Kp observado | Índice planetario Kp | No tiene mapa. Es un número global. | Índice de 3 horas | 2026-11-06T00:00:00 a 2026-11-13T03:00:00 | 2026-11-13T03:00:00, Kp 0,33 | 2026-11-13T07:45:49Z |
| D28 SWPC, Kp previsto | Kp previsto, no una probabilidad | Igual, sin mapa | Pasos de 3 horas | 17 pasos hasta 2026-11-16T03:00:00Z | No es una observación | Archivado 2026-11-13T07:56:50Z |

`GET /v1/sources/D15` respondió `available` y frescura `recent_archive`.

### Qué es descarga única, historia o automático

- El NetCDF de cuatro días y los 144 meses se bajaron con comandos manuales. No hay un proceso que los repita al arrancar.
- La serie mensual reemplazó un intento de pedir el año entero. Esas peticiones anuales respondían HTTP 502. Un mes sí entraba. El resultado es un promedio por mes, ponderado por el coseno de la latitud, con un mes anulado si faltan más del 20 % de los días. Esa serie permite la tendencia, el experimento de análogos, el CSV y las respuestas del asistente sobre SST. No pinta el rectángulo del globo: el globo usa el activo diario.
- Sismos y Kp tienen una cadencia escrita en código, una hora y tres horas, pero solo corre cuando alguien ejecuta `npm run ingest:feeds`. En esta revisión no había un planificador encendido. A las 21:46 UTC del 13 de noviembre el Kp observado seguía siendo el de las 03:00 UTC.
- El pronóstico de Kp es una corrida guardada. El proveedor puede borrar la suya; la copia local no se actualiza sola.

## 3. Recorridos comprobados en esta pasada

### Observación y procedencia

1. Abrir http://127.0.0.1:5173/ y pulsar REAL.
2. La ficha muestra «SST del Caribe occidental», 29,7327 °C, y aclara que no es anomalía, HotSpot ni blanqueamiento.
3. «Ver trazabilidad» muestra activo, checksum, tamaño, colección y la frase de que no es DEMO.

Eso funcionó de punta a punta contra la API local. IMERG permanece como texto de bloqueo en el mismo panel.

### Tendencia

1. Con REAL activo, pulsar Tendencias.
2. El panel cargó «SST del Caribe occidental», 2014-01 a 2025-12.
3. El texto en pantalla: la anomalía sube unos 0,068 °C por año; el intervalo va de 0,024 a 0,109; no es un pronóstico.

La misma consulta `GET /v1/analyses/d15-sst` devolvió pendiente 0,06811693754521339 °C/año, intervalo 0,0238228785306142 a 0,1088159353488615, 144 meses, `predictable: not_a_forecast`. La región no se elige: el código solo acepta `caribe-occidental`. Otra región queda no disponible. No es una tendencia mundial.

### Pronóstico y replay

El único pronóstico visible en Explorar es el Kp importado, en el panel izquierdo: «Kp 0,33 · 2026-11-13T03:00:00 · índice planetario, no un aviso local». Ese 0,33 es el último valor **observado**. Los 17 pasos previstos están en el archivo y en la sección Tendencias, dentro de «Pronóstico importado». No se volvió a abrir ese bloque en esta pasada: **no comprobado** en pantalla esta tarde. El archivo sí se leyó de disco.

El experimento propio no es un pronóstico operativo. `GET /v1/experiments/sst-anomaly` devolvió `validated_for_use: false`, `additional_skill: false`, 47 casos, error absoluto medio del análogo 0,404 °C y de la persistencia 0,214 °C. Anticipa la anomalía del mes siguiente en el mismo recorte y no le gana a repetir el mes actual. El replay de junio de 2024 ya está guardado en `data/real/forecasts/replay/2024-06.json`, con desenlace incluido, porque se reveló en la fase 8. Los botones «Guardar predicción» y «Revelar desenlace» estaban en el texto de la página. No se creó un replay nuevo en esta revisión.

## 4. Fenómenos

Una casilla de filtro no es una capacidad. En DEMO solo hay fichas generadas para F01, F11, F15, F19, F25 y F29. El resto de los identificadores que aparecen en un grupo de filtros no tienen tarjeta propia.

| ID | Fenómeno | DEMO | Observación real | Indicador | Tendencia | Pronóstico | Bloqueo o límite |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F01 | Lluvias extremas | Fichas ilustrativas en mm | No | No | No | No | D01 pide Earthdata |
| F02 | Olas de calor | Solo el grupo «Calor y sequía» | No | No | No | No | La SST no es temperatura del aire |
| F03 | Olas de frío y heladas | Solo el grupo | No | No | No | No | Sin fuente |
| F04 | Tormentas severas y granizo | No | No | No | No | No | Sin fuente |
| F05 | Tornados | No | No | No | No | No | Sin fuente |
| F06 | Ciclones tropicales | No | No | No | No | No | Sin fuente |
| F07 | Marejadas e inundación costera | Solo el grupo de lluvia | No | No | No | No | Sin fuente |
| F08 | Nieve y tormentas de hielo | No | No | No | No | No | Sin fuente |
| F09 | Tormentas de polvo | No | No | No | No | No | Sin fuente |
| F10 | Contaminación y transporte de humo | No | No | No | No | No | Sin fuente |
| F11 | Sequías | Ficha hero y otras ilustrativas de humedad | No | No | No | No | D02 pide Earthdata; el HDF no se bajó |
| F12 | Crecidas fluviales | Solo el grupo de lluvia | No | No | No | No | GloFAS pide cuenta CDS |
| F13 | Inundaciones repentinas | Solo el grupo de lluvia | No | No | No | No | Sin fuente |
| F14 | Escasez de agua | Solo el grupo de calor | No | No | No | No | Sin fuente |
| F15 | Peligro de incendios | Fichas de un índice inventado | No | No hay archivo FWI | No | No | GWIS quedó como portal |
| F16 | Estrés agrícola | No | No | No | No | No | Sin fuente |
| F17 | El Niño y La Niña | Solo el grupo de océano | No | No | No | No | Sin fuente |
| F18 | Olas de calor marinas | Solo el grupo de océano | No | No | No | No | La SST del recorte no es una ola de calor marina |
| F19 | Estrés térmico de corales | Fichas ilustrativas de anomalía | SST parcial, solo el recorte del Caribe | No | Parcial: anomalía mensual de esa SST, no daño biológico | No | No hay HotSpot, DHW ni outlook de blanqueamiento |
| F20 | Floraciones de algas nocivas | Solo el grupo de océano | No | No | No | No | Sin fuente |
| F21 | Hipoxia acuática | No | No | No | No | No | Sin fuente |
| F22 | Condiciones favorables para Vibrio | No | No | No | No | No | Sin fuente |
| F23 | Langosta del desierto | No | No | No | No | No | Sin fuente |
| F24 | Actividad volcánica y erupciones | Solo el grupo de tierra | No | No | No | No | Sin fuente |
| F25 | Deslizamientos por lluvia | Fichas ilustrativas de lluvia, no un deslizamiento | No | No | No | No | Sin fuente |
| F26 | Desbordes de lagos glaciares | Solo el grupo de tierra | No | No | No | No | Sin fuente |
| F27 | Tsunamis | Solo el grupo de tierra | No | No | No | No | Sin fuente |
| F28 | Réplicas sísmicas | Solo el grupo de tierra | Parcial: 15 sismos M≥5, no probabilidades de réplica | No | No | No | D22 no está ingerido |
| F29 | Tormentas geomagnéticas | Fichas ilustrativas en km/s, no el Kp | Kp planetario conectado | No | No | Parcial: Kp previsto importado, no validado y no local | No convierte una fulguración en intensidad local |
| F30 | Impactos de asteroides conocidos | Solo el grupo de clima espacial | No | No | No | No | Sin fuente |
| F31 | Cambios en la AMOC | No | Investigación | No | Investigación | Investigación | No hay transporte ni fecha de colapso |

Ningún indicador del catálogo está calculado. Ningún pronóstico está validado.

## 5. Distancia respecto del producto imaginado

**Qué detecta hoy con datos reales.** Temperatura del mar en un grado de longitud y latitud del Caribe occidental, en cuatro instantes de noviembre de 2026 y en 144 meses hasta diciembre de 2025. Quince sismos recientes de magnitud 5 o más. El índice Kp planetario de unos días. Nada más.

**Qué anticipa y con qué evidencia.** Un Kp previsto por SWPC, guardado el 13 de noviembre, con validez hasta el 16. No está validado y no es un aviso local. El experimento de análogos estima la anomalía de SST del mes siguiente en el mismo recorte; la evidencia dice que su error es mayor que el de la persistencia, así que no se promociona. No hay otro pronóstico.

**Qué es mundial y qué es regional.** El globo y la base GIBS son mundiales. El Kp es un índice planetario, no un mapa. Los sismos son puntos sueltos de una consulta reciente, no una vigilancia continua del planeta. La SST, su tendencia y el experimento cubren solo el recorte del Caribe occidental.

**Qué pide una actualización manual.** Los cuatro días de SST, la historia mensual, los sismos, el Kp observado y el Kp previsto. Los comandos son `npm run ingest:d15`, `npm run ingest:d15-history` y `npm run ingest:feeds`. No hay un servicio que los dispare.

**Qué sigue siendo solo la ilustración.** El huracán, la densidad de pines, los conteos grandes, el campo continuo de América, las etiquetas de riesgo, la humedad de la Amazonía, los pronósticos demo y cualquier fenómeno de la tabla que no tenga una fila real. El «31 fenómenos» de la barra no significa que haya 31 detectores.

## Próximos tres incrementos

1. **Un campo de SST más amplio, el mismo producto.** Fuente: NOAA Coral Reef Watch CoralTemp v3.1, `analysed_sst`, por ERDDAP, sin credencial. Resultado visible: en REAL, un campo con leyenda en °C sobre una cuenca o el planeta, con fecha y huecos transparentes, sin convertir cada celda en un pin. Requisitos: una petición adelgazada que quepa en el límite de descarga ya usado; conservar el recorte trazable de 1°. Criterio de aceptación: una celda conocida coincide con el archivo, un fallo de red deja el campo anterior y no abre DEMO, y el texto no dice blanqueamiento ni HotSpot.
2. **Lluvia observada en un recorte, si hay credencial.** Fuente: IMERG Early, D01, con `EARTHDATA_USERNAME` y `EARTHDATA_PASSWORD` en `.env`. Resultado visible: una lluvia con unidad, tiempo y procedencia, separada de las fichas DEMO. Si la credencial falta o la descarga falla, el panel sigue diciendo bloqueado. Criterio de aceptación: el valor sale del archivo decodificado, no de la ficha de 50 señales, y no se interpreta como inundación ni como lluvia futura.
3. **Poner en marcha la cadencia que ya existe.** No hace falta otra fuente. Un proceso local debe ejecutar la actualización de sismos y de Kp, mostrar la edad del archivo y conservar la instantánea anterior si la red falla. Criterio de aceptación: después de la cadencia, `retrieved_at` cambia cuando el proveedor publicó algo nuevo, y un error deja el Kp 0,33 del 13 de noviembre en vez de pasar a DEMO.
