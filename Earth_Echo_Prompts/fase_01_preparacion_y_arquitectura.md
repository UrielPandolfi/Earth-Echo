# Fase 01 Preparación del proyecto y arquitectura ejecutable

## Objetivo de esta ejecución

Construí la base profesional de Earth Echo a partir de los archivos que ya están en este workspace. Earth Echo será un observatorio ambiental mundial con globo 3D, capas, señales, tendencias, pronósticos y exploración histórica. El objetivo inmediato es que el proyecto arranque y tenga contratos claros para las fases siguientes. Necesito implementación y verificaciones, además de las decisiones de diseño.

## Instrucciones de ejecución que se aplican a esta fase

Actuá como responsable de implementar Earth Echo en el proyecto abierto en Cursor. Ejecutá esta fase y dejá código funcionando. Empezá inspeccionando el estado real del repositorio, sus instrucciones y lo terminado en fases anteriores. Si encontrás trabajo existente correcto, continuá desde ahí. Conservá los cambios del usuario y evitá reescrituras generales que no sean necesarias para este objetivo.

Localizá y leé `Earth_Echo_Especificacion.md`, `Earth_Echo_Catalogo.json` y la imagen de referencia cuyo nombre empieza con `Earth Echo Global Environmental Observatory`. Si sus nombres difieren, resolvelos por los archivos reales del proyecto y registrá las rutas. La captura del explorador de Windows sirve para identificar archivos, pero la referencia visual es el PNG de la aplicación. Consultá también `AGENTS.md`, `PLAN.md`, `PROGRESS.md` y las decisiones técnicas existentes. Estos tres documentos originales son referencias que deben conservarse; agregá esquemas, configuración y notas aparte.

El PNG gobierna el diseño visual. La especificación y el catálogo gobiernan el significado de los datos, sus fuentes y sus limitaciones. Los valores y gráficos de la imagen son ilustrativos y no constituyen un dataset. El catálogo es una especificación de capacidades candidatas, no un archivo de observaciones ni un motor predictivo ya implementado. Una fuente documentada, una fuente conectada y un modelo evaluado son estados distintos.

Trabajá con autonomía en decisiones reversibles. Consultá documentación oficial vigente para APIs y bibliotecas, elegí versiones compatibles y conservá lockfiles. Verificá las funciones que realmente existan en la versión instalada. No reemplaces una dificultad con una dependencia adicional sin justificarla. Pedí información solo cuando falte algo imprescindible, como una credencial o una decisión de costo; mientras tanto avanzá con trabajo independiente y explicá el bloqueo concreto. Nunca solicites secretos por el chat: indicá el nombre de la variable y cómo configurarla localmente.

No adelantes funcionalidades de otra fase como si ya estuvieran terminadas. Implementá únicamente las interfaces mínimas que la fase actual necesite para extenderse después. Evitá clases base, repositorios genéricos y sistemas de plugins sin una segunda implementación real que los justifique. La separación entre UI, globo, datos, conectores y ciencia sí debe mantenerse. La lógica científica no vive dentro de componentes visuales.

Los datos simulados pertenecen a un modo DEMO explícito. La aplicación nunca cambia silenciosamente de REAL a DEMO cuando falla una fuente. Un resultado sin datos suficientes queda no disponible. No inventes probabilidades, confianza, causalidad, fechas de desastres, conexiones científicas ni indicadores de estado saludable. Todo contador debe representar una consulta definida. Conservá origen, unidades, calidad, tiempo y alcance de cada resultado.

Verificá lo que cambies con comprobaciones útiles: tipos y compilación, cálculos e integración cuando correspondan, interacción y captura cuando cambie la UI. No agregues tests que solo reproduzcan literalmente la implementación ni métricas de cobertura como sustituto de comprobar comportamiento. Si no podés ejecutar una herramienta, distinguí la limitación del resultado verificado. Una captura del PNG de referencia no es evidencia de la aplicación construida.

Al terminar, actualizá `PROGRESS.md` con trabajo completo, evidencia, limitaciones y siguiente paso. Registrá decisiones duraderas en el documento correspondiente, sin duplicar todo el historial. Entregá comandos para ejecutar, rutas o URL locales reales y una lista breve de comprobaciones efectivamente ejecutadas. Si Git está disponible y configurado, creá un commit local acotado con los archivos propios de esta fase. No incluyas secretos, archivos gigantes de datos ni cambios ajenos; no publiques ni fuerces pushes. Cerrá esta fase con su reporte y esperá el siguiente prompt.


## Inspección antes de modificar

1. Enumerá la estructura relevante del proyecto, sin recorrer dependencias, cachés o archivos binarios innecesarios. Identificá si hay una aplicación existente, su gestor de paquetes, servicios, versión de lenguaje, pruebas y cambios pendientes de Git.
2. Abrí el PNG de la aplicación y reconocé su composición. Si disponés de inspección de imágenes, usala. Si no, dejá documentada esa limitación y conservá el archivo como referencia para la fase visual. No confundas la captura del explorador de archivos con la captura del producto.
3. Parseá el JSON completo y extraé sus IDs reales de fuentes y fenómenos, campos, estados y referencias cruzadas. Validá IDs duplicados y referencias inexistentes. No transformes silenciosamente los textos descriptivos en instrucciones ejecutables.
4. Leé la especificación, especialmente arquitectura, tiempos, unidades, validación histórica y secuencia propuesta. Construí una lista breve de capacidades confirmadas, propuestas y dependientes de accesos externos.

## Decisión de stack y prueba técnica mínima

