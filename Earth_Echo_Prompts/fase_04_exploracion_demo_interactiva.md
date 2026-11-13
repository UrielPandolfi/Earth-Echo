# Fase 04 Exploración completa con datos de demostración

## Objetivo de esta ejecución

Convertí la pantalla y el globo de las fases anteriores en una experiencia de exploración completa. Al terminar, la aplicación debe parecerse visualmente a la referencia y permitir usar filtros, capas, agrupaciones, inspector, búsqueda y tiempo con datos simulados coherentes. La demostración tiene que usar los contratos que después utilizará el backend real. Esta fase no conecta la ciencia al aspecto de datos inventados: identifica de manera visible todo el escenario DEMO.

## Instrucciones de ejecución que se aplican a esta fase

Actuá como responsable de implementar Earth Echo en el proyecto abierto en Cursor. Ejecutá esta fase y dejá código funcionando. Empezá inspeccionando el estado real del repositorio, sus instrucciones y lo terminado en fases anteriores. Si encontrás trabajo existente correcto, continuá desde ahí. Conservá los cambios del usuario y evitá reescrituras generales que no sean necesarias para este objetivo.

Localizá y leé `Earth_Echo_Especificacion.md`, `Earth_Echo_Catalogo.json` y la imagen de referencia cuyo nombre empieza con `Earth Echo Global Environmental Observatory`. Si sus nombres difieren, resolvelos por los archivos reales del proyecto y registrá las rutas. La captura del explorador de Windows sirve para identificar archivos, pero la referencia visual es el PNG de la aplicación. Consultá también `AGENTS.md`, `PLAN.md`, `PROGRESS.md` y las decisiones técnicas existentes. Estos tres documentos originales son referencias que deben conservarse; agregá esquemas, configuración y notas aparte.

El PNG gobierna el diseño visual. La especificación y el catálogo gobiernan el significado de los datos, sus fuentes y sus limitaciones. Los valores y gráficos de la imagen son ilustrativos y no constituyen un dataset. El catálogo es una especificación de capacidades candidatas, no un archivo de observaciones ni un motor predictivo ya implementado. Una fuente documentada, una fuente conectada y un modelo evaluado son estados distintos.

Trabajá con autonomía en decisiones reversibles. Consultá documentación oficial vigente para APIs y bibliotecas, elegí versiones compatibles y conservá lockfiles. Verificá las funciones que realmente existan en la versión instalada. No reemplaces una dificultad con una dependencia adicional sin justificarla. Pedí información solo cuando falte algo imprescindible, como una credencial o una decisión de costo; mientras tanto avanzá con trabajo independiente y explicá el bloqueo concreto. Nunca solicites secretos por el chat: indicá el nombre de la variable y cómo configurarla localmente.

No adelantes funcionalidades de otra fase como si ya estuvieran terminadas. Implementá únicamente las interfaces mínimas que la fase actual necesite para extenderse después. Evitá clases base, repositorios genéricos y sistemas de plugins sin una segunda implementación real que los justifique. La separación entre UI, globo, datos, conectores y ciencia sí debe mantenerse. La lógica científica no vive dentro de componentes visuales.

Los datos simulados pertenecen a un modo DEMO explícito. La aplicación nunca cambia silenciosamente de REAL a DEMO cuando falla una fuente. Un resultado sin datos suficientes queda no disponible. No inventes probabilidades, confianza, causalidad, fechas de desastres, conexiones científicas ni indicadores de estado saludable. Todo contador debe representar una consulta definida. Conservá origen, unidades, calidad, tiempo y alcance de cada resultado.

Verificá lo que cambies con comprobaciones útiles: tipos y compilación, cálculos e integración cuando correspondan, interacción y captura cuando cambie la UI. No agregues tests que solo reproduzcan literalmente la implementación ni métricas de cobertura como sustituto de comprobar comportamiento. Si no podés ejecutar una herramienta, distinguí la limitación del resultado verificado. Una captura del PNG de referencia no es evidencia de la aplicación construida.

Al terminar, actualizá `PROGRESS.md` con trabajo completo, evidencia, limitaciones y siguiente paso. Registrá decisiones duraderas en el documento correspondiente, sin duplicar todo el historial. Entregá comandos para ejecutar, rutas o URL locales reales y una lista breve de comprobaciones efectivamente ejecutadas. Si Git está disponible y configurado, creá un commit local acotado con los archivos propios de esta fase. No incluyas secretos, archivos gigantes de datos ni cambios ajenos; no publiques ni fuerces pushes. Cerrá esta fase con su reporte y esperá el siguiente prompt.


## Modelo del escenario de demostración

Implementá un repositorio de fixtures o un proveedor DEMO detrás de la misma interfaz de consulta que utilizará el proveedor REAL. No distribuyas arrays independientes por componentes ni hagas que un componente reconozca un modo por nombres de variables. Incluí IDs estables, geometría, tipo de información, categoría, variable, unidad, validez temporal y fuente prevista. Una fuente prevista es distinta de una fuente que produjo una medición real.

Generá el conjunto de demostración de forma determinista, con una semilla registrada. Ofrecé un escenario visual de apertura que reproduzca la densidad y selección del PNG, y un conjunto más grande destinado a rendimiento. Los puntos pueden representar datos simulados sobre ubicaciones geográficas válidas, sin atribuir desastres reales a ciudades o fechas reales. La pantalla debe indicar DEMO sin obligar a leer un tooltip.

Incluí observaciones, condiciones de peligro y pronósticos ilustrativos en categorías diferentes. Un indicador no es una probabilidad. Si el ejemplo usa un porcentaje, definí si representa anomalía, cobertura, percentil o una probabilidad simulada. Para evitar confusión, preferí valores ilustrativos de variables e índices con unidades correctas y reservá los porcentajes de ocurrencia para etapas científicas posteriores.

