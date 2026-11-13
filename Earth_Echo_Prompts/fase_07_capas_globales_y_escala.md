# Fase 07 Ampliación de fuentes capas globales y volumen

## Objetivo de esta ejecución

Ampliá Earth Echo hasta convertirlo en un observatorio con varias fuentes y capas ambientales simultáneas, conservando trazabilidad, claridad y rendimiento. La interfaz debe transmitir la riqueza de la captura cuando existen muchos datos, pero cada marca REAL tiene que responder a un registro o agregado válido. El catálogo completo debe quedar representado mediante capacidades y estados, sin simular que los 31 fenómenos tienen predictores operativos.

## Instrucciones de ejecución que se aplican a esta fase

Actuá como responsable de implementar Earth Echo en el proyecto abierto en Cursor. Ejecutá esta fase y dejá código funcionando. Empezá inspeccionando el estado real del repositorio, sus instrucciones y lo terminado en fases anteriores. Si encontrás trabajo existente correcto, continuá desde ahí. Conservá los cambios del usuario y evitá reescrituras generales que no sean necesarias para este objetivo.

Localizá y leé `Earth_Echo_Especificacion.md`, `Earth_Echo_Catalogo.json` y la imagen de referencia cuyo nombre empieza con `Earth Echo Global Environmental Observatory`. Si sus nombres difieren, resolvelos por los archivos reales del proyecto y registrá las rutas. La captura del explorador de Windows sirve para identificar archivos, pero la referencia visual es el PNG de la aplicación. Consultá también `AGENTS.md`, `PLAN.md`, `PROGRESS.md` y las decisiones técnicas existentes. Estos tres documentos originales son referencias que deben conservarse; agregá esquemas, configuración y notas aparte.

El PNG gobierna el diseño visual. La especificación y el catálogo gobiernan el significado de los datos, sus fuentes y sus limitaciones. Los valores y gráficos de la imagen son ilustrativos y no constituyen un dataset. El catálogo es una especificación de capacidades candidatas, no un archivo de observaciones ni un motor predictivo ya implementado. Una fuente documentada, una fuente conectada y un modelo evaluado son estados distintos.

Trabajá con autonomía en decisiones reversibles. Consultá documentación oficial vigente para APIs y bibliotecas, elegí versiones compatibles y conservá lockfiles. Verificá las funciones que realmente existan en la versión instalada. No reemplaces una dificultad con una dependencia adicional sin justificarla. Pedí información solo cuando falte algo imprescindible, como una credencial o una decisión de costo; mientras tanto avanzá con trabajo independiente y explicá el bloqueo concreto. Nunca solicites secretos por el chat: indicá el nombre de la variable y cómo configurarla localmente.

No adelantes funcionalidades de otra fase como si ya estuvieran terminadas. Implementá únicamente las interfaces mínimas que la fase actual necesite para extenderse después. Evitá clases base, repositorios genéricos y sistemas de plugins sin una segunda implementación real que los justifique. La separación entre UI, globo, datos, conectores y ciencia sí debe mantenerse. La lógica científica no vive dentro de componentes visuales.

Los datos simulados pertenecen a un modo DEMO explícito. La aplicación nunca cambia silenciosamente de REAL a DEMO cuando falla una fuente. Un resultado sin datos suficientes queda no disponible. No inventes probabilidades, confianza, causalidad, fechas de desastres, conexiones científicas ni indicadores de estado saludable. Todo contador debe representar una consulta definida. Conservá origen, unidades, calidad, tiempo y alcance de cada resultado.

Verificá lo que cambies con comprobaciones útiles: tipos y compilación, cálculos e integración cuando correspondan, interacción y captura cuando cambie la UI. No agregues tests que solo reproduzcan literalmente la implementación ni métricas de cobertura como sustituto de comprobar comportamiento. Si no podés ejecutar una herramienta, distinguí la limitación del resultado verificado. Una captura del PNG de referencia no es evidencia de la aplicación construida.