Si estamos comenzando desde cero, tomá como hipótesis frontend React con TypeScript y Vite, un motor geoespacial especializado para el globo, y backend Python con FastAPI. CesiumJS es el candidato inicial del globo. Antes de fijarlo, comprobá que funciona en el entorno local, cómo integrar sus assets, estilos y workers, qué imágenes puede mostrar y qué servicios exigen cuenta, token o atribución. No confundas la biblioteca con los servicios externos de contenido.

Realizá una prueba mínima que monte y desmonte un globo o vista técnica en el frontend. La apariencia de esta prueba puede ser básica; el diseño final llega en las fases 02 y 03. Verificá que el motor no genere instancias duplicadas al remontar el componente y que no haya un error de importación o de assets. Si ya existe otro motor adecuado, evaluá conservarlo en vez de migrar por preferencia.

Fijá versiones compatibles con lockfile. Elegí un único gestor de paquetes para el frontend y un mecanismo reproducible para Python. Comprobá comandos en Windows y documentá la alternativa con Docker o WSL cuando corresponda. Las rutas del proyecto pueden contener espacios, como `E:\Earth Echo`; los comandos y scripts deben manejarlos correctamente. No dependas de una ruta absoluta de tu entorno.

No instales simultáneamente varias bibliotecas de mapas, varios sistemas de estado o varios servidores. PostgreSQL con PostGIS es la dirección propuesta para almacenamiento geográfico cuando la fase de datos lo requiera. Redis, colas distribuidas y almacenamiento remoto se incorporarán cuando haya una necesidad operativa concreta; esta fase no debe exigir una infraestructura extensa para mostrar una pantalla local.

## Estructura mínima mantenible

Definí una organización equivalente a estas responsabilidades, adaptando nombres al repositorio real:

- Aplicación web y composición de pantalla.
- Componentes visuales y tokens de diseño.
- Adaptador del motor del globo.
- Dominio ambiental y contratos compartidos.
- Repositorio de datos de demostración.
- API y servicios de consulta.
- Conectores externos y procesamiento científico.
- Documentación, muestras pequeñas y pruebas relevantes.

No crees implementaciones vacías de 31 detectores para aparentar avance. El catálogo puede describirlos y la aplicación puede conocer sus estados, pero cada capacidad debe indicar si está especificada, conectada, experimental o validada para un alcance. Tampoco construyas un sistema de plugins complejo antes de necesitarlo.

## Contratos de datos que deben quedar definidos

Definí esquemas con validación en los límites de entrada. Elegí una fuente de verdad para los contratos de API y un mecanismo que detecte divergencia entre Python y TypeScript. No mantengas dos modelos enormes escritos a mano sin una prueba de compatibilidad.

El catálogo de fuentes debe conservar identificador, nombre, documentación, cobertura, acceso y estado de integración. El catálogo de fenómenos debe conservar IDs y referencias a fuentes. Los registros operativos se guardan separados del catálogo original.

Diseñá registros de activo, observación, señal y pronóstico. Incluí geometría o soporte espacial, variable, unidad, intervalo observado, fecha de emisión cuando exista, instante de disponibilidad, instante de ingestión, calidad, versión de producto, origen y modo de datos. Un pronóstico requiere fecha de inicialización, plazo y validez. La probabilidad debe admitir `null` y tener definición cuando exista. Un dato faltante no se convierte en cero.

Usá UTC en almacenamiento y transporte, con fechas ISO 8601 con zona. La UI podrá presentar una zona horaria explícita. Guardá intervalos para productos compuestos, no una hora inventada. Si la disponibilidad histórica se desconoce, representala como desconocida: no asumas que coincidió con la observación.

Definí convención de coordenadas GeoJSON longitud y latitud, tratamiento de geometrías y antimeridiano y significado de extensión geográfica. Un punto de síntesis regional debe identificar la región que representa. No conviertas todas las variables científicas en pines puntuales por conveniencia.

## Configuración y muestra de acceso

Prepará configuración por entorno, `.env.example` sin secretos, exclusiones de Git y comandos para iniciar frontend y una API mínima de salud. El servidor debe tener límites de entrada y orígenes de desarrollo explícitos. Diferenciá salud del proceso y disponibilidad de proveedores.

Elegí una fuente candidata del catálogo para el primer flujo real. Obtené una muestra pequeña, pública o con una credencial ya configurada, y comprobá formato y metadatos. Si requiere una cuenta ausente, documentá el requisito y probá una muestra pública compatible de otra fuente, identificando el cambio. No descargues archivos mundiales completos. La muestra se usa para resolver viabilidad, no para afirmar una predicción.

## Documentación que debe quedar creada

Creá o actualizá un `AGENTS.md` conciso con las reglas duraderas del proyecto, un `PLAN.md` con las diez fases y criterios de aceptación, un `PROGRESS.md` con el estado real y un README con requisitos y comandos. Registrá la decisión de stack y las responsabilidades en una nota de arquitectura. Separá pendientes científicos de problemas de instalación.

## Criterios de aceptación

- Frontend y API mínima arrancan siguiendo el README.
- La prueba del motor se ejecuta, y su ciclo de vida queda comprobado.
- El catálogo se valida sin alterar los archivos de referencia.
- Los contratos distinguen observación, señal, pronóstico, datos simulados y estados no disponibles.
- Existe una estrategia explícita de tiempos, geometrías, unidades y procedencia.
- Se ejecutaron las comprobaciones de compilación, contratos y salud pertinentes.
- Quedan identificados accesos faltantes, sin prometer conexiones que no se probaron.

## Reporte de cierre

Informá estructura creada, stack elegido y razones concretas, comandos verificados, resultado de la prueba del motor, resultado de la muestra de datos y bloqueos. Señalá qué debe usar la fase 02 y cuáles son las decisiones que ya quedaron fijadas. No empieces a construir el diseño completo ni modelos predictivos en esta fase.
