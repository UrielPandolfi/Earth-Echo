# Fase 06 Series regionales y análisis de tendencias

## Objetivo de esta ejecución

Implementá la capacidad central de investigación de Earth Echo: elegir una región, variable y período, visualizar su historia y analizar qué cambió, cuánto y con qué incertidumbre. La experiencia debe cubrir el núcleo de Earth System Trend Detective y conservar el diseño del observatorio. Esta fase agrega análisis científico reproducible, sin confundir una tendencia histórica con un pronóstico futuro.

## Instrucciones de ejecución que se aplican a esta fase

Actuá como responsable de implementar Earth Echo en el proyecto abierto en Cursor. Ejecutá esta fase y dejá código funcionando. Empezá inspeccionando el estado real del repositorio, sus instrucciones y lo terminado en fases anteriores. Si encontrás trabajo existente correcto, continuá desde ahí. Conservá los cambios del usuario y evitá reescrituras generales que no sean necesarias para este objetivo.

Localizá y leé `Earth_Echo_Especificacion.md`, `Earth_Echo_Catalogo.json` y la imagen de referencia cuyo nombre empieza con `Earth Echo Global Environmental Observatory`. Si sus nombres difieren, resolvelos por los archivos reales del proyecto y registrá las rutas. La captura del explorador de Windows sirve para identificar archivos, pero la referencia visual es el PNG de la aplicación. Consultá también `AGENTS.md`, `PLAN.md`, `PROGRESS.md` y las decisiones técnicas existentes. Estos tres documentos originales son referencias que deben conservarse; agregá esquemas, configuración y notas aparte.

El PNG gobierna el diseño visual. La especificación y el catálogo gobiernan el significado de los datos, sus fuentes y sus limitaciones. Los valores y gráficos de la imagen son ilustrativos y no constituyen un dataset. El catálogo es una especificación de capacidades candidatas, no un archivo de observaciones ni un motor predictivo ya implementado. Una fuente documentada, una fuente conectada y un modelo evaluado son estados distintos.

Trabajá con autonomía en decisiones reversibles. Consultá documentación oficial vigente para APIs y bibliotecas, elegí versiones compatibles y conservá lockfiles. Verificá las funciones que realmente existan en la versión instalada. No reemplaces una dificultad con una dependencia adicional sin justificarla. Pedí información solo cuando falte algo imprescindible, como una credencial o una decisión de costo; mientras tanto avanzá con trabajo independiente y explicá el bloqueo concreto. Nunca solicites secretos por el chat: indicá el nombre de la variable y cómo configurarla localmente.

No adelantes funcionalidades de otra fase como si ya estuvieran terminadas. Implementá únicamente las interfaces mínimas que la fase actual necesite para extenderse después. Evitá clases base, repositorios genéricos y sistemas de plugins sin una segunda implementación real que los justifique. La separación entre UI, globo, datos, conectores y ciencia sí debe mantenerse. La lógica científica no vive dentro de componentes visuales.

Los datos simulados pertenecen a un modo DEMO explícito. La aplicación nunca cambia silenciosamente de REAL a DEMO cuando falla una fuente. Un resultado sin datos suficientes queda no disponible. No inventes probabilidades, confianza, causalidad, fechas de desastres, conexiones científicas ni indicadores de estado saludable. Todo contador debe representar una consulta definida. Conservá origen, unidades, calidad, tiempo y alcance de cada resultado.

Verificá lo que cambies con comprobaciones útiles: tipos y compilación, cálculos e integración cuando correspondan, interacción y captura cuando cambie la UI. No agregues tests que solo reproduzcan literalmente la implementación ni métricas de cobertura como sustituto de comprobar comportamiento. Si no podés ejecutar una herramienta, distinguí la limitación del resultado verificado. Una captura del PNG de referencia no es evidencia de la aplicación construida.

Al terminar, actualizá `PROGRESS.md` con trabajo completo, evidencia, limitaciones y siguiente paso. Registrá decisiones duraderas en el documento correspondiente, sin duplicar todo el historial. Entregá comandos para ejecutar, rutas o URL locales reales y una lista breve de comprobaciones efectivamente ejecutadas. Si Git está disponible y configurado, creá un commit local acotado con los archivos propios de esta fase. No incluyas secretos, archivos gigantes de datos ni cambios ajenos; no publiques ni fuerces pushes. Cerrá esta fase con su reporte y esperá el siguiente prompt.


## Elegir un caso de análisis con datos suficientes

Partí de la variable real de la fase 05 si tiene una historia apropiada. Si solo hay unas pocas observaciones recientes, ampliá un subconjunto histórico de la misma colección o elegí una colección histórica compatible, documentando la decisión. No calcules una tendencia climática convincente con unos días de datos para llenar un gráfico.

Definí explícitamente región, unidad, agregación temporal, período de referencia y período analizado. Un cambio de producto o versión puede generar discontinuidades. No mezcles dos fuentes solo porque sus variables tienen nombres parecidos. Si las combinás, justificá compatibilidad y mostrala en la procedencia.

Usá un caso real pequeño como recorrido principal y datos sintéticos controlados exclusivamente para verificar métodos. Las series sintéticas pueden tener pendiente conocida, estacionalidad, huecos y ruido. Deben quedar separadas de los resultados REAL.

## Selección de región y extracción

