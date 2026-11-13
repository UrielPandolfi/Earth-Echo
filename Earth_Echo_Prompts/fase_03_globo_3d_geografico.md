# Fase 03 Globo 3D geográfico y cámara integrados

## Objetivo de esta ejecución

Transformá el área central en un globo 3D geográfico real, convincente y fluido. Debe acercarse a la Tierra de la imagen: continente americano visible, relieve y textura apropiados, iluminación coherente y una atmósfera sutil. Conservá el diseño construido en la fase 02. Esta fase resuelve el motor del mapa y su ciclo de vida; las señales y filtros completos se conectan en la fase 04.

## Instrucciones de ejecución que se aplican a esta fase

Actuá como responsable de implementar Earth Echo en el proyecto abierto en Cursor. Ejecutá esta fase y dejá código funcionando. Empezá inspeccionando el estado real del repositorio, sus instrucciones y lo terminado en fases anteriores. Si encontrás trabajo existente correcto, continuá desde ahí. Conservá los cambios del usuario y evitá reescrituras generales que no sean necesarias para este objetivo.

Localizá y leé `Earth_Echo_Especificacion.md`, `Earth_Echo_Catalogo.json` y la imagen de referencia cuyo nombre empieza con `Earth Echo Global Environmental Observatory`. Si sus nombres difieren, resolvelos por los archivos reales del proyecto y registrá las rutas. La captura del explorador de Windows sirve para identificar archivos, pero la referencia visual es el PNG de la aplicación. Consultá también `AGENTS.md`, `PLAN.md`, `PROGRESS.md` y las decisiones técnicas existentes. Estos tres documentos originales son referencias que deben conservarse; agregá esquemas, configuración y notas aparte.

El PNG gobierna el diseño visual. La especificación y el catálogo gobiernan el significado de los datos, sus fuentes y sus limitaciones. Los valores y gráficos de la imagen son ilustrativos y no constituyen un dataset. El catálogo es una especificación de capacidades candidatas, no un archivo de observaciones ni un motor predictivo ya implementado. Una fuente documentada, una fuente conectada y un modelo evaluado son estados distintos.

Trabajá con autonomía en decisiones reversibles. Consultá documentación oficial vigente para APIs y bibliotecas, elegí versiones compatibles y conservá lockfiles. Verificá las funciones que realmente existan en la versión instalada. No reemplaces una dificultad con una dependencia adicional sin justificarla. Pedí información solo cuando falte algo imprescindible, como una credencial o una decisión de costo; mientras tanto avanzá con trabajo independiente y explicá el bloqueo concreto. Nunca solicites secretos por el chat: indicá el nombre de la variable y cómo configurarla localmente.

No adelantes funcionalidades de otra fase como si ya estuvieran terminadas. Implementá únicamente las interfaces mínimas que la fase actual necesite para extenderse después. Evitá clases base, repositorios genéricos y sistemas de plugins sin una segunda implementación real que los justifique. La separación entre UI, globo, datos, conectores y ciencia sí debe mantenerse. La lógica científica no vive dentro de componentes visuales.

Los datos simulados pertenecen a un modo DEMO explícito. La aplicación nunca cambia silenciosamente de REAL a DEMO cuando falla una fuente. Un resultado sin datos suficientes queda no disponible. No inventes probabilidades, confianza, causalidad, fechas de desastres, conexiones científicas ni indicadores de estado saludable. Todo contador debe representar una consulta definida. Conservá origen, unidades, calidad, tiempo y alcance de cada resultado.

Verificá lo que cambies con comprobaciones útiles: tipos y compilación, cálculos e integración cuando correspondan, interacción y captura cuando cambie la UI. No agregues tests que solo reproduzcan literalmente la implementación ni métricas de cobertura como sustituto de comprobar comportamiento. Si no podés ejecutar una herramienta, distinguí la limitación del resultado verificado. Una captura del PNG de referencia no es evidencia de la aplicación construida.

Al terminar, actualizá `PROGRESS.md` con trabajo completo, evidencia, limitaciones y siguiente paso. Registrá decisiones duraderas en el documento correspondiente, sin duplicar todo el historial. Entregá comandos para ejecutar, rutas o URL locales reales y una lista breve de comprobaciones efectivamente ejecutadas. Si Git está disponible y configurado, creá un commit local acotado con los archivos propios de esta fase. No incluyas secretos, archivos gigantes de datos ni cambios ajenos; no publiques ni fuerces pushes. Cerrá esta fase con su reporte y esperá el siguiente prompt.


## Continuidad técnica

Revisá la decisión del motor de la fase 01 y su prueba. Usá esa integración salvo que exista un impedimento comprobable. Si proponés cambiarla, explicá el problema específico y verificá una alternativa mínima antes de migrar. No montes simultáneamente dos motores para solucionar un problema de cámara o textura.

Consultá la documentación de la versión instalada para cámara, globo, imagery, selección y destrucción de recursos. Identificá qué assets, workers y estilos deben servirse durante desarrollo y desde el build final. Comprobá URLs relativas, base path y carga desde una ruta que no sea la raíz del dominio.

No asumas que las imágenes de satélite, terreno o edificios vienen incluidas gratuitamente con la biblioteca. Elegí un proveedor o asset de base con condiciones claras. Si requiere una cuenta, hacelo configurable y declaralo. Debe haber una alternativa visual reproducible para el modo de demostración que no dependa de una credencial secreta embebida en el frontend.