## Estado único de exploración

Centralizá selección de región, capas activas, filtros, señal seleccionada, instante temporal, ventana y modo de datos. El dominio de la selección y el estado de la cámara pueden tener responsabilidades distintas. Usá IDs y selectores derivados para impedir que contadores y mapa se calculen con filtros diferentes.

Definí qué representa cada contador: total del dataset, total tras filtros, total dentro de la vista y cantidad de agrupaciones renderizadas. Mostrá la distinción que sea relevante en la UI. La suma de categorías no debe duplicar señales con múltiples etiquetas sin una explicación. No copies los números del PNG como constantes de producción.

Si una selección deja de cumplir un filtro, decidí un comportamiento explícito: cerrar el inspector o mantenerlo marcado como fuera del filtro. Implementá una de esas alternativas de forma consistente. Si no quedan resultados, la pantalla muestra vacío y explica cómo recuperarse. Las fallas de carga, ausencia de resultados y ausencia de cobertura son estados diferentes.

## Símbolos y agrupación espacial

Conectá los símbolos definidos en la UI: círculo para observación, triángulo para condición de peligro y rombo para pronóstico, o las formas aprobadas en el diseño. La leyenda debe corresponder exactamente a los objetos renderizados. Un cambio de categoría no puede alterar arbitrariamente el significado de una forma.

Agrupá señales cercanas según el nivel de detalle. El número de una agrupación es la cantidad de registros que representa después de aplicar los filtros y la selección temporal. No cuentes como nuevas señales los grupos generados. Al acercarse o seleccionar un grupo, se puede ampliar la región o mostrar sus elementos. Evitá agrupaciones que mezclen puntos alejados a ambos lados del antimeridiano por una resta simple de longitudes.

Utilizá una técnica compatible con el motor y con el volumen objetivo. Evitá crear miles de componentes DOM flotantes o listeners independientes cuando una colección del motor o una selección centralizada resuelve el problema. Ocultá objetos posteriores a la Tierra y aplicá prioridades a rótulos. No llenes el globo de etiquetas superpuestas para aparentar más información.

## Capas ambientales y leyendas

Mostrá ejemplos de campos continuos como humedad, temperatura y precipitación mediante capas geográficas, no mediante un pin por celda. El proveedor DEMO puede generar un ráster pequeño y reproducible, pero tiene que declararlo simulado. Una textura de color decorativa no es un análisis científico.

Al activar un campo, actualizá leyenda, unidad, rango y fecha. Explicá cuándo el valor es absoluto y cuándo es anomalía. No uses la misma barra para dos magnitudes incompatibles. Definí una composición comprensible cuando se activan varios campos: opacidad, orden y una leyenda vinculada a cada capa, o limitá las capas activas simultáneas con una razón de legibilidad.

La ausencia de valor en una celda debe verse transparente o con una máscara identificada. No la conviertas en un extremo de la escala. El usuario debe poder apagar y volver a encender una capa sin duplicarla ni perder sus metadatos.

## Inspector y búsqueda

Seleccionar una señal actualiza título, región, tipo, valores, unidad, gráfico, horizonte, fuentes previstas y límites. Las pestañas Resumen, Datos y Antecedentes muestran contenido conectado con esa selección. El análisis ampliado debe abrir una vista real con información del fixture, no repetir un bloque estático para cualquier punto.

Implementá búsqueda local de regiones y señales disponibles. Los resultados deben diferenciar una región de un evento y permitir centrar la cámara. Evitá depender de un geocodificador externo todavía no elegido. Incluí selección accesible mediante lista o búsqueda para que el mouse no sea la única forma de llegar a un punto del globo.

Los gráficos deben tener cantidad, unidad, eje temporal y una separación entre observado y pronosticado. Los intervalos inciertos no representan error de medición por defecto; su significado viene del registro. Un dato faltante interrumpe la serie cuando corresponde. Mostrá timestamps legibles y conservá UTC internamente.

## Tiempo y reproducción

El control temporal debe consultar realmente otro estado del escenario. Cambiar la etiqueta de fecha sin cambiar las señales o series disponibles no completa la interacción. Las observaciones no aparecen en fechas anteriores a su disponibilidad y los pronósticos conservan su inicialización y plazo.

Implementá avance, pausa, salto a último dato y límites de reproducción. Si una capa tiene cadencia diaria y otra horaria, definí cómo se selecciona el último dato válido de cada una y qué tolerancia se permite. No interpoles una lectura diaria para fingir observaciones cada minuto. Al cambiar filtros o región, evitá que una petición antigua sobrescriba la selección nueva.

## Criterios de aceptación

- Todos los controles visibles tienen una acción útil o un estado deshabilitado explicado.
- Filtros, mapa, contadores e inspector describen el mismo conjunto.
- Agrupaciones, selección y ocultamiento posterior funcionan con el escenario pequeño y el grande.
- La búsqueda permite recuperar una señal sin depender de hover.
- La línea temporal cambia el contenido y respeta intervalos de validez del fixture.
- Las capas y gráficos muestran unidades, leyendas y ausencia de datos correctamente.
- Se prueba cambiar filtros rápidamente, vaciar resultados, desmontar capas y volver al encuadre inicial.
- Las capturas del escenario de apertura conservan la composición del PNG.

## Reporte de cierre

Mostrá el recorrido de demostración, volumen de registros usado, comportamiento observado y capturas reales. Informá qué adaptador se reemplazará en la fase 05 y qué componentes ya están preparados para datos externos. Al terminar esta fase debe existir una aplicación visualmente convincente e interactiva, identificada como DEMO.
