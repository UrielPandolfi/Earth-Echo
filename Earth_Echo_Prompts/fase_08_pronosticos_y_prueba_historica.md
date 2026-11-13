# Fase 08 Pronósticos y evaluación histórica reproducible

## Objetivo de esta ejecución

Implementá la parte anticipatoria de Earth Echo con dos caminos explícitos: integrar pronósticos científicos existentes y construir un primer predictor experimental propio. Agregá el modo histórico que oculta información posterior a una fecha, guarda el pronóstico y después revela el desenlace. La interfaz debe distinguir esos experimentos de una predicción ya validada para uso real.

## Instrucciones de ejecución que se aplican a esta fase

Actuá como responsable de implementar Earth Echo en el proyecto abierto en Cursor. Ejecutá esta fase y dejá código funcionando. Empezá inspeccionando el estado real del repositorio, sus instrucciones y lo terminado en fases anteriores. Si encontrás trabajo existente correcto, continuá desde ahí. Conservá los cambios del usuario y evitá reescrituras generales que no sean necesarias para este objetivo.

Localizá y leé `Earth_Echo_Especificacion.md`, `Earth_Echo_Catalogo.json` y la imagen de referencia cuyo nombre empieza con `Earth Echo Global Environmental Observatory`. Si sus nombres difieren, resolvelos por los archivos reales del proyecto y registrá las rutas. La captura del explorador de Windows sirve para identificar archivos, pero la referencia visual es el PNG de la aplicación. Consultá también `AGENTS.md`, `PLAN.md`, `PROGRESS.md` y las decisiones técnicas existentes. Estos tres documentos originales son referencias que deben conservarse; agregá esquemas, configuración y notas aparte.

El PNG gobierna el diseño visual. La especificación y el catálogo gobiernan el significado de los datos, sus fuentes y sus limitaciones. Los valores y gráficos de la imagen son ilustrativos y no constituyen un dataset. El catálogo es una especificación de capacidades candidatas, no un archivo de observaciones ni un motor predictivo ya implementado. Una fuente documentada, una fuente conectada y un modelo evaluado son estados distintos.

Trabajá con autonomía en decisiones reversibles. Consultá documentación oficial vigente para APIs y bibliotecas, elegí versiones compatibles y conservá lockfiles. Verificá las funciones que realmente existan en la versión instalada. No reemplaces una dificultad con una dependencia adicional sin justificarla. Pedí información solo cuando falte algo imprescindible, como una credencial o una decisión de costo; mientras tanto avanzá con trabajo independiente y explicá el bloqueo concreto. Nunca solicites secretos por el chat: indicá el nombre de la variable y cómo configurarla localmente.

No adelantes funcionalidades de otra fase como si ya estuvieran terminadas. Implementá únicamente las interfaces mínimas que la fase actual necesite para extenderse después. Evitá clases base, repositorios genéricos y sistemas de plugins sin una segunda implementación real que los justifique. La separación entre UI, globo, datos, conectores y ciencia sí debe mantenerse. La lógica científica no vive dentro de componentes visuales.

Los datos simulados pertenecen a un modo DEMO explícito. La aplicación nunca cambia silenciosamente de REAL a DEMO cuando falla una fuente. Un resultado sin datos suficientes queda no disponible. No inventes probabilidades, confianza, causalidad, fechas de desastres, conexiones científicas ni indicadores de estado saludable. Todo contador debe representar una consulta definida. Conservá origen, unidades, calidad, tiempo y alcance de cada resultado.

Verificá lo que cambies con comprobaciones útiles: tipos y compilación, cálculos e integración cuando correspondan, interacción y captura cuando cambie la UI. No agregues tests que solo reproduzcan literalmente la implementación ni métricas de cobertura como sustituto de comprobar comportamiento. Si no podés ejecutar una herramienta, distinguí la limitación del resultado verificado. Una captura del PNG de referencia no es evidencia de la aplicación construida.

