# Fase 10 Integración final operación y entrega del producto

## Objetivo de esta ejecución

Convertí el trabajo acumulado en una versión consistente, instalable y demostrable de Earth Echo. Verificá la fidelidad visual respecto de la captura y el funcionamiento del recorrido completo, desde la fuente hasta la explicación. Esta fase corrige defectos de integración y operación; no agrega funcionalidades grandes que no se hayan planificado ni transforma capacidades experimentales en validadas por cambiar su etiqueta.

## Instrucciones de ejecución que se aplican a esta fase

Actuá como responsable de implementar Earth Echo en el proyecto abierto en Cursor. Ejecutá esta fase y dejá código funcionando. Empezá inspeccionando el estado real del repositorio, sus instrucciones y lo terminado en fases anteriores. Si encontrás trabajo existente correcto, continuá desde ahí. Conservá los cambios del usuario y evitá reescrituras generales que no sean necesarias para este objetivo.

Localizá y leé `Earth_Echo_Especificacion.md`, `Earth_Echo_Catalogo.json` y la imagen de referencia cuyo nombre empieza con `Earth Echo Global Environmental Observatory`. Si sus nombres difieren, resolvelos por los archivos reales del proyecto y registrá las rutas. La captura del explorador de Windows sirve para identificar archivos, pero la referencia visual es el PNG de la aplicación. Consultá también `AGENTS.md`, `PLAN.md`, `PROGRESS.md` y las decisiones técnicas existentes. Estos tres documentos originales son referencias que deben conservarse; agregá esquemas, configuración y notas aparte.

El PNG gobierna el diseño visual. La especificación y el catálogo gobiernan el significado de los datos, sus fuentes y sus limitaciones. Los valores y gráficos de la imagen son ilustrativos y no constituyen un dataset. El catálogo es una especificación de capacidades candidatas, no un archivo de observaciones ni un motor predictivo ya implementado. Una fuente documentada, una fuente conectada y un modelo evaluado son estados distintos.

Trabajá con autonomía en decisiones reversibles. Consultá documentación oficial vigente para APIs y bibliotecas, elegí versiones compatibles y conservá lockfiles. Verificá las funciones que realmente existan en la versión instalada. No reemplaces una dificultad con una dependencia adicional sin justificarla. Pedí información solo cuando falte algo imprescindible, como una credencial o una decisión de costo; mientras tanto avanzá con trabajo independiente y explicá el bloqueo concreto. Nunca solicites secretos por el chat: indicá el nombre de la variable y cómo configurarla localmente.

No adelantes funcionalidades de otra fase como si ya estuvieran terminadas. Implementá únicamente las interfaces mínimas que la fase actual necesite para extenderse después. Evitá clases base, repositorios genéricos y sistemas de plugins sin una segunda implementación real que los justifique. La separación entre UI, globo, datos, conectores y ciencia sí debe mantenerse. La lógica científica no vive dentro de componentes visuales.

Los datos simulados pertenecen a un modo DEMO explícito. La aplicación nunca cambia silenciosamente de REAL a DEMO cuando falla una fuente. Un resultado sin datos suficientes queda no disponible. No inventes probabilidades, confianza, causalidad, fechas de desastres, conexiones científicas ni indicadores de estado saludable. Todo contador debe representar una consulta definida. Conservá origen, unidades, calidad, tiempo y alcance de cada resultado.

Verificá lo que cambies con comprobaciones útiles: tipos y compilación, cálculos e integración cuando correspondan, interacción y captura cuando cambie la UI. No agregues tests que solo reproduzcan literalmente la implementación ni métricas de cobertura como sustituto de comprobar comportamiento. Si no podés ejecutar una herramienta, distinguí la limitación del resultado verificado. Una captura del PNG de referencia no es evidencia de la aplicación construida.

Al terminar, actualizá `PROGRESS.md` con trabajo completo, evidencia, limitaciones y siguiente paso. Registrá decisiones duraderas en el documento correspondiente, sin duplicar todo el historial. Entregá comandos para ejecutar, rutas o URL locales reales y una lista breve de comprobaciones efectivamente ejecutadas. Si Git está disponible y configurado, creá un commit local acotado con los archivos propios de esta fase. No incluyas secretos, archivos gigantes de datos ni cambios ajenos; no publiques ni fuerces pushes. Cerrá esta fase con su reporte y esperá el siguiente prompt.


## Auditoría del estado real

