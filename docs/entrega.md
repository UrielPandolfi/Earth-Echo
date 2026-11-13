# Entrega local de Earth Echo

Esta entrega corre en la máquina de desarrollo. No hay un servidor público ni un modelo de lenguaje cargado. El detalle de cada fenómeno sigue en `GET /v1/capabilities`.

## Matriz de lo que esta versión hace

| Capacidad | Implementación | DEMO | REAL | Alcance | Límite |
| --- | --- | --- | --- | --- | --- |
| Globo WGS84 | Implementada | Sí | Sí | Vista global | Sin terreno 3D. La base puede ser GIBS o Natural Earth II. |
| Filtros, búsqueda, tiempo y agrupación | Implementada | Sí, escenario con semilla | Fechas del recorte y capa de sismos | El escenario demo | Los conteos del PNG no son el inventario real. |
| SST CoralTemp, D15 | Implementada | No | Sí | Caribe occidental, 2026-11-08 a 2026-11-11 | No es HotSpot, DHW ni blanqueamiento. |
| Tendencia de la anomalía de SST | Implementada | No | Sí | 2014-01 a 2025-12, una región | No es un pronóstico ni una causa. |
| Análogos a un mes | Experimental | No | Retrospectivo | Misma región, 47 meses | No supera a la persistencia. No está validado. |
| Kp previsto, D28 | Importado | No | Sí, una corrida archivada | Índice planetario | No es probabilidad ni aviso local. |
| Sismos M≥5, D21 | Implementada | No | Sí, instantánea | Eventos observados | No hay fecha del próximo sismo. |
| Asistente | Implementada | Sí, sin medir el escenario | Sí, sobre las herramientas | Consulta | Qwen no está instalado. |
| Lluvia D01, humedad D02, caudal | Bloqueada | Solo fichas ilustradas | No | Catálogo | Faltan credenciales o cuenta. |
| FWI, calor del aire, AMOC y el resto | Especificada o de investigación | No | No | Matriz | No hay predictor operativo. |

De los 31 fenómenos, la observación queda así: 1 conectada, 2 parciales, 3 bloqueadas, 1 de investigación y 24 especificadas. El único pronóstico parcial es el Kp importado. Ningún pronóstico está validado para uso.

## Guion corto

1. `npm run dev:api` y `npm run dev:web`. Abrí http://127.0.0.1:5173/.
2. DEMO. La ficha «Déficit de humedad» es ilustrativa. Cambiá un filtro, buscá la señal y mové el tiempo. El globo no se recrea.
3. REAL. Aparece la SST del Caribe, los sismos y el Kp. IMERG sigue bloqueado y la pantalla no vuelve a DEMO.
4. Tendencias. La pendiente es la ya calculada. Guardá la predicción de un mes y después revelá el desenlace.
5. Asistente. Preguntá por la tendencia. Si el modelo no está configurado, la respuesta sale de las herramientas y lo dice.
6. Histórico. La matriz muestra los 31 fenómenos, con observación, indicador, tendencia y pronóstico por separado.

## Copia y restauración

No hay un servicio de base aparte. La copia útil es el directorio `data/real`:

- `d15/index.sqlite` y `d15/assets` para el recorte de SST.
- `d15/monthly_series.json` para la serie agregada.
- `feeds` para sismos y Kp observado.
- `forecasts` para el Kp previsto y los replay.

Los NetCDF mensuales pueden ocupar mucho y no están en Git. Para restaurar, detenés la API, reponés esos archivos en las mismas rutas y volvés a arrancar. `GET /ready` tiene que volver a decir `query_stores: ready`. Eso no actualiza a los proveedores.

## Arranque después de reiniciar

Los JSON y el SQLite se leen de disco. No hay un planificador residente: `npm run ingest:feeds` y `npm run ingest:d15` se lanzan a mano. El mapa abre aunque `/v1/assistant/status` diga `unavailable`.
