# Fase 05 Primer flujo real desde el proveedor hasta el globo

## Objetivo de esta ejecución

Implementá un recorrido pequeño pero completo con datos ambientales reales. Debe incluir acceso al proveedor, archivo original, decodificación, normalización, almacenamiento, consulta por API y visualización. Conservá el diseño de las fases anteriores y sustituí el proveedor DEMO por el proveedor REAL mediante el contrato existente. El éxito es que cada valor mostrado pueda rastrearse y reproducirse.

## Instrucciones de ejecución que se aplican a esta fase

Actuá como responsable de implementar Earth Echo en el proyecto abierto en Cursor. Ejecutá esta fase y dejá código funcionando. Empezá inspeccionando el estado real del repositorio, sus instrucciones y lo terminado en fases anteriores. Si encontrás trabajo existente correcto, continuá desde ahí. Conservá los cambios del usuario y evitá reescrituras generales que no sean necesarias para este objetivo.

Localizá y leé `Earth_Echo_Especificacion.md`, `Earth_Echo_Catalogo.json` y la imagen de referencia cuyo nombre empieza con `Earth Echo Global Environmental Observatory`. Si sus nombres difieren, resolvelos por los archivos reales del proyecto y registrá las rutas. La captura del explorador de Windows sirve para identificar archivos, pero la referencia visual es el PNG de la aplicación. Consultá también `AGENTS.md`, `PLAN.md`, `PROGRESS.md` y las decisiones técnicas existentes. Estos tres documentos originales son referencias que deben conservarse; agregá esquemas, configuración y notas aparte.

El PNG gobierna el diseño visual. La especificación y el catálogo gobiernan el significado de los datos, sus fuentes y sus limitaciones. Los valores y gráficos de la imagen son ilustrativos y no constituyen un dataset. El catálogo es una especificación de capacidades candidatas, no un archivo de observaciones ni un motor predictivo ya implementado. Una fuente documentada, una fuente conectada y un modelo evaluado son estados distintos.

Trabajá con autonomía en decisiones reversibles. Consultá documentación oficial vigente para APIs y bibliotecas, elegí versiones compatibles y conservá lockfiles. Verificá las funciones que realmente existan en la versión instalada. No reemplaces una dificultad con una dependencia adicional sin justificarla. Pedí información solo cuando falte algo imprescindible, como una credencial o una decisión de costo; mientras tanto avanzá con trabajo independiente y explicá el bloqueo concreto. Nunca solicites secretos por el chat: indicá el nombre de la variable y cómo configurarla localmente.

No adelantes funcionalidades de otra fase como si ya estuvieran terminadas. Implementá únicamente las interfaces mínimas que la fase actual necesite para extenderse después. Evitá clases base, repositorios genéricos y sistemas de plugins sin una segunda implementación real que los justifique. La separación entre UI, globo, datos, conectores y ciencia sí debe mantenerse. La lógica científica no vive dentro de componentes visuales.

Los datos simulados pertenecen a un modo DEMO explícito. La aplicación nunca cambia silenciosamente de REAL a DEMO cuando falla una fuente. Un resultado sin datos suficientes queda no disponible. No inventes probabilidades, confianza, causalidad, fechas de desastres, conexiones científicas ni indicadores de estado saludable. Todo contador debe representar una consulta definida. Conservá origen, unidades, calidad, tiempo y alcance de cada resultado.

Verificá lo que cambies con comprobaciones útiles: tipos y compilación, cálculos e integración cuando correspondan, interacción y captura cuando cambie la UI. No agregues tests que solo reproduzcan literalmente la implementación ni métricas de cobertura como sustituto de comprobar comportamiento. Si no podés ejecutar una herramienta, distinguí la limitación del resultado verificado. Una captura del PNG de referencia no es evidencia de la aplicación construida.

Al terminar, actualizá `PROGRESS.md` con trabajo completo, evidencia, limitaciones y siguiente paso. Registrá decisiones duraderas en el documento correspondiente, sin duplicar todo el historial. Entregá comandos para ejecutar, rutas o URL locales reales y una lista breve de comprobaciones efectivamente ejecutadas. Si Git está disponible y configurado, creá un commit local acotado con los archivos propios de esta fase. No incluyas secretos, archivos gigantes de datos ni cambios ajenos; no publiques ni fuerces pushes. Cerrá esta fase con su reporte y esperá el siguiente prompt.


## Elegir una primera fuente realizable

Revisá la muestra y el acceso comprobados en la fase 01. Como ruta inicial, evaluá un subconjunto pequeño de NASA GPM IMERG D01 para observación de precipitación. Si las credenciales o el formato dificultan completar el recorrido, evaluá NOAA Coral Reef Watch D15 para monitoreo térmico oceánico. La elección debe quedar documentada según acceso real, variable disponible y compatibilidad con el caso de uso, sin afirmar que ambos productos tienen el mismo significado.

Si elegís precipitación, esta fase muestra valores o acumulaciones observadas. No la presentes todavía como predictor de lluvia extrema ni como anomalía sin una referencia histórica. Si elegís Coral Reef Watch, conservá la definición oficial de SST, HotSpot o DHW seleccionada y no la conviertas automáticamente en daño biológico confirmado.

No cambies a otra fuente silenciosamente cuando falte una cuenta. Informá el bloqueo, el nombre de la variable de entorno y el flujo de configuración local. Mientras se obtiene acceso, avanzá con contratos, almacenamiento y una muestra real archivada cuya procedencia esté conservada. Una muestra real archivada puede probar decodificación, pero no completa una integración viva por sí sola.