Revisá código, contratos, migraciones, documentación, conectores, pruebas, configuraciones y capturas de las fases anteriores. No asumas que todo está terminado porque un documento diga completo. Contrastá los criterios de aceptación con evidencia ejecutada y registrá discrepancias.

Generá una matriz de entrega para cada capacidad: implementada, disponible en DEMO, disponible con datos reales, limitada regionalmente, experimental, bloqueada o de investigación. Separá estado de implementación, frescura del dato, nivel de peligro y evidencia científica. Una capacidad deshabilitada por falta de credenciales no se anuncia como caída del planeta entero.

Identificá deuda que afecte la entrega: fuentes con URLs supuestas, conversiones no verificadas, datos de ejemplo fuera de DEMO, errores silenciados, promesas de IA no respaldadas y accesos privados que aparecen en el frontend. Corregí defectos dentro del alcance y dejá explícitos los límites científicos que no se resuelven con una corrección de software.

## Recorridos completos de usuario

Verificá un recorrido DEMO reproducible que abra la vista cercana al PNG, gire el globo, active capas, aplique filtros, abra una agrupación, seleccione una señal, cambie pestañas y explore el tiempo. La demostración debe ser estable ante una actualización de datos o una respuesta lenta.

Verificá un recorrido REAL con una fuente conectada: consultar disponibilidad, cargar región, mostrar observación, abrir su serie, ejecutar análisis y consultar procedencia. Si hay un forecast disponible, abrí una corrida y mostrale al usuario emisión, plazo y cobertura.

Verificá el experimento histórico: configurar corte, construir entradas permitidas, guardar estimación, revelar desenlace y abrir métricas. Confirmá en el backend que el resultado quedó persistido antes del acceso al desenlace y que las caches no saltan la restricción temporal.

Si la IA está disponible, comprobá una pregunta respondible, una que deba abstenerse y una con un proveedor fallando. Si está apagada, el observatorio debe mantener el resto de sus funciones. No conviertas la disponibilidad de un modelo local en requisito oculto para abrir el mapa.

## Verificación visual final

Fijá un escenario DEMO, cámara, dimensiones, fuentes tipográficas y datos deterministas. Capturá la aplicación al tamaño nativo del PNG y en 1920 por 1080 y 1366 por 768. Compará proporción de paneles, encuadre y tamaño de la Tierra, densidad de controles, colores, iconos, jerarquía, espaciado y legibilidad.

Corregí diferencias importantes dentro de la app. No edites la captura de salida para que parezca que el software tiene un componente que no existe. No uses una imagen estática para reemplazar el globo real en la evidencia. Una comparación automática puede excluir regiones dinámicas identificadas, pero no ocultar defectos grandes bajo una máscara arbitraria.

Revisá títulos largos, varios proveedores, conteos grandes, ausencia de resultados, errores y gráficos con huecos. Los controles deben seguir utilizables con zoom de navegador y navegación por teclado. Las atribuciones obligatorias conservan legibilidad aunque no existan en la imagen conceptual.

## Pruebas funcionales y científicas relevantes

Ejecutá comprobación de tipos, build y tests pertinentes. Cubrí límites de contratos, unidades, intervalos, máscaras, agregados, antimeridiano, idempotencia y control de fecha histórica. Las pruebas deben comprobar comportamiento y resultados conocidos, no repetir las mismas fórmulas de la implementación como única evidencia.

Probá errores de proveedor, credencial ausente, timeout, archivo inválido, dato vencido, actualización sin nuevos activos y revisión de un producto. El usuario ve un estado específico; el último dato válido conserva su fecha. Una fuente caída no provoca fallback DEMO automático.

Separá pruebas deterministas de acceso externo y de evaluación del modelo de lenguaje. Las pruebas automáticas habituales no deben depender de una descarga mundial o de que un proveedor cambie sus datos durante la ejecución. Conservá una muestra real pequeña con licencia y procedencia cuando corresponda.

Los resultados científicos se contrastan con definiciones y referencias de los métodos. No certifiques un modelo por pasar tests unitarios. El estado validado requiere la evidencia fuera de muestra del alcance declarado; si falta, se conserva experimental o sin evaluar.

## Rendimiento y estabilidad

Repetí los escenarios medidos de la fase 07 en el mismo equipo o declarando las diferencias. Medí carga inicial, red, memoria, giro, filtros, selección y cambios de tiempo. Verificá que abrir y cerrar capas y paneles varias veces no acumule viewers, listeners, tareas o recursos gráficos.

