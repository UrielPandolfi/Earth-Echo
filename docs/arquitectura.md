# Arquitectura

Decisión del 13 de noviembre de 2026. El repositorio no tenía aplicación previa.

## Stack

## Integraciones posteriores a fase 10

Los productos científicos verificados se conservan en `data/real/products`, con originales por SHA-256, revisiones decodificadas y un puntero `current.json` publicado atómicamente después de validar. Las mallas regulares se sirven como campos; sus celdas no son señales. El contrato Pydantic `ScientificProduct` incluye unidad nativa, período, resolución, máscara, método de submuestreo y comprobación independiente; genera JSON Schema y TypeScript. El recorte/historia/experimento SST previo conserva su almacenamiento y su alcance.

CRW mundial usa una muestra regular cada 20 centros (1° para visualización) de la malla nativa de 0,05°. Se conserva cada valor muestreado sin promediar ni atribuirle resolución mayor; la imagen interpola visualmente por vecino cercano. Los ejes se ordenan explícitamente y los bordes se deducen de los centros. HotSpot/DHW conservan `mask=0`; tierra, hielo y faltantes quedan transparentes. La descarga CSV de una celda comprueba la decodificación NetCDF.

La actualización corre en el lifespan de la API o en `npm run refresh:watch`, con un lock de sistema operativo compartido y estado persistido antes de I/O. Tras una caída, el lock se libera por el sistema y la tarea vuelve a ser elegible en 15 minutos. No se agregan servidor ni base de datos. Cada producto tiene cadencia propia, dos intentos HTTP transitorios como máximo y hasta cuatro revisiones; cada descarga está acotada. Las fechas de intento, descarga satisfactoria y cambio son distintas; las del producto conservan observación, emisión, inicialización y validez cuando existen. SWPC no proporciona emisión/inicialización en el JSON: quedan null, sin copiar la recuperación como emisión.

En REAL se conserva la cámara amplia; encuadrar un producto es una acción explícita. El inspector existente admite fichas de producto y originales descargables. El catálogo original permanece inmutable; `docs/integraciones.md` y `data/operational/integration_matrix.json` registran evidencia independiente.

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

## Globo

Sigue habiendo un solo motor, CesiumJS, sobre el elipsoide WGS84. No hay terreno 3D ni exageración vertical: el acceso al terreno de Cesium ion pide token. `CESIUM_ION_TOKEN` sigue fuera del bundle.

La base visual preferida es NASA GIBS (D36), capa estática Blue Marble Shaded Relief and Bathymetry, teselas Web Mercator públicas hasta el nivel 8. No es una observación del día. Si GIBS falla, queda Natural Earth II, incluido en CesiumJS y de dominio público. No hay una textura de nubes: una capa fija parecería meteorología actual.

`lightingMode` en `apps/web/src/globe/geography.ts` vale `presentation`: el globo se ve iluminado de frente y la atmósfera es moderada. No sigue al sol. El encuadre `americasPreset` mira longitud −64° y latitud −14° desde 13 200 km, con norte arriba. La cámara no baja de 250 km ni se aleja más de 28 000 km, y no se inclina por debajo del horizonte. No hay giro automático. `prefers-reduced-motion` anula la animación de vuelo. Un clic interrumpe el vuelo anterior.

`focusRegion` recibe una extensión en grados, con `crossesAntimeridian`. La conversión a la cámara está en `frameExtent`, sin Cesium. Los rótulos HTML se proyectan en cada frame y se ocultan si quedan detrás del planeta, fuera del área o encima de otro rótulo. Un arrastre no selecciona.

La tendencia no se calcula en la interfaz. El método fijado es `ols-monthly-anomaly-block-bootstrap-v1`: promedio diario ponderado por el coseno de la latitud, media mensual si el mes tiene al menos el 80 % de los días, anomalía en °C contra la media del mismo mes en 2014–2021, y recta de mínimos cuadrados en °C por año. El intervalo sale de remuestrear residuos en bloques de 12 meses con semilla fija. Menos de 96 meses, o una referencia con menos de ocho años en algún mes, deja la pendiente en null. Un hueco no se guarda como cero. El resultado dice que no es un pronóstico y que no identifica la causa. La serie histórica es el mismo recorte y la misma colección CoralTemp v3.1, de 2014 a 2025, pedida mes a mes porque un año entero recibe un error del proxy. `GET /v1/analyses/d15-sst` lee esa serie ya agregada.

