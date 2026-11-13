# Arquitectura

Decisión del 13 de noviembre de 2026. El repositorio no tenía aplicación previa.

## Stack

| Pieza | Elección | Motivo |
| --- | --- | --- |
| Interfaz | React 19.3, TypeScript 7.0.2, Vite 8.3.8 | El prompt lo proponía y el entorno ya tiene Node 22 y npm. Un solo gestor: npm, con `package-lock.json`. |
| Globo | CesiumJS 1.147 y `vite-plugin-cesium` 1.2.23 | Motor geográfico 3D. La prueba monta y destruye un `Viewer`. No se agregó otra librería de mapas. |
| API | Python 3.12, FastAPI 0.162.5, Pydantic 2.14.3, Uvicorn 0.54 | Validación en el borde y un proceso de salud separado de los proveedores. El entorno reproducible es uv, con `uv.lock`. |
| Contratos | Modelos Pydantic, JSON Schema Draft 2020-12 y tipos TypeScript generados | Una sola fuente. `npm run contracts:check` detecta divergencia. |
| Pruebas de interfaz | Vitest 5.1 y jsdom 26.1 | jsdom 31 pide un Node más nuevo que el 22.14 instalado. |

Cesium 1.147 declara `node >= 22.17.0`. Con Node 22.14.0 npm avisó y el paquete se instaló. El globo, los workers y las texturas locales funcionaron en el navegador. No hace falta Docker para desarrollar; Docker no está instalado en esta máquina.

## Responsabilidades

- `apps/web`: composición de la pantalla técnica, tokens mínimos de esa pantalla y cliente de la API.
- `apps/web/src/globe`: adaptador de Cesium y el registro que impide dos visores en el mismo contenedor.
- `services/api/src/earth_echo/contracts`: observación, señal, pronóstico, activo y resultado no disponible.
- `services/api/src/earth_echo/catalog`: lectura y validación del catálogo original, más el estado operativo aparte.
- `services/api/src/earth_echo/connectors`: normalización de las muestras ya guardadas.
- `services/api/src/earth_echo/queries`: la consulta que exige un modo y no mezcla demo con real.
- `data/demo`: el único fixture sintético.
- `data/samples`: muestras públicas pequeñas.
- `data/operational`: estado de integración y hashes de las referencias.
- La ciencia todavía no tiene módulo. No hay detectores vacíos. Cuando exista un cálculo, irá en `services/api/src/earth_echo/science` y no en React.

## Imágenes del globo

CesiumJS, licencia Apache-2.0, no es lo mismo que Cesium ion. La imaginería y el terreno por defecto de ion piden cuenta y token. Esta fase usa `Assets/Textures/NaturalEarthII`, servido desde el propio paquete, y `EllipsoidTerrainProvider`. El crédito visible dice «Natural Earth». El logo de Cesium ion que muestra el widget es la atribución del visor, no una sesión de ion: en la prueba no hubo pedidos a `cesium.com`.

`CESIUM_ION_TOKEN` queda reservado y no entra al bundle. La fase 03 puede elegir otra base, por ejemplo NASA GIBS (D36), sin montar un segundo motor.

## Tiempo

Todo valor de transporte lleva zona y se normaliza a UTC. Un instante no recibe una hora de fin inventada. Un intervalo usa inicio inclusive y fin exclusive. Un producto de un día cuyo proveedor cierra en `23:59:59.999Z` se guarda hasta la medianoche siguiente, y el `time_end` original queda en la calidad. Si no se conoce cuándo estuvo disponible el dato, `availability.status` es `unknown`; no se copia la hora de observación.

## Geometría y unidades

Coordenadas GeoJSON en orden longitud, latitud, WGS84. La extensión es `west`, `south`, `east`, `north`. Si cruza el antimeridiano, `crosses_antimeridian` es verdadero y `west` es mayor que `east`: el área va de `west` hasta 180 y de -180 hasta `east`. Una línea o anillo que salta más de 180 grados se rechaza. El rol `region_anchor` exige `region_id`. El rol `grid_cell` exige `grid_id`. Un producto mallado puede tener extensión sin convertirse en un punto.

La unidad viaja con el valor presente. Cero es un valor medido válido. Un faltante no tiene valor ni unidad. La magnitud sísmica conserva `magType` (`mww` en la muestra) y no se traduce a otra escala. La profundidad USGS queda como posición vertical en kilómetros, no como el valor científico.

## Procedencia y modos

Cada registro real o demo lleva fuentes, activo, colección, versión, licencia cuando se conoce, calidad e instante de ingesta. `retrieval` distingue `viability_sample`, `demo_fixture` y, más adelante, `live`.

La probabilidad usa `state: absent` con valor nulo, o `state: defined` con un número de 0 a 1 y una definición. Un pronóstico exige inicialización, emisión no anterior, ventana de validez y un valor o una probabilidad definida.

## Catálogo

El JSON original es la fuente del catálogo. La validación encontró 48 fuentes, 26 variables y 31 fenómenos, sin IDs duplicados ni referencias rotas. D36, D37, D38, D39 y D40 no alimentan un fenómeno: son imagen, descubrimiento, documentación del modelo de lenguaje, validación y el desafío. V14, V18, V21 y V22 mencionan en prosa insumos que no son IDs del catálogo. Todos los fenómenos siguen en «Especificado sin implementar», mapeado al estado `specified`.

El estado de integración vive en `data/operational/source_integration.json`. Lo que no está ahí queda `documented`.

## Primer flujo real

La candidata del primer flujo ambiental es **D02 NASA SMAP SPL3SMP_E**, porque la referencia visual muestra humedad del suelo y F11 es prioridad P1. CMR respondió 200 con metadatos de un gránulo (4719 bytes). El HDF no se descargó: hace falta Earthdata y CMR informa un archivo de cientos de megabytes. Variables: `EARTHDATA_USERNAME` y `EARTHDATA_PASSWORD`.

Para ejercer el contrato con un registro real se usó **D21 USGS ComCat**, un GeoJSON público de un evento (1155 bytes, HTTP 200). Es otra fuente, no un sustituto de la humedad. No hay pronóstico sísmico derivado de esa muestra. `GET /signals?phenomenon_id=F11&mode=real` responde no disponible por credencial y no incluye el valor sintético del demo.

## Interfaz de la fase 02

La pantalla de entrada es `ObservatoryApp`. El adaptador `mountGlobe` sigue siendo el único lugar que crea el visor. Los tokens están en `apps/web/src/styles/tokens.css`.

El PNG mide 1672×941. El layout usa 17,1 % para filtros, el resto central para el globo y 26,1 % para el inspector, con barra superior de 48 px y franja temporal de 78 px. Esas relaciones salen de la imagen, no de una grilla genérica.

El escenario Amazonía central vive en `apps/web/src/demo/scenario.ts`. Los conteos de la barra central son la suma de los tipos de información activos de ese archivo. El «31 fenómenos» sale de `GET /catalog/phenomena` y, si la API no responde, se muestra no disponible. La búsqueda, la agrupación en el globo y el análisis completo quedan explícitamente pendientes. No se conectó ningún proveedor científico.

## Lo que esta fase no incorpora

PostgreSQL, PostGIS, Redis, colas, cuentas de Copernicus y el runtime de Qwen. No son un problema de instalación de la pantalla local: son trabajo de fases posteriores o accesos científicos todavía cerrados.
