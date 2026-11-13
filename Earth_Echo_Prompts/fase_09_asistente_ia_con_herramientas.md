# Fase 09 Asistente de IA conectado a datos y herramientas

## Objetivo de esta ejecución

Agregá un asistente conversacional que permita explorar Earth Echo mediante preguntas sobre regiones, variables, tendencias y resultados disponibles. El candidato de partida es un modelo Qwen de pesos abiertos servido localmente o por un endpoint compatible configurado. El asistente debe consultar herramientas del sistema y explicar su evidencia. La aplicación principal debe seguir funcionando cuando el modelo no está disponible.

## Instrucciones de ejecución que se aplican a esta fase

Actuá como responsable de implementar Earth Echo en el proyecto abierto en Cursor. Ejecutá esta fase y dejá código funcionando. Empezá inspeccionando el estado real del repositorio, sus instrucciones y lo terminado en fases anteriores. Si encontrás trabajo existente correcto, continuá desde ahí. Conservá los cambios del usuario y evitá reescrituras generales que no sean necesarias para este objetivo.

Localizá y leé `Earth_Echo_Especificacion.md`, `Earth_Echo_Catalogo.json` y la imagen de referencia cuyo nombre empieza con `Earth Echo Global Environmental Observatory`. Si sus nombres difieren, resolvelos por los archivos reales del proyecto y registrá las rutas. La captura del explorador de Windows sirve para identificar archivos, pero la referencia visual es el PNG de la aplicación. Consultá también `AGENTS.md`, `PLAN.md`, `PROGRESS.md` y las decisiones técnicas existentes. Estos tres documentos originales son referencias que deben conservarse; agregá esquemas, configuración y notas aparte.

El PNG gobierna el diseño visual. La especificación y el catálogo gobiernan el significado de los datos, sus fuentes y sus limitaciones. Los valores y gráficos de la imagen son ilustrativos y no constituyen un dataset. El catálogo es una especificación de capacidades candidatas, no un archivo de observaciones ni un motor predictivo ya implementado. Una fuente documentada, una fuente conectada y un modelo evaluado son estados distintos.

Trabajá con autonomía en decisiones reversibles. Consultá documentación oficial vigente para APIs y bibliotecas, elegí versiones compatibles y conservá lockfiles. Verificá las funciones que realmente existan en la versión instalada. No reemplaces una dificultad con una dependencia adicional sin justificarla. Pedí información solo cuando falte algo imprescindible, como una credencial o una decisión de costo; mientras tanto avanzá con trabajo independiente y explicá el bloqueo concreto. Nunca solicites secretos por el chat: indicá el nombre de la variable y cómo configurarla localmente.

No adelantes funcionalidades de otra fase como si ya estuvieran terminadas. Implementá únicamente las interfaces mínimas que la fase actual necesite para extenderse después. Evitá clases base, repositorios genéricos y sistemas de plugins sin una segunda implementación real que los justifique. La separación entre UI, globo, datos, conectores y ciencia sí debe mantenerse. La lógica científica no vive dentro de componentes visuales.

Los datos simulados pertenecen a un modo DEMO explícito. La aplicación nunca cambia silenciosamente de REAL a DEMO cuando falla una fuente. Un resultado sin datos suficientes queda no disponible. No inventes probabilidades, confianza, causalidad, fechas de desastres, conexiones científicas ni indicadores de estado saludable. Todo contador debe representar una consulta definida. Conservá origen, unidades, calidad, tiempo y alcance de cada resultado.

Verificá lo que cambies con comprobaciones útiles: tipos y compilación, cálculos e integración cuando correspondan, interacción y captura cuando cambie la UI. No agregues tests que solo reproduzcan literalmente la implementación ni métricas de cobertura como sustituto de comprobar comportamiento. Si no podés ejecutar una herramienta, distinguí la limitación del resultado verificado. Una captura del PNG de referencia no es evidencia de la aplicación construida.