Al terminar, actualizá `PROGRESS.md` con trabajo completo, evidencia, limitaciones y siguiente paso. Registrá decisiones duraderas en el documento correspondiente, sin duplicar todo el historial. Entregá comandos para ejecutar, rutas o URL locales reales y una lista breve de comprobaciones efectivamente ejecutadas. Si Git está disponible y configurado, creá un commit local acotado con los archivos propios de esta fase. No incluyas secretos, archivos gigantes de datos ni cambios ajenos; no publiques ni fuerces pushes. Cerrá esta fase con su reporte y esperá el siguiente prompt.


## Pronósticos externos primero

Elegí uno o dos productos existentes cuyo acceso ya esté resuelto, por ejemplo un pronóstico meteorológico para temperatura o precipitación, un caudal previsto o un outlook térmico oceánico. Confirmá formato, versión, horizonte, cobertura y metodología en la documentación vigente del proveedor.

Conservá centro emisor, inicialización, emisión, validez, miembro de ensemble cuando exista y variable. El pronóstico de un modelo es una cantidad prevista; una probabilidad de evento derivada requiere definir evento y calibración. No conviertas una salida determinista en un porcentaje porque la UI tiene lugar para una cifra.

Guardá cada corrida que se use para mostrar o evaluar un resultado. El archivo rodante del proveedor puede borrar emisiones viejas. No asumas que el forecast disponible hoy es el mismo que estaba publicado en una fecha pasada. Las revisiones deben identificarse.

## Definición del primer experimento propio

Elegí un objetivo acotado con suficientes datos y una utilidad clara. Candidato: anticipar si la humedad del suelo de una región quedará por debajo de un umbral estacional durante el siguiente período. Definí variable objetivo, unidad espacial, frecuencia, horizonte, umbral y evidencia que determina el desenlace. Registrá todo antes de elegir el modelo.

Empezá por métodos simples y comparables. Incluí climatología y persistencia como referencias. Evaluá una búsqueda de análogos históricos, que es parte de la idea original del producto, y un modelo estadístico sencillo si aporta una comparación útil. No entrenes un modelo grande ni uses un LLM para generar el número por defecto.

En la búsqueda de análogos, definí variables de estado, ventanas antecedentes, normalización, distancia, estación comparable, región y cantidad de vecinos. Todos los parámetros se ajustan sin usar el período de prueba. Un antecedente es elegible solo si su evolución completa hasta el horizonte ya estaba disponible en la fecha de la predicción. Excluí ventanas solapadas que revelen el propio desenlace.

Las transformaciones, imputaciones, climatologías y umbrales deben tener versión y ajustarse dentro de cada partición temporal. No uses estadísticas calculadas con toda la historia para normalizar el entrenamiento y la prueba. Si el objetivo se redefine después de ver resultados, eso constituye un experimento nuevo.

## Validación temporal y espacial

Separá entrenamiento, selección de método y prueba final por tiempo. Definí un gap cuando las ventanas antecedentes o de desenlace se solapan. Mantené juntos registros del mismo evento y evitá que una misma sequía aparezca parcialmente en entrenamiento y prueba como si fueran casos independientes.

Si se afirma transferencia a regiones nuevas, agregá evaluación espacial separada. Un resultado medido en una cuenca no se anuncia para todos los continentes. Informá desempeño por época, región y horizonte, además del promedio global.

Para probabilidades, verificá calibración y utilizá una métrica apropiada como Brier y curvas de calibración cuando haya tamaño suficiente. Informá también falsas alarmas, omisiones y frecuencia base. Para cantidades continuas, usá errores y sesgo con unidades. No elijas una métrica que se vea excelente simplemente porque casi nunca ocurre un evento.

Estimá incertidumbre de evaluación respetando dependencia temporal y cantidad de eventos independientes. Un solo desastre famoso es una demostración de caso, no una validación general. Cuando faltan ejemplos, el informe debe mostrar evidencia insuficiente.

