# Arquitectura

La humedad relativa derivada IFS usa la razón de presión de vapor a Td y saturación a T de FAO-56, ecuaciones 10/11/14, en %. Comparte con VPD los dos mensajes GRIB completos y su archivo SHA; no agrega otra descarga. Es instantánea respecto de agua líquida, limitada conservadoramente a 0 ≤ Td ≤ T ≤ 50 °C; hielo, supersaturación y faltantes son null, sin recorte a 0/100 %. No representa humedad del suelo, del combustible ni probabilidad.

El análisis RAPID `rapid-annual-ols-2005-2023-v1` vive en ciencia/ingestión, separado de la interfaz. Usa medias mensuales nativas del activo ya retenido, años calendario completos 2005–2023 y pesos por días gregorianos. Un año con un mes ausente permanece null; pendiente OLS sólo con al menos 15 de los 19 años válidos, todos con igual peso. Conserva período, fórmula, parámetros, entrada SHA y resultado escalar con unidad en el contrato. Es análisis descriptivo regional, sin significación estadística o pronóstico. Los contadores separan campos calculados, análisis calculados, indicadores importados y señales de evento. No hay otra descarga ni duplicación del NetCDF compartido.

Decisión del 13 de noviembre de 2026. El repositorio no tenía aplicación previa.

## Stack

## Integraciones posteriores a fase 10

Los productos científicos verificados se conservan en `data/real/products`, con originales por SHA-256, revisiones decodificadas y un puntero `current.json` publicado atómicamente después de validar. Las mallas regulares se sirven como campos; sus celdas no son señales. El contrato Pydantic `ScientificProduct` incluye unidad nativa, período, resolución, máscara, método de submuestreo y comprobación independiente; genera JSON Schema y TypeScript. El recorte/historia/experimento SST previo conserva su almacenamiento y su alcance.

CRW mundial usa una muestra regular cada 20 centros (1° para visualización) de la malla nativa de 0,05°. Se conserva cada valor muestreado sin promediar ni atribuirle resolución mayor; la imagen interpola visualmente por vecino cercano. Los ejes se ordenan explícitamente y los bordes se deducen de los centros. HotSpot/DHW conservan `mask=0`; tierra, hielo y faltantes quedan transparentes. La descarga CSV de una celda comprueba la decodificación NetCDF.

La actualización corre en el lifespan de la API o en `npm run refresh:watch`, con un lock de sistema operativo compartido y estado persistido antes de I/O. Tras una caída, el lock se libera por el sistema y la tarea vuelve a ser elegible en 15 minutos. No se agregan servidor ni base de datos. Cada producto tiene cadencia propia, dos intentos HTTP transitorios como máximo y hasta cuatro revisiones; cada descarga está acotada. Las fechas de intento, descarga satisfactoria y cambio son distintas; las del producto conservan observación, emisión, inicialización y validez cuando existen. SWPC no proporciona emisión/inicialización en el JSON: quedan null, sin copiar la recuperación como emisión.

En REAL se conserva la cámara amplia; encuadrar un producto es una acción explícita. El inspector existente admite fichas de producto y originales descargables. El catálogo original permanece inmutable; `docs/integraciones.md` y `data/operational/integration_matrix.json` registran evidencia independiente.

MODIS usa subconjuntos científicos ORNL DAAC, con entero original, bandas QA y metadatos de escala incluidos en un mismo activo compartido por NDVI/EVI o LST día/noche. La proyección sinusoidal es esférica con R=6371007.181 m; pyproj reproyecta por vecino más cercano a WGS84, sin rellenar nubes. Se conserva el intervalo del compuesto y el identificador de procesamiento, sin inventar una versión que REST no informa.

IFS usa el índice público oficial para obtener cinco mensajes GRIB del paso +24 h por Range. ecCodes verifica parámetro/unidad, escaneo y tiempos contra el índice; la lluvia conserva 0–24 h y convierte m→mm. El GRIB original contiene la resolución científica; la UI recibe centros muestreados a 1°. Una misma corrida no se descarga para cada fenómeno. El presupuesto del almacén nuevo es 256 MB por defecto, configurable en el servidor; se amplió desde 128 MB tras medir uso y disco disponible. Al agotarlo, una actualización falla explícitamente conservando lo válido.

Las evaluaciones orbitales y probabilidades OAF no se convierten en puntos de impacto. `ProductSample` requiere definición si contiene probabilidad. OAF conserva la región y modelo del proveedor, y se coteja con el checksum del manifiesto ComCat. Los mensajes CAP preservan prueba/cancelación y expiración; sin polígono no se reutiliza el epicentro como geometría de aviso. GVP es inventario estático con símbolos grises, sin precursores. ONI es historia de medias móviles, separada del diagnóstico ENSO operativo.