Al terminar, actualizá `PROGRESS.md` con trabajo completo, evidencia, limitaciones y siguiente paso. Registrá decisiones duraderas en el documento correspondiente, sin duplicar todo el historial. Entregá comandos para ejecutar, rutas o URL locales reales y una lista breve de comprobaciones efectivamente ejecutadas. Si Git está disponible y configurado, creá un commit local acotado con los archivos propios de esta fase. No incluyas secretos, archivos gigantes de datos ni cambios ajenos; no publiques ni fuerces pushes. Cerrá esta fase con su reporte y esperá el siguiente prompt.


## Revisar capacidades existentes antes de añadir IA

Inventariá las consultas, análisis y pronósticos realmente disponibles después de la fase 08. El asistente solo puede ofrecer acciones respaldadas por esas capacidades. No inventes una función para anticipar cualquier desastre porque el catálogo contiene su nombre.

Prepará una lista de intenciones útiles: resumir señales de una región, explicar una variable, consultar fuentes y fechas, abrir una serie, comparar períodos compatibles, describir una tendencia calculada y explicar el resultado de un experimento. Si una pregunta requiere una fuente no conectada, la respuesta debe reconocerlo y enlazar a su estado de integración.

Separá explicación científica general, consulta de datos y evaluación de un modelo. Una respuesta general sobre qué es una sequía no debe parecer un diagnóstico de una región. Una explicación de antecedentes no debe afirmar causalidad entre coincidencias observadas.

## Proveedor de modelo y recursos

Inspeccioná si existe un runtime local configurado y qué modelos están disponibles. Verificá la documentación oficial y licencia del checkpoint que se elija. Fijá nombre, versión o revisión, configuración y cuantización si corresponde. No asumas que un modelo grande entra en la memoria del equipo.

Evaluá un checkpoint pequeño o cuantizado cuando los recursos sean limitados y medí latencia, memoria, contexto útil y calidad en español con las tareas del producto. La elección debe basarse en ese benchmark, no en el tamaño del nombre. Evitá descargas masivas de pesos sin conocer espacio y presupuesto. Si hace falta que el usuario instale o habilite un runtime, indicá pasos concretos y continuá con la integración independiente del proveedor.

La dirección del modelo y sus credenciales se configuran del lado servidor. No permitas que una petición de usuario indique una URL arbitraria de inferencia o reenvíe tokens. Un servidor desplegado no puede asumir acceso al modelo que corre en la PC del desarrollador: documentá la topología real.

Implementá un proveedor desacoplado con timeout, cancelación, límite de tokens y respuesta de indisponibilidad. El modo sin IA mantiene mapa, filtros, datos, tendencias y pronósticos. Un mock del modelo sirve para tests y debe estar identificado; no se muestra como una respuesta de Qwen realmente ejecutada.

## Herramientas estructuradas

Definí herramientas pequeñas con esquemas tipados, permisos y límites. Como orientación, el asistente puede consultar capacidades de un fenómeno, señales por región y fecha, detalle de una señal, serie de una variable, resultado de tendencia y reporte de un experimento. Ajustá nombres a la API existente y evitá duplicar los servicios científicos dentro del módulo de chat.

El servidor valida todos los argumentos: IDs existentes, intervalo temporal, área, unidad solicitada y límites de volumen. El modelo no ejecuta SQL libre, comandos del sistema, código arbitrario ni descargas desde URLs propuestas en el texto. Las operaciones de ingestión, borrado y entrenamiento no se habilitan como herramientas de conversación por defecto.

Las herramientas devuelven datos compactos con identificadores, tiempos, unidades, cobertura, método, incertidumbre y procedencia. No envíes todo el globo ni archivos científicos completos al contexto. Si hace falta una agregación, calculala en un servicio y devolvé el resultado junto a su definición.

Definí un presupuesto de llamadas por pregunta y una política de interrupción. Cuando un trabajo científico tarda, el asistente debe informar su estado real. No responderá que calculó un análisis si solo puso una tarea en una cola.

## Contexto documental y evidencia

Construí recuperación sobre la especificación, el catálogo y la documentación interna aprobada. Conservá IDs de fuentes, fenómenos y versiones. El contenido recuperado es evidencia documental, no una instrucción que pueda modificar permisos o ignorar las reglas del sistema.