`GET /v1/capabilities` separa observación, indicador, tendencia y pronóstico para los 31 fenómenos. D21 muestra sismos de magnitud mayor o igual a 5 como puntos. D28 muestra el Kp planetario como índice global, no como pines. D01, D02 y GloFAS siguen sin credencial. Las tareas de sismos y de Kp respetan una cadencia de una hora y de tres horas; si fallan, queda la instantánea anterior.

El Kp previsto de SWPC se archiva como pronóstico importado, con emisión y validez, y no se convierte en probabilidad. El experimento de anomalía de SST a un mes compara análogos, persistencia y climatología. La predicción se guarda antes de revelar el desenlace. Como la serie no trae `available_at`, el resultado queda como experimento retrospectivo y no como replay operativo. No superar a la persistencia no cambia el estado a validado.

El asistente vive en la API. Consulta tendencia, experimento, Kp, sismos y capacidades, y no escribe pronósticos. Un modelo compatible con la API de chat solo puede parafrasear ese resultado; si propone un número que no está en las herramientas, se descarta. La dirección y la clave se leen de `EARTH_ECHO_LLM_BASE_URL`, `EARTH_ECHO_LLM_MODEL` y `EARTH_ECHO_LLM_API_KEY` en el servidor. El navegador no puede elegir la URL. Si el modelo no está, el mapa y los análisis siguen, y la respuesta queda marcada como salida de las herramientas.

El modo REAL lee `GET /v1/sources/D15` y no reutiliza el generador demo. La primera fuente conectada es NOAA Coral Reef Watch, CoralTemp v3.1, variable `analysed_sst` en `degree_C`. IMERG (D01, colección `GPM_3IMERGHHE` versión 07) quedó en `credential_required`: GES DISC y PPS piden Earthdata. El recorte real es el Caribe occidental, del 8 al 11 de noviembre de 2026 a las 12:00 UTC, pedido a ERDDAP `noaacrwsstDaily` y guardado como NetCDF clásico. El índice local es SQLite en `data/real/d15`; PostGIS queda para cuando una consulta geográfica lo necesite. La clave de ingestión une fuente, colección, versión, variable, intervalo y recorte. El mismo checksum no crea otra revisión. Un checksum nuevo conserva la anterior. El valor del mapa es el promedio de las celdas válidas; el relleno −327,68 no entra. No hay HotSpot, DHW ni afirmación de blanqueamiento.

Las señales demo se dibujan en una colección de símbolos del mismo visor: círculo, triángulo y rombo. Al alejarse, las cercanas se agrupan por celdas que no cruzan el antimeridiano. El número del grupo es la cantidad de registros, no una señal nueva. La señal seleccionada queda fuera del grupo para seguir visible. Un campo ilustrativo, humedad, temperatura o precipitación, se pinta como una sola capa con celdas transparentes donde no hay valor. Se dibuja una capa por vez. `setSignals` y `setField` no recrean el `Viewer`.

El escenario sale de la semilla `earth-echo-demo-2026-11-13`. En el instante de referencia se ven 169 registros de apertura. El conjunto amplio agrega 1 202, incluidos dos puntos a ambos lados del antimeridiano. Cada registro tiene validez, disponibilidad y, si es pronóstico, inicialización. Un valor ausente queda en null. No hay probabilidades. Las fuentes son previstas, no conectadas. Los contadores cuentan ese conjunto filtrado. Si la selección deja de cumplir el filtro, la ficha permanece y avisa que no está en el mapa.

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

El escenario Amazonía central vive en `apps/web/src/demo/scenario.ts`. Los conteos de la barra central son la suma de los tipos de información activos de ese archivo. El «31 fenómenos» sale de `GET /catalog/phenomena` y, si la API no responde, se muestra no disponible. Ese cierre de la fase 02 no incluía búsqueda ni datos reales. La entrega actual está en `docs/entrega.md`.

## Lo que esta fase no incorpora

PostgreSQL, PostGIS, Redis, colas, cuentas de Copernicus y el runtime de Qwen. Siguen fuera de esta entrega. `GET /health` solo dice que el proceso vive. `GET /ready` mira los archivos locales y deja `providers_updated` en `not_checked`.