## Alcance acotado y proveedor comprobado

Usá una región pequeña y un período corto. Para la parte temporal alcanza inicialmente con varias observaciones que permitan probar consulta y selección. No descargues el planeta entero ni años de datos para demostrar que un endpoint responde.

Leé documentación y metadatos de la colección exacta. Registrá identificador de producto, versión, licencia, forma de acceso, resolución, cadencia y demora de publicación. Distinguí disponibilidad nominal de la frecuencia observada en las muestras. Conservá el instante de adquisición o intervalo, emisión cuando exista y disponibilidad conocida.

No inventes URLs de archivos a partir de patrones supuestos si el proveedor tiene un catálogo de descubrimiento. Implementá la ruta más pequeña que permita localizar y obtener la colección elegida, con límites de área, tiempo y volumen. Definí cómo se resuelve una revisión del mismo producto.

## Pipeline de ingestión

Implementá un adaptador con responsabilidades reconocibles: descubrir activos, obtenerlos, verificar formato e integridad, decodificar, aplicar calidad y normalizar. Cada paso debe devolver un resultado que pueda auditarse. No descargues y proceses rásteres pesados durante una petición HTTP del usuario.

Guardá el archivo original de forma inmutable o con versionado identificable, checksum y metadatos. La base conserva el registro del activo y el vínculo con los derivados. Para esta etapa puede usarse almacenamiento local configurado; mantené una interfaz que permita pasarlo a objetos remotos cuando haya una necesidad concreta.

La ingestión debe ser idempotente: ejecutar la misma tarea dos veces no duplica observaciones ni crea señales nuevas por accidente. Elegí una clave estable basada en fuente, colección, versión, adquisición, variable y soporte espacial. Si el proveedor corrige un activo, preservá la versión usada antes y la revisión nueva.

Controlá timeout, tamaño máximo, contenido inesperado y respuestas HTML de autenticación que aparentan un archivo válido. No registres tokens ni URLs firmadas completas en logs. Los reintentos deben ser limitados y adecuados a la política del proveedor. Un error no provoca una descarga mundial de respaldo.

## Normalización científica mínima

Leé unidades, scale factors, offsets, máscara de calidad y valores de relleno. Convertí los valores con una función probada y conservá unidad nativa y unidad canónica. No trates un valor de relleno como una medición extrema.

Para precipitación, distinguí tasa, promedio y acumulado, y considerá la duración exacta del intervalo. Para temperatura, distinguí aire y superficie. Para un índice ya procesado, conservá definición y ventana del producto. Si no podés demostrar una conversión, dejá la variable sin normalizar y explicá el requisito pendiente.

Registrá geometría y soporte espacial. Una celda de una malla no representa una medición puntual con exactitud infinitesimal. Al mostrar un resumen regional, declaralo como agregado y guardá cómo fue calculado. Evitá duplicar celdas de bordes o antimeridiano durante recortes.

## Persistencia y API

Introducí las migraciones y tablas necesarias para fuentes operativas, activos y observaciones. Si se incorpora PostGIS, usá índices y tipos adecuados para las consultas reales; no agregues una tabla por fenómeno si el contrato común los puede representar correctamente. Los archivos ráster grandes permanecen en almacenamiento de activos, no como gigantescos JSON dentro de filas.

Implementá endpoints versionados para estado de fuentes, disponibilidad temporal, consulta espacial y detalle del dato o señal. Aplicá límites a extensión, duración y número de elementos. La UI recibe la cantidad y resolución que puede representar, sin descargar millones de valores en una petición inicial.

Agregá un comando reproducible de ingestión y un mecanismo sencillo de ejecución fuera de la petición web. Un scheduler distribuido todavía no es obligatorio. Concurrencia, cancelación y deduplicación deben quedar claras para poder programar actualización en la fase 07.

## Integración con la pantalla existente

Implementá selección explícita DEMO y REAL. En REAL, actualizá mapa, leyenda, gráfico e inspector desde el backend. Mostrá última observación, última ingestión, cadencia y estado de frescura. Un dato antiguo puede ser válido como archivo histórico; no se etiqueta como una observación actual.

Cuando una región no tiene cobertura, mostrala como tal. Si una consulta no devuelve datos, conservá la cámara y filtros útiles, pero no rellenes el hueco con el escenario DEMO. La aplicación debe poder volver a DEMO mediante una acción explícita del usuario sin contaminar caches o persistencia REAL.

## Criterios de aceptación

- Existe un subconjunto real con fuente, versión, fecha, unidad y calidad trazables.
- El pipeline vuelve a ejecutarse sin duplicar resultados.
- La decodificación y las conversiones se contrastan con una muestra conocida del producto.
- La API permite consultar y recuperar los metadatos del activo original.
- El mismo registro se reconoce en archivo, almacenamiento, API, mapa e inspector.
- Datos ausentes, vencidos, credencial faltante y error de proveedor tienen estados distintos.
- Reiniciar servicios no pierde los datos persistidos.
- Se probó el flujo sin depender exclusivamente de mocks; las pruebas de red quedan separadas de las deterministas.

## Reporte de cierre

Entregá la fuente elegida, región y período probados, comandos de ingestión y consulta, ejemplo de trazabilidad, pruebas ejecutadas y accesos pendientes. Si no se pudo obtener una muestra externa por un bloqueo real, marcá la fase parcialmente bloqueada y separá lo comprobado con archivo archivado de la conexión viva pendiente.