Al terminar, actualizá `PROGRESS.md` con trabajo completo, evidencia, limitaciones y siguiente paso. Registrá decisiones duraderas en el documento correspondiente, sin duplicar todo el historial. Entregá comandos para ejecutar, rutas o URL locales reales y una lista breve de comprobaciones efectivamente ejecutadas. Si Git está disponible y configurado, creá un commit local acotado con los archivos propios de esta fase. No incluyas secretos, archivos gigantes de datos ni cambios ajenos; no publiques ni fuerces pushes. Cerrá esta fase con su reporte y esperá el siguiente prompt.


## Plan por incrementos dentro de esta fase

Antes de implementar, construí una matriz de capacidades con los IDs reales del catálogo. Para cada fenómeno registrá observación, indicador, tendencia y pronóstico por separado, fuente conectada, cobertura, demora, requisitos faltantes y evidencia disponible. Un módulo puede tener monitoreo real y pronóstico pendiente. Evitá un único booleano que lo marque completamente implementado.

Dividí esta fase en incrementos pequeños. Completá y verificá un conector antes de iniciar el siguiente. Reutilizá descargas y transformaciones cuando varios fenómenos usan la misma fuente. No crees múltiples pipelines IMERG independientes para lluvia, agricultura y deslizamientos. Los bloqueos de credenciales se registran y no detienen el desarrollo de conectores independientes.

## Primer grupo de capacidades prioritarias

Extendé los conectores necesarios para las familias iniciales: precipitación F01, temperatura y calor F02, condiciones de sequedad F11, caudales F12, peligro de incendio F15 y estrés térmico de corales F19. Evaluá fuentes D01, D02, D03, D07, D10, D11 y D15 según acceso y formato realmente disponibles.

No confundas sus salidas. Lluvia observada no es lluvia futura. Temperatura alta no es una ola de calor sin duración y umbral. Humedad baja no prueba una sequía de cualquier tipo. Un caudal elevado no da profundidad de inundación urbana. Un índice FWI no es probabilidad de ignición. Estrés térmico de un arrecife no confirma blanqueamiento biológico.

Para estas capacidades, implementá observaciones o indicadores fundamentados y acceso a tendencias cuando haya historia suficiente. Los pronósticos que ya existan pueden prepararse como conectores, pero la validación y presentación temporal final se cierran en la fase 08. Si un producto solo está disponible mediante un portal visual, no declares ingestión numérica hasta resolver un archivo o servicio adecuado.

## Cobertura del resto del catálogo

Recorré las demás familias y registrá la capacidad máxima que los datos disponibles permiten representar:

- Frío y heladas F03, nieve F08, polvo F09 y contaminación F10 pueden compartir insumos atmosféricos, pero requieren variables, niveles y promedios propios.
- Tormentas severas F04 y tornados F05 necesitan distinguir ambientes favorables de eventos locales; no publiques ubicaciones exactas futuras basadas solamente en una malla global.
- Ciclones F06 requieren identificar cuenca, centro emisor, trayectoria y definición de intensidad. El historial best track no es un forecast emitido en esa época.
- Marejadas F07, inundación repentina F13 y abastecimiento de agua F14 tienen dependencias locales que deben quedar visibles.
- Agricultura F16 necesita calendario y cultivo; ENSO F17 y calor marino F18 necesitan índices y referencias coherentes.
- Algas F20, hipoxia F21 y Vibrio F22 permanecen limitados a regiones y métodos con evidencia; una señal de temperatura o clorofila no completa el diagnóstico biológico.
- Langostas F23 usa el ámbito y especies del sistema correspondiente, no un predictor de todas las plagas mundiales.
- Volcanes F24, lagos glaciares F26 y tsunamis F27 requieren observatorios, sensores o centros responsables; un inventario mundial no sustituye esas mediciones.
- Deslizamientos F25 diferencia susceptibilidad, nowcast y pronóstico futuro. Réplicas F28 diferencia probabilidad condicionada a una secuencia de predicción de terremotos individuales.
- Clima espacial F29 y asteroides F30 conservan escala, emisor, solución y fecha. Un acercamiento no es impacto y una señal solar no garantiza intensidad geomagnética.
- AMOC F31 se mantiene como investigación y tendencias, sin una cuenta regresiva de colapso.