Permití seleccionar una región disponible, un rectángulo o un polígono razonable según lo que el motor y el backend ya admiten. Validá geometría, área mínima y máxima y cruce del antimeridiano. Evitá un editor GIS completo si una selección acotada resuelve el caso.

Extraé valores usando máscaras, fracción de cobertura y ponderación por área cuando corresponda a la malla. No hagas un promedio ingenuo de celdas de latitudes diferentes si ese cálculo cambia el significado del agregado. Declarar el método es parte de la salida.

Para variables acumuladas, flujos y promedios, definí agregaciones distintas. El total de lluvia de un mes no es el promedio de tasas sin integrar duración. Las medias temporales deben considerar la cobertura válida y no rellenar días faltantes con cero. Calculá y devolvé cantidad de observaciones, intervalos esperados, cobertura y huecos.

La extracción debe ser reproducible: misma selección, activos y versión de método producen el mismo resultado. Guardá la definición de la consulta y los IDs de activos usados. Aplicá cache cuya clave incluya todos los parámetros que cambien el significado.

## Anomalías y climatología

Permití comparar una serie con una referencia histórica definida. Explicá si la anomalía se expresa en unidades absolutas, porcentaje relativo o percentil. No uses una anomalía porcentual cuando el denominador puede ser cero o cuando carece de sentido para esa variable.

La comparación debe respetar estaciones o meses equivalentes. Un descenso de vegetación en una época habitual de cosecha no se presenta automáticamente como deterioro ambiental. Si no hay suficiente cobertura para una referencia estacional razonable, devolvé esa limitación en lugar de crear una línea base arbitraria.

Para una vista exploratoria histórica, documentá el período de referencia completo. Para futuras pruebas de predicción, las climatologías se ajustarán solo con datos anteriores a la fecha de corte. Diseñá el servicio para poder pasar una referencia versionada, evitando una dependencia oculta de todo el futuro.

## Métodos de tendencia y significancia

Implementá un método simple y bien explicado como punto de partida: pendiente lineal con unidades por tiempo y un intervalo de incertidumbre apropiado. Evaluá si la estacionalidad y la autocorrelación requieren agregación, modelado, remuestreo por bloques o un método estacional. Si usás Mann Kendall y una pendiente robusta, verificá hipótesis, versión y tratamiento de estacionalidad.

No elijas el método que produzca el menor valor p. Fijá la configuración por caso de uso antes de ver el resultado. No uses la salida de una regresión estándar como si sus supuestos se cumplieran automáticamente. Si la serie no permite aplicar el método, la salida debe ser no evaluable con una razón.

Separá magnitud del cambio, significancia estadística e importancia práctica. Una tendencia no significativa no equivale a ausencia demostrada de cambio. Una tendencia significativa no demuestra su causa ni permite extrapolarla indefinidamente. Cuando se hagan pruebas sobre muchas regiones o celdas, aplicá una estrategia documentada de comparaciones múltiples o identificá claramente el análisis como exploratorio.

## Servicio de análisis y respuesta

Separá extracción, agregación, referencia, estimación y presentación. La UI no implementa fórmulas. La respuesta incluye serie, unidad, tiempo, cobertura, método, parámetros, pendiente, intervalo, estadístico y supuestos pertinentes, además de advertencias específicas y procedencia.

Usá identificadores de ejecución y versión de método. Si el procesamiento tarda, ejecutalo como trabajo y devolvé estado consultable, evitando bloquear indefinidamente una petición. Las consultas similares no deben crear trabajos duplicados. Los errores del método no se transforman en una pendiente cero.

Podés exportar el resultado como un archivo tabular y metadatos JSON con región, referencia y fuentes. La exportación debe conservar valores nulos y unidades; no se limita a una imagen del gráfico. Incluí atribución de los productos usados.

## Integración visual

Abrí el análisis desde una señal o región sin reemplazar el diseño completo. Usá el inspector para un resumen y una vista ampliada para el gráfico detallado. El usuario debe poder volver al globo conservando filtros, selección y tiempo.

Mostrá ejes con cantidades y unidades, período seleccionado, referencia, cobertura y método. Observaciones, tendencia y bandas deben tener leyendas consistentes. Los huecos se ven como huecos cuando corresponda. No suavices la línea de una forma que sugiera observaciones inexistentes.

Permití comparar dos períodos o regiones únicamente si sus unidades y agregaciones son compatibles. Una explicación breve en lenguaje claro puede generarse mediante plantillas deterministas: todavía no es necesario conectar una IA para explicar pendiente, rango y cobertura.

## Criterios de aceptación

- Hay un recorrido real de selección geográfica, historia, gráfico y tendencia.
- La agregación espacial y temporal tiene definición y pruebas con resultados conocidos.
- Los métodos recuperan una pendiente conocida y se comportan correctamente con huecos y casos no evaluables.
- El resultado conserva referencia, configuración, incertidumbre y procedencia.
- Se diferencian cambio, significancia y predictibilidad.
- Una exportación permite reproducir el análisis.
- La UI conserva su composición y los gráficos son legibles en los tamaños de escritorio fijados.

## Reporte de cierre

Informá variable, región, cobertura histórica y métodos implementados. Entregá un ejemplo real reproducible, verificaciones independientes y límites estadísticos pendientes. Explicá qué capacidades quedan listas para ampliar en la fase 07 y qué configuración debe preservarse para evaluación temporal en la 08.