Los GeoTIFF/HDF5 grandes usan rangos HTTP acotados, con ETag fuerte o Last-Modified para coherencia, validación de Content-Range y presupuesto de bytes/peticiones/tiempo. Un archivo JSON conserva URL, tamaño, identidad y bloques originales base64 para reproducir la decodificación sin red. LHASA usa ventana nativa y maneja su eje latitudinal ascendente; MHW comparte bloques entre tres plazos. Las probabilidades mensuales importadas conservan su definición experimental y no validan el modelo SST propio.

La identidad de revisión incluye metadatos científicos y método, además del archivo. Solo se permite ignorar cambios de bytes si un conector calculó un checksum explícito de todos los valores y metadatos científicos del activo (ERDDAP agrega tiempos de petición en history). Un campo de visualización igual no demuestra igualdad del original. La lista resumida excluye mallas y muestras; se solicita el detalle al seleccionar para evitar transferir todos los campos en cada apertura.

En Windows, `ops/windows/install-refresh.ps1` registra e inicia una tarea local al iniciar sesión, con el Python del proyecto y sin ventana. Comparte el lock con la API; no se solapan descargas. Estado efímero y heartbeat permanecen fuera de Git. Instalación, parada y recuperación se describen en `docs/actualizacion.md`.

El planificador mantiene el lock y estado en el padre y ejecuta un trabajo concreto por hijo, sin ventana ni planificador anidado. Un límite total de 180 segundos incluye DNS/I/O/decodificación; al vencer, el hijo se termina y se espera antes de continuar. Esto evita que una conexión que sigue goteando bytes bloquee todas las fuentes aun con timeout de socket. Los secretos no aparecen en argumentos. La publicación atómica conserva el válido anterior ante una terminación.

Las trayectorias importadas reutilizan GeoJSON y extensión existentes, con tiempos/calidad en registros vinculados. IBTrACS conserva centros, agencia y período nativo del viento sin armonización. Se cortan las líneas al antimeridiano; los vértices de borde son solo dibujo. La colección de polilíneas vive dentro del mismo adaptador Cesium, sin otro visor. La cámara cambia solo por acción explícita y el inspector sirve también para seleccionar los sistemas.

Las áreas CAP conservan estado y urgencia aunque el mensaje sea pasado; `todate` describe el evento y no reemplaza `expires`. Se cotejan revisiones entre RSS y CAP. Partición de polígonos usa GEOS/Shapely, rechaza originales inválidos y conserva anillos/partes, sin reparar ni usar bbox como área afectada. Las fechas operativas se muestran en el inspector por trabajo concreto; una falla mantiene el producto científico, con su fecha y error visibles.

GEBCO usa subconjuntos numéricos OPeNDAP y TID de la misma edición/coordenadas. La comprobación binaria detecta magic HDF5/CDF antes de elegir lector; no intenta abrir un NetCDF clásico como HDF5 recorriendo el archivo. `quality_values` se alinea por celda y su leyenda identifica tipo de fuente, sin convertirlo en confianza. El datum nominal MSL y su heterogeneidad se conservan; no se usa la grilla para navegación ni hidráulica.

ASIS se resuelve desde el catálogo FAO y se bloquea por OBJECTID, estación y máscara de cultivo. Solo se publican exportaciones F32 sin renderer que coinciden con getSamples, a centros nativos. Los overviews del servicio no se tratan como valores nativos cuando el cotejo discrepa. Códigos especiales fuera del dominio porcentual se conservan por celda y enmascaran sin adivinar categorías. Una ventana dekadal de edición no reemplaza el período acumulado del indicador desde el comienzo del ciclo.

Las observaciones categóricas usan `ProductSample.category`, sin codificar presencia/ausencia como un número físico inventado. RAMSES conserva incluso los reportes de ausencia y separa fecha UTC publicada de hora textual sin definición adicional. Extensión por producto habilita foco explícito de reportes regionales. Búsqueda/paginación del inspector permiten seleccionar cualquier registro aun si varios puntos comparten coordenadas; el contador sigue contando reportes de la consulta, no individuos o enjambres.

Las variables físicas derivadas viven en ciencia pura, con orquestación separada de ingestión y UI. Rapidez a 10 m usa norma u/v; VPD usa FAO-56 sobre T/Td con dominio conservador líquido 0–50 °C. No son detectores de eventos ni modelos entrenados. Contratos preservan fórmula, parámetros, unidades, período sin climatología, hashes de entradas y método versionado. Se coteja contra los GRIB nativos con otra aritmética (sqrt/Decimal), sin duplicar descargas ni transformar software correcto en validación predictiva.

