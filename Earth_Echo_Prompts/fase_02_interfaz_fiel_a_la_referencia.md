# Fase 02 Interfaz de escritorio fiel a la referencia visual

## Objetivo de esta ejecución

Construí la pantalla principal de Earth Echo con una fidelidad visual alta respecto del PNG de referencia. Debe verse como la misma aplicación: tema oscuro, globo dominante en el área central, filtros a la izquierda, inspector a la derecha y exploración temporal abajo. El objetivo de esta fase es cerrar el diseño de escritorio y sus componentes. La integración definitiva del globo se completa en la fase 03 y la interacción ambiental completa en la 04.

## Instrucciones de ejecución que se aplican a esta fase

Actuá como responsable de implementar Earth Echo en el proyecto abierto en Cursor. Ejecutá esta fase y dejá código funcionando. Empezá inspeccionando el estado real del repositorio, sus instrucciones y lo terminado en fases anteriores. Si encontrás trabajo existente correcto, continuá desde ahí. Conservá los cambios del usuario y evitá reescrituras generales que no sean necesarias para este objetivo.

Localizá y leé `Earth_Echo_Especificacion.md`, `Earth_Echo_Catalogo.json` y la imagen de referencia cuyo nombre empieza con `Earth Echo Global Environmental Observatory`. Si sus nombres difieren, resolvelos por los archivos reales del proyecto y registrá las rutas. La captura del explorador de Windows sirve para identificar archivos, pero la referencia visual es el PNG de la aplicación. Consultá también `AGENTS.md`, `PLAN.md`, `PROGRESS.md` y las decisiones técnicas existentes. Estos tres documentos originales son referencias que deben conservarse; agregá esquemas, configuración y notas aparte.

El PNG gobierna el diseño visual. La especificación y el catálogo gobiernan el significado de los datos, sus fuentes y sus limitaciones. Los valores y gráficos de la imagen son ilustrativos y no constituyen un dataset. El catálogo es una especificación de capacidades candidatas, no un archivo de observaciones ni un motor predictivo ya implementado. Una fuente documentada, una fuente conectada y un modelo evaluado son estados distintos.

Trabajá con autonomía en decisiones reversibles. Consultá documentación oficial vigente para APIs y bibliotecas, elegí versiones compatibles y conservá lockfiles. Verificá las funciones que realmente existan en la versión instalada. No reemplaces una dificultad con una dependencia adicional sin justificarla. Pedí información solo cuando falte algo imprescindible, como una credencial o una decisión de costo; mientras tanto avanzá con trabajo independiente y explicá el bloqueo concreto. Nunca solicites secretos por el chat: indicá el nombre de la variable y cómo configurarla localmente.

No adelantes funcionalidades de otra fase como si ya estuvieran terminadas. Implementá únicamente las interfaces mínimas que la fase actual necesite para extenderse después. Evitá clases base, repositorios genéricos y sistemas de plugins sin una segunda implementación real que los justifique. La separación entre UI, globo, datos, conectores y ciencia sí debe mantenerse. La lógica científica no vive dentro de componentes visuales.

Los datos simulados pertenecen a un modo DEMO explícito. La aplicación nunca cambia silenciosamente de REAL a DEMO cuando falla una fuente. Un resultado sin datos suficientes queda no disponible. No inventes probabilidades, confianza, causalidad, fechas de desastres, conexiones científicas ni indicadores de estado saludable. Todo contador debe representar una consulta definida. Conservá origen, unidades, calidad, tiempo y alcance de cada resultado.

Verificá lo que cambies con comprobaciones útiles: tipos y compilación, cálculos e integración cuando correspondan, interacción y captura cuando cambie la UI. No agregues tests que solo reproduzcan literalmente la implementación ni métricas de cobertura como sustituto de comprobar comportamiento. Si no podés ejecutar una herramienta, distinguí la limitación del resultado verificado. Una captura del PNG de referencia no es evidencia de la aplicación construida.

Al terminar, actualizá `PROGRESS.md` con trabajo completo, evidencia, limitaciones y siguiente paso. Registrá decisiones duraderas en el documento correspondiente, sin duplicar todo el historial. Entregá comandos para ejecutar, rutas o URL locales reales y una lista breve de comprobaciones efectivamente ejecutadas. Si Git está disponible y configurado, creá un commit local acotado con los archivos propios de esta fase. No incluyas secretos, archivos gigantes de datos ni cambios ajenos; no publiques ni fuerces pushes. Cerrá esta fase con su reporte y esperá el siguiente prompt.


## Análisis visual obligatorio

Abrí el PNG y medí su tamaño real. Redactá un inventario breve de regiones visuales antes de implementar: barra superior, sidebar, área del globo, panel de detalle, leyenda, controles flotantes y barra temporal. Estimá proporciones y convertí esas relaciones en reglas de layout. Usá la captura como referencia, no como una sugerencia para diseñar otro dashboard.

La imagen muestra una aplicación de escritorio de alta densidad. Conservá paneles compactos, textos legibles, filas de datos y separadores finos. Evitá convertirla en una landing page con tarjetas gigantes y grandes títulos. No reemplaces el globo por una cuadrícula de métricas ni agregues secciones de marketing, onboarding, planes de pago, perfiles o autenticación que no se solicitaron.

La composición preferida reserva aproximadamente una sexta parte del ancho a los filtros, algo más de la mitad al globo y cerca de un cuarto al inspector. Ajustá esas proporciones contra el PNG real en lugar de tomarlas como números inmutables. La cámara y la Tierra pueden invadir visualmente parte del área central, pero no deben tapar los paneles ni los controles.