Probá navegación prolongada y solicitudes rápidas con respuestas fuera de orden. El último estado elegido debe prevalecer. Cancelá trabajos innecesarios o dejalos en un estado visible. No resuelvas un problema de rendimiento ocultando datos sin indicar su agregación o resolución.

Dejá un presupuesto documentado con escenario, volumen, resolución y equipo. Un FPS favorable con diez puntos no prueba escalabilidad con miles. Si el objetivo no se cumple, implementá una mejora medida o registrá el límite del release.

## Persistencia y operación

Comprobá arranque desde una instalación limpia, aplicación de migraciones y configuración por entorno. Revisá rutas con espacios en Windows. Los comandos deben declarar puertos, dependencias y ubicación de activos; no depender de servicios que solo estén abiertos en la sesión del desarrollador.

Verificá reinicio de API, frontend, scheduler y base según la topología elegida. Los datos persistidos, ejecuciones y experimentos deben recuperarse. Documentá copia y restauración de metadatos y activos esenciales, y probá una restauración pequeña sin destruir el entorno principal.

Revisá límites de tareas, cuotas, retención y almacenamiento. Las trazas deben permitir identificar una falla por conector y ejecución sin exponer secretos. Diferenciá servicio vivo, listo para consultas y proveedor actualizado. Evitá un único indicador verde que oculte fallas de datos.

## Configuración segura y despliegue

Revisá secretos, tokens de mapas, direcciones de inferencia, permisos de archivos y datos publicados. Los tokens que deban ser públicos por diseño del proveedor se restringen según sus mecanismos; los secretos reales permanecen en servidor. No confundas una variable prefijada para el frontend con un almacenamiento secreto.

Aplicá validación de entradas, consultas acotadas, CORS apropiado y límites de descarga y procesamiento. Las tareas administrativas de ingestión, borrado o entrenamiento no quedan expuestas libremente por comodidad. No agregues cuentas o roles complejos sin necesidad del alcance, pero sí protegé las operaciones que corresponda.

Prepará build, imágenes o instrucciones de despliegue y configuración reproducible para el entorno elegido. Verificá salud, rutas, assets, workers, base path y URLs de backend. El servidor remoto no asume acceso al Qwen que corre en la PC del usuario. Dejá documentada la alternativa sin IA o el servicio accesible autorizado.

No publiques una instancia abierta ni contrates infraestructura de pago como consecuencia implícita de este prompt. Prepará una entrega revisable y usá un destino ya autorizado si existe. Registrá costos conocidos y requisitos pendientes sin inventar una factura futura.

## Documentación y demo final

Actualizá README con instalación, variables, ejecución, ingestión, actualización, pruebas, backup y limitaciones. Incluí fuentes y atribuciones. Prepará un guion corto de demostración que muestre globo, filtros, señal, fuente, tendencia y replay, diferenciando qué pasos usan datos reales y cuáles DEMO.

Actualizá `PLAN.md`, `PROGRESS.md`, matriz de capacidades y decisiones. Si quedan bloqueos externos, el informe final debe nombrarlos y explicar cómo resolverlos. La visión de un observatorio mundial puede estar representada con capacidades limitadas o experimentales sin afirmar que todo es anticipable.

## Criterios de aceptación

- La app arranca desde las instrucciones y mantiene datos después de reiniciar.
- Los recorridos DEMO, REAL, tendencias y replay se probaron en el alcance disponible.
- La IA funciona con evidencia o queda explícitamente deshabilitada sin romper el producto.
- La revisión visual se completó con capturas auténticas y tamaños conocidos.
- Las pruebas y benchmarks se ejecutaron y sus límites están registrados.
- No hay secretos expuestos ni modos de datos mezclados silenciosamente.
- Existe una matriz honesta de capacidades y una entrega reproducible.
- Los accesos o problemas pendientes están diferenciados de las funciones terminadas.

## Reporte de cierre

Entregá instrucciones finales, capturas, comandos comprobados, resultados de pruebas, mediciones, capacidades reales y bloqueos pendientes. Enumerá de forma breve qué reproduce ya la captura y qué parte de la visión científica sigue experimental o limitada. Dejá un commit local limpio y un siguiente backlog priorizado; no declares funcionalidades ausentes como terminadas para cerrar las diez fases.