El resultado de esta revisión es una matriz honesta y consultable. No hace falta fabricar un detector para cada fila. Sí hace falta mostrar qué existe y qué falta para avanzar. No elimines limitaciones del catálogo para lograr un indicador verde.

## Representación espacial según tipo de dato

Implementá rutas distintas para ráster continuo, puntos observados, regiones agregadas, polígonos de aviso y trayectorias. Un campo global se muestra como campo con nivel de detalle y leyenda, no como un millón de pines. Una alerta regional conserva geometría y emisor. Una trayectoria conserva orden temporal y plazo.

Prepará derivados optimizados para visualización, manteniendo el archivo científico como fuente analítica. Las teselas de imagen sirven para renderizar; sus colores no se leen como si fueran el dato original. Los resúmenes y muestreos tienen método declarado. Aplicá máscaras de cobertura y calidad antes de componer la capa.

Consultá por área visible y nivel de detalle cuando tenga sentido. Manejás antimeridiano y polos. Al alejarse, agregá o reducí detalle sin cambiar el total científico de forma oculta. El número de símbolos visibles puede reducirse por agrupación, pero el número de observaciones representadas debe seguir siendo rastreable.

## Actualización y operación de conectores

Implementá ejecución programada acorde con la cadencia del producto, con tareas idempotentes, límites por proveedor y backoff. Una fuente diaria no se consulta cada segundo. Conservá adquisición, emisión, disponibilidad e ingestión; ninguna de esas fechas reemplaza las otras.

Separá errores de autenticación, cuota, red, formato, ausencia de nuevo dato y cambio de esquema. Conservá el último dato válido con su fecha cuando falle una actualización y marcá su frescura. Una actualización fallida no debe borrar todo el mapa ni cambiar a DEMO.

Aplicá retención, límites de descarga y limpieza de derivados reproducibles. Los archivos usados en evaluaciones o resultados publicados deben permanecer referenciados. No descargues conjuntos globales enormes sin medir almacenamiento, tiempo y costo. Si una región o servicio requiere un acceso diferente, declaralo en configuración.

## Escala y presupuesto de rendimiento

Creá escenarios separados con aproximadamente mil, diez mil y, si el entorno lo admite, más registros sintéticos para medir. La carga de prueba se identifica como tal. Medí carga inicial, respuesta a filtros, selección, giro y zoom, memoria y estabilidad tras alternar capas varias veces. Registrá equipo, navegador, resolución y volumen.

Definí un presupuesto de rendimiento alcanzable y justificá el objetivo. Podés usar como referencia inicial una navegación de al menos 30 FPS con diez mil registros mediante agrupación o reducción de detalle en el equipo de prueba, pero verificá si el objetivo es razonable antes de declararlo requisito cumplido. El benchmark no se resuelve reduciendo silenciosamente el conjunto real a veinte puntos.

Mové transformaciones pesadas fuera del hilo de UI cuando corresponda. Evitá recalcular agrupaciones y series completas por cada evento de movimiento de cámara. Usá cancelación y protección contra respuestas viejas. Cacheá con claves que incluyan fuente, tiempo, filtros, área, resolución y versión.

## Criterios de aceptación

- Varias fuentes alimentan el mismo modelo de consulta sin duplicar pipelines.
- Las capacidades prioritarias tienen estado verificable por salida y región.
- Todos los fenómenos del catálogo aparecen en una matriz de capacidad, incluyendo los limitados y de investigación.
- Cada capa identifica unidad, escala, fecha, cobertura y calidad.
- Existen actualización programada, manejo de errores y política de retención.
- Los escenarios grandes se midieron y los resultados se comparan con un presupuesto explícito.
- La UI conserva densidad y jerarquía similares a la captura sin ocultar huecos de datos.

## Reporte de cierre

Entregá la matriz de capacidades, fuentes realmente conectadas, accesos faltantes, mediciones de rendimiento, volúmenes descargados y capturas del modo REAL y DEMO. Separá lo implementado de lo que queda preparado para la fase 08. Ningún bloqueo científico se resuelve inventando datos o probabilidades.