## Sistema visual implementado en código

Creá tokens para superficies, texto, bordes, acentos, estados, tipografía, tamaños y espaciados. El tema principal es azul noche y grafito, texto claro, acento turquesa y colores de datos sobrios. Utilizá una familia tipográfica adecuada con alternativa local y no dependas de que una fuente externa cargue para que el layout funcione.

Elegí una única familia coherente de iconos. Los símbolos científicos de observación, riesgo, pronóstico y agrupación necesitan una definición distinta de los iconos decorativos. Mantené accesibilidad por forma y texto, además del color. Los anillos, sombras y brillos deben ser discretos y responder al mapa, no convertir la UI en una interfaz de ciencia ficción.

No ocultes atribuciones obligatorias del mapa para copiar un píxel del PNG. Reservá un lugar legible y poco intrusivo para licencias y proveedores reales. Los textos científicos de la imagen deben corregirse si contradicen el catálogo, manteniendo la composición visual.

## Componentes y regiones de la pantalla

Construí una barra superior con la identidad Earth Echo, navegación principal y búsqueda. En esta fase la búsqueda puede tener estados visuales y una interfaz preparada para conectar resultados en la fase 04. No la presentes como operativa si todavía no consulta nada. Evitá navegación que conduzca a pantallas vacías sin explicación.

El panel izquierdo incluye categorías de fenómenos, casillas de activación, contadores, tipos de información, capas ambientales, leyenda del campo seleccionado y opción de agrupar señales. Usá filas compactas alineadas. Los números de ejemplo provienen de fixtures, no de textos arbitrarios repartidos por el código.

El área central contiene el contenedor real del motor, un control de capas activas, una síntesis de señales visibles, leyenda de símbolos y controles de cámara. Conservá el adaptador técnico de la fase 01 si existe. Podés usar un estado provisional explícito para el contenido geográfico mientras se termina en la fase 03; no uses el PNG completo como fondo y controles invisibles superpuestos.

El panel derecho muestra una señal seleccionada, su región, tipo, pestañas Resumen, Datos y Antecedentes, gráfico y metadatos. La composición debe funcionar con un título largo, un proveedor largo, varias fuentes o un campo sin valor. El botón de análisis abre un contenedor preparado o muestra claramente su estado; no debe fingir una operación que todavía no existe.

La franja inferior incluye reproducción, selección de modo y una línea de tiempo con separación clara entre pasado observado y futuro estimado. Reservá espacio para etiquetas y controles sin recurrir a texto ilegible. La futura selección temporal debe tener una representación única en el estado de la app, aunque en esta fase solo se construya la vista.

## Layout y comportamiento de escritorio

Utilizá una estructura de CSS que distribuya el espacio y permita que el mapa ocupe el área restante. Evitá posicionar toda la pantalla con coordenadas absolutas. Los elementos flotantes locales del mapa sí pueden tener anclajes dentro de su contenedor.

Comprobá el tamaño nativo del PNG, 1920 por 1080 y 1366 por 768. No estires toda la imagen con una escala CSS para disimular problemas. Ajustá proporciones, anchos mínimos, texto y zonas desplazables. El documento no debe tener overflow horizontal a estos tamaños. Si el inspector necesita scroll vertical, su cabecera y acciones esenciales deben seguir siendo utilizables; evitá varios scrolls anidados innecesarios.

El objetivo principal es desktop. Incluí una adaptación básica para un ancho reducido que conserve acceso a filtros y detalle, pero no gastes esta fase en una experiencia móvil alternativa que cambie la dirección de escritorio. La app debe sobrevivir al resize sin desmontar el motor por cada píxel.

## Estados de los componentes

Representá carga, vacío, error, seleccionado, deshabilitado y dato no disponible en los componentes que lo necesiten. Las casillas, selectores, pestañas y botones se implementan con controles semánticos. El estado de foco debe ser visible. Ningún estado esencial depende exclusivamente de hover.

Construí un escenario de demostración estable que reproduzca la selección de Amazonía central y el aspecto general del PNG. Indicá DEMO o datos simulados de forma visible. Este escenario es una referencia visual reproducible, separada de la futura pantalla REAL.

## Verificación visual

Iniciá la aplicación y capturá su pantalla, no el archivo de referencia. Compará ambas al mismo ancho y alto. Revisá silueta general, proporción del globo, altura de barra superior e inferior, ancho de paneles, densidad de filas, contraste, tipografía, espaciados y alineación de iconos. Documentá diferencias concretas y corregí las importantes antes de cerrar.

No uses un porcentaje subjetivo de similitud como única evidencia. Si aplicás una comparación automática, controlá tipografía cargada, dispositivo, antialiasing y regiones dinámicas. La comparación de la UI estática es distinta de la futura comparación del planeta en movimiento.

## Criterios de aceptación

- La estructura, estilo y jerarquía recuerdan claramente al PNG original.
- Los componentes están separados por responsabilidad y usan tokens comunes.
- El layout funciona en los tres tamaños de escritorio definidos.
- Los ejemplos están identificados y centralizados.
- Las capturas de la aplicación fueron inspeccionadas y los defectos visuales se corrigieron.
- No existen controles simulados como si fueran operaciones reales ni una pantalla construida como una imagen única.

## Reporte de cierre

Entregá rutas de capturas, tamaños comprobados, diferencias visuales pendientes y componentes preparados para la fase 03. Informá qué interacciones pertenecen todavía a la fase 04. Conservá el estado ejecutable y no conectes proveedores reales como parte de esta tarea.