## Disponibilidad de información y prevención de fuga

La simulación histórica debe consultar `available_at` o un registro equivalente de disponibilidad. Una observación ocurrida antes de la fecha de corte puede haberse publicado después y, por tanto, no ser utilizable. Si ese tiempo se desconoce, el registro no se considera automáticamente disponible en una prueba que afirme fidelidad al tiempo real.

IMERG Final, reanálisis revisados, best tracks y archivos reconstruidos pueden ser excelentes para estudiar el pasado, pero no necesariamente eran accesibles entonces. Si se usan, identificá el resultado como experimento retrospectivo con datos reconstruidos y separalo de un replay de corridas realmente archivadas.

El backend aplica el corte temporal; no alcanza con ocultar una línea en el navegador. Los endpoints de features, catálogos usados como entradas, caches y selecciones de casos deben respetar la restricción. La herramienta de evaluación accede al desenlace en una operación separada después de guardar la predicción.

La IA conversacional no genera el resultado numérico ni actúa como juez. Puede conocer el desenlace histórico por entrenamiento. Si se usa para explicar un replay, recibe únicamente información permitida y resultados de herramientas; su texto nunca constituye evidencia de capacidad predictiva.

## Registro de experimentos

Guardá un identificador de experimento y ejecución, definición del objetivo, particiones, datasets, hashes o versiones, código, parámetros, semilla y métricas. La predicción se persiste antes de cargar el desenlace para la evaluación. Guardá estados de error y casos excluidos, además de resultados correctos.

Cada modelo registra su alcance y estado. Un modelo puede estar conectado y producir una salida experimental sin superar a persistencia. En ese caso conservá el resultado y explicá que no se ha demostrado habilidad adicional. No lo promociones a validado modificando el umbral o escondiendo casos difíciles.

No ejecutes búsquedas masivas de hiperparámetros, descargas gigantes o entrenamientos caros sin un presupuesto definido. Esta fase debe conseguir un experimento simple reproducible y una evaluación honesta. El motor debe permitir añadir otro modelo después sin cambiar el contrato de la UI.

## Experiencia de usuario

En el globo y los gráficos, observaciones y pronósticos tienen estilos distintos. La transición temporal muestra la fecha de emisión y horizonte. Una banda de incertidumbre conserva su definición; no se dibuja una banda inventada para que el gráfico parezca científico.

Implementá un replay con región, fecha de corte y horizonte. El flujo es preparar entradas permitidas, calcular y guardar, mostrar la estimación y revelar el desenlace. El usuario puede consultar antecedentes elegidos y métricas de evaluación. No diseñes un espectáculo con un único caso favorable como si fuera prueba general.

Los resultados no disponibles, fuera de cobertura o con evidencia insuficiente se muestran claramente. Una proyección de largo plazo, una alerta de llegada tras un evento iniciado y un pronóstico previo son tipos diferentes. Conservá esa distinción en tarjetas, leyendas y explicaciones.

## Criterios de aceptación

- Al menos un forecast externo se conserva y visualiza con emisión y validez correctas, si su acceso está disponible.
- Hay un objetivo propio formalizado, referencias simples y experimento reproducible.
- Las particiones y transformaciones excluyen información futura y ventanas superpuestas indebidas.
- La predicción queda guardada antes de revelar el desenlace.
- El informe incluye errores, falsas alarmas, omisiones y comparación con referencias.
- La UI diferencia resultado experimental, evaluación retrospectiva y pronóstico importado.
- Si el método no mejora referencias o la evidencia es insuficiente, ese resultado se informa sin maquillarlo.

## Reporte de cierre

Entregá definición del objetivo, método, datos, particiones, métricas, casos de prueba y límites de disponibilidad histórica. Indicá qué capacidades anticipatorias se pueden mostrar y con qué estado. Esta fase puede cerrarse con un experimento técnicamente completo que no demuestre habilidad predictiva; debe quedar identificado como tal y no validado para producción.