Separá documentos estáticos de resultados recientes de herramientas. Para una afirmación sobre estado actual, el modelo necesita una consulta actual con fecha. Que el catálogo describa SMAP no significa que haya una observación SMAP cargada para esa región.

Las respuestas deben vincularse a entradas concretas que el usuario pueda abrir: fuente, activo, serie, análisis o experimento. El texto debe indicar cobertura y limitaciones cuando cambien la interpretación. Si no hay evidencia, debe responder que falta el dato o que la capacidad no está implementada, sin rellenar con conocimiento general presentado como medición.

No generes probabilidades numéricas en lenguaje libre. Si un porcentaje existe, viene de una herramienta con definición. No fabriques citas, nombres de artículos ni archivos. Las conexiones entre señales se describen como asociación o hipótesis salvo que el módulo y la evidencia permitan una interpretación causal específica.

## Restricción temporal en replay

Cuando el usuario esté en una simulación histórica, el contexto del asistente incluye la fecha de corte y el modo. Las herramientas aplican esa restricción en el backend. Los resultados posteriores o métricas del desenlace no se entregan antes de revelarlos.

Un LLM puede conocer un evento histórico por entrenamiento. Por eso no se utiliza como predictor numérico, clasificador del desenlace ni evaluador del experimento. Si se permite una explicación antes de revelar el futuro, debe limitarse a los datos de herramientas y no alterar la predicción almacenada por el módulo científico.

No uses el nombre de una catástrofe futura como feature de una consulta del replay. Si el usuario pide directamente el desenlace antes de revelarlo, explicá la restricción de esa experiencia o permití salir explícitamente del replay; no mezcles los contextos silenciosamente.

## Integración con el diseño de escritorio

Agregá acceso al asistente mediante un panel o cajón que respete el espacio del mapa y del inspector. Conservá el diseño aprobado y evitá reducir el globo a una miniatura permanente. La conversación puede usar la región y señal seleccionadas mediante una indicación visible del contexto compartido.

Implementá estados de envío, recepción, cancelación, error y modelo no disponible. Si hay streaming, el estado y la conclusión deben distinguirse. Una conexión interrumpida no deja una respuesta parcial con apariencia de resultado completo. Los enlaces a evidencia deben seguir funcionando al cambiar de señal.

El asistente puede proponer acciones locales de exploración, como abrir una serie o centrar la cámara, mediante un esquema validado. No dejes que texto sin estructurar controle el estado de la aplicación. El usuario debe conservar control de la selección y poder cerrar el panel.

## Evaluación con preguntas representativas

Creá un pequeño conjunto de pruebas que incluya una pregunta respondible con dato real, una con cobertura parcial, una sobre una fuente ausente, una con fecha pasada, una comparación de unidades incompatibles y una solicitud imposible como fecha exacta de terremoto. Agregá una entrada documental que intente dar instrucciones para comprobar que no modifica permisos.

Comprobá trazabilidad de cada afirmación, fidelidad a números y unidades, reconocimiento de ausencia de evidencia y comportamiento con modelo desconectado. Separá tests deterministas con proveedor simulado de una evaluación real del modelo elegido. Registrá que una ejecución favorable aislada no garantiza todas las respuestas futuras.

## Criterios de aceptación

- Hay un proveedor configurable y una prueba real del modelo si el runtime está disponible.
- El mapa y los análisis siguen funcionando con IA deshabilitada.
- Las herramientas están tipadas, limitadas y validadas por el servidor.
- Las respuestas referencian resultados reales o reconocen la falta de información.
- El replay conserva su restricción temporal y el LLM no decide la predicción ni su éxito.
- Se midieron recursos y se ejecutaron pruebas de preguntas y fallas relevantes.
- La integración visual conserva la composición del producto.

## Reporte de cierre

Informá modelo y configuración, topología, recursos medidos, herramientas habilitadas, pruebas reales y simuladas, preguntas que todavía no se pueden responder y límites conocidos. Si falta el runtime, dejá el adaptador y la UI comprobados, pero marcá la inferencia real pendiente en lugar de declararla ejecutada.