HydroATLAS se lee como BasinATLAS v1 nivel 03, sin sustituirlo por otro inventario. Se extraen SHP/SHX/DBF/PRJ mediante rangos ZIP, con CRC32 y replay offline; el límite de expansión evita descargar/descomprimir la colección mundial de niveles completos. Una única caché de miembros se reutiliza al comprobar la identidad del archivo Figshare. Las unidades HYBAS_ID=603… son el alcance sudamericano. SUB_AREA/UP_AREA/topología mantienen valores y unidades nativos; los otros atributos permanecen en el original sin interpretación. Para dibujar anillos que se tocan se usa GEOS make_valid(structure), solo si conserva área planar relativa a 1e-10 y bbox a 1e-10°, con calidad explícita y original intacto. Luego se simplifica con topología a 0.01°; no se recalcula el área científica. Transformaciones fuera del criterio quedan sin dibujo. El primer acceso de 31,7 MB medido justifica 420 s totales para este trabajo (`EARTH_ECHO_HYDROATLAS_TIMEOUT_SECONDS`, 30–600), sin extender los otros trabajos.

FIRMS selecciona NOAA-20 C2 desde el índice público oficial, CSV y SHP de Sudamérica. Se cotejan todos los píxeles entre formatos; una revisión desalineada se rechaza. FRP permanece MW, brillo K, adquisición UTC y calidad categórica nativa. `map_eligible` separa máscara visual de conservación científica: low/FRP ausente no dibujan punto, pero sus coordenadas y valores siguen en tabla/original. Una respuesta vacía con formatos coherentes es válida, sin afirmar ausencia regional de fuego. El contador distingue observaciones, registros históricos, indicadores importados, campos y señales calculadas; no suma inventarios o celdas como observaciones.

Los puntos REAL se agrupan ya en la cámara inicial, con tamaño angular dependiente de altura. Un presupuesto de 1.500 símbolos fuerza agrupación adicional aun en conjuntos densos; cada grupo suma sus registros originales y la selección queda separada. No se descartan observaciones para aliviar el visor y la tabla conserva acceso individual. Las pruebas con 20.000 entradas verifican límite, conservación de cantidades y ambos lados del antimeridiano. El límite responde al bloqueo observado al enviar 15.000 billboards a la vista inicial.

Los reportes de actividad GVP se separan del inventario estático. Se coteja RSS con CAP 1.1 y se conserva el período local textual; el UTC por registro es emisión, no instante de actividad. Un circle CAP de radio cero es ubicación del volcán, nunca área afectada. Fuente atrasada permanece archivo histórico con su fecha; una página web más reciente no autoriza a cambiar la fecha del feed. El desfase de zona entre canal RSS e ítems/CAP se conserva sin inventar una corrección.

RGI7 usa atributos científicos G/C del espejo académico público OGGM mediante rangos acotados, sin afirmar descarga de huellas NSIDC. Solo filas completas del fragmento inicial de Alaska se publican; la ventana no representa toda la región. Área km² y puntos representativos nativos (no centroides) permanecen con su ID original. src_date sin zona se conserva como texto de fecha fuente, sin inventar UTC. Un área/punto se coteja entre producto glaciar G y complejo C coincidentes; guía RGI7 fija unidades y semántica. El inventario estático no habilita observación o predicción de GLOF.

Las series regionales integradas usan representación `time_series`, separada de `planetary`: RAPID 26,5° N no es índice planetario ni malla mundial. El NetCDF completo de transportes se comparte entre AMOC/calor/agua dulce; `Units` distingue Sv/PW y tiempo CF gregorian es coordenada mensual representativa, no medición instantánea. Fecha de creación sin hora/zona no se convierte en emisión UTC. La serie publicada se conserva incluso cuando un intento de reconstrucción desde perfiles discretos difiere; la verificación usa valores binarios y estadísticas oficiales, sin declarar validado otro método. El gráfico conserva todos los valores, reduce solo rótulos y corta la línea en faltantes, sin interpolarlos.

Sentinel-3A OC4Me L3 llega por una distribución pública modificada de Copernicus en NOAA; pertenece a D25 y no sustituye NASA OceanColor D17 o las escenas CDSE todavía no descargadas. Se conserva el estado Experimental, la atribución exigida y el baseline temporal. graphics es overlay y nunca QA. La grilla mantiene NaN y valores que exceden colorBarMaximum: una paleta no define validez científica. `color_scale=log10` afecta sólo el color; contrato rechaza valores no positivos en esa presentación antes que ocultar un cero. Identidad científica conserva ejes, valores y todos los atributos, excluyendo únicamente dos líneas de historial añadidas por la petición ERDDAP; el procesamiento Sentinel-SAFE/cwutils permanece en el hash.

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