## Representación de la Tierra

Usá coordenadas y geometrías geográficas reales. Para una esfera simplificada o elipsoide, documentá el modelo de referencia. No dibujes continentes a mano ni inventes polígonos para conseguir una silueta parecida. Las texturas deben respetar proyección, orientación, polos y costura longitudinal.

Buscá una textura o capa base que permita reconocer terreno, costas, océanos y regiones. Controlá saturación y contraste para que los futuros datos ambientales se lean encima. Las nubes, si se incluyen, son un recurso visual identificado salvo que provengan de una capa meteorológica real con fecha. No conviertas una textura estática de nubes en evidencia de tormentas actuales.

La atmósfera debe tener intensidad moderada. El brillo del borde no debe ocultar costas ni crear un halo enorme. Si la iluminación real por fecha produce un globo casi oscuro en el encuadre inicial, el modo DEMO puede tener una iluminación de presentación fija, claramente separada del modo astronómico real. Preservá esa decisión en configuración.

El terreno 3D detallado es opcional en esta fase si su costo o acceso dificulta el objetivo. Priorizá el globo global, texturas correctas y estabilidad. Si existe terreno real, no exageres sus alturas sin indicar la escala. Un mapa de riesgo no debe cambiar de interpretación porque el relieve fue deformado por estética.

## Cámara y navegación

Definí un preset inicial que se acerque al encuadre del PNG: América del Sur en el centro de interés, América del Norte arriba y Atlántico hacia un lateral. Ajustá distancia, inclinación y campo visible con capturas de la aplicación. No fijes el encuadre solo para tu monitor.

Implementá giro, acercamiento, alejamiento y volver a vista inicial. Agregá límites para impedir atravesar el planeta, perderlo indefinidamente o generar posiciones no válidas. Conservá una navegación intuitiva con mouse y trackpad. Las acciones de cámara desde la UI no deben iniciar dos animaciones que compitan entre sí.

Ofrecé un método `focusRegion` o equivalente para centrar una región y otro para restaurar el preset. Debe admitir geometría o extensión, no una lista de ciudades codificada. Manejás correctamente extensiones que cruzan el antimeridiano y el caso de una región muy pequeña. Si una vista no puede representarse con sentido, devolvé un estado claro.

No agregues giro automático permanente por defecto. El globo debe permanecer estable mientras se leen señales. Respetá la preferencia de movimiento reducido y permití interrumpir animaciones con interacción del usuario.

## Coordenadas y selección

Implementá una capa adaptadora que traduzca el dominio geográfico al motor. Las entradas de la app usan la convención declarada, y cualquier transformación a coordenadas internas ocurre en un lugar comprobable. Incluí altura y referencia vertical solamente cuando tienen significado.

La selección de un punto o región debe resolver un identificador estable. Distinguí click de drag para evitar abrir un inspector cada vez que se gira la Tierra. Los datos que quedan detrás del planeta no deben verse ni seleccionarse a través de la superficie. Prepará esta capacidad con unas pocas geometrías técnicas identificadas, sin inventar detectores científicos.

Los rótulos y gráficos superpuestos en HTML deben estar anclados a la proyección de pantalla y reaccionar al resize. Si un rótulo no cabe, reubicalo, agrupalo u ocultalo según prioridad. Evitá que una etiqueta siga flotando en una ubicación falsa después de mover la cámara.

## Rendimiento y ciclo de vida

El motor es un recurso persistente del componente del globo. Un cambio de filtro no debe recrear el viewer entero. Guardá referencias de recursos, suscripciones y handlers, y liberá cada uno al desmontar. Verificá el caso de montaje y desmontaje adicional en desarrollo de React; no desactives las comprobaciones de desarrollo para ocultar un bug de limpieza.

Si el motor permite renderizar por demanda, evaluá esa opción para vistas estáticas. Detené trabajo innecesario cuando no hay cambios. Las animaciones y materiales visuales deben tener un costo conocido. No uses una textura de resolución enorme por defecto si una alternativa más pequeña produce la misma calidad visible.

Incluí estado de carga, error de imágenes, WebGL no disponible y pérdida de contexto si el entorno permite detectarlos. La interfaz lateral debe seguir accesible cuando el mapa falla. El fallback informa el problema; no sustituye silenciosamente el globo por una foto que parezca interactiva.

## Criterios de aceptación

- El globo es geográfico e interactivo y reproduce un encuadre cercano a la referencia.
- Texturas y proveedores tienen procedencia y condiciones documentadas.
- Cámara, zoom y restauración funcionan en escritorio y con resize.
- Las coordenadas y extensiones se transforman correctamente, incluyendo un caso de antimeridiano.
- Las geometrías posteriores se ocultan y la selección no atraviesa el planeta.
- Montar y desmontar no duplica recursos ni deja listeners o bucles activos.
- Se midió el comportamiento básico en el navegador objetivo y se guardaron capturas reales.

## Reporte de cierre

Informá proveedor y licencia de la base, configuración de cámara, límites técnicos, comprobaciones de ciclo de vida y capturas comparativas. Dejá documentada la interfaz que la fase 04 usará para agregar, actualizar y quitar capas y señales. No implementes todavía todos los conectores externos.
