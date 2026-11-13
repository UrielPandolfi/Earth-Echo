# Prompts de implementación de Earth Echo

Estos diez prompts están preparados para construir la aplicación por fases en Cursor, usando la especificación, el catálogo y el PNG que ya están en tu proyecto. Son instrucciones de implementación; este paquete no contiene una aplicación construida ni modelos entrenados.

## Cómo usarlos

1. Descomprimí el paquete dentro de la carpeta del proyecto, preferentemente en `prompts/`. Conservá el Markdown de especificación, el JSON y el PNG originales accesibles en el workspace.
2. Abrí el proyecto completo en Cursor. Usá el modo de agente que pueda leer y modificar archivos, ejecutar comandos e inspeccionar la aplicación.
3. Adjuntá o mencioná el archivo de la fase 01 y los tres archivos de referencia. Pedí que ejecute ese prompt completo. No pegues los diez a la vez.
4. Probá el resultado con los criterios de cierre. Si hay fallas, pedí corregir esa misma fase antes de continuar. Si falta un acceso externo, exigí un estado de bloqueo preciso en lugar de datos ficticios.
5. Continuá con la fase siguiente. Podés abrir un chat nuevo cuando convenga: cada prompt repite las reglas necesarias y obliga a leer el progreso real.

El archivo `Earth_Echo_10_Prompts_Cursor.md` reúne exactamente el contenido de los diez prompts en un documento. Los archivos separados del ZIP son más cómodos para trabajar fase por fase. Los encabezados y las listas dentro de cada archivo forman parte del prompt: copiá el documento completo.

## Orden y resultado esperado

| Fase | Resultado |
| --- | --- |
| 01 | Proyecto ejecutable, arquitectura mínima y contratos de datos |
| 02 | Interfaz de escritorio que reproduce la referencia |
| 03 | Globo geográfico 3D real integrado en la interfaz |
| 04 | Exploración completa con datos simulados identificados |
| 05 | Primer flujo con datos reales desde proveedor hasta globo |
| 06 | Investigación de regiones, series y tendencias |
| 07 | Ampliación de capas, capacidades y volumen de datos |
| 08 | Pronósticos y evaluación retrospectiva reproducible |
| 09 | Asistente con Qwen y consultas apoyadas en herramientas |
| 10 | Pruebas completas, rendimiento, operación y entrega |

Al terminar la fase 04, la aplicación debería acercarse visual y funcionalmente a la imagen en modo DEMO. Las fases siguientes incorporan datos y análisis sin desarmar ese diseño. La fase 10 comprueba el alcance realmente conectado y evaluado. El catálogo completo puede incluir funciones regionales, experimentales o de investigación: exhibirlas con su estado correcto forma parte del producto.

## Criterios generales

La imagen es un objetivo visual; no demuestra que existan 1.284 señales reales ni que todos los pronósticos sean posibles. Los contadores, gráficos y capas del modo REAL se calculan a partir de datos disponibles y trazables. La IA conversacional explica resultados y consulta herramientas; el cálculo y la evaluación permanecen en módulos científicos versionados.

El stack propuesto se confirma en la fase 01. Como punto de partida, los prompts sugieren React con TypeScript, un motor geoespacial como CesiumJS y una API Python. Las versiones, servicios de imágenes, cuotas y requisitos de credenciales se verifican al implementar. Si ya existe un stack adecuado, se conserva y se documenta la decisión.

No hay un cronograma garantizado ni una promesa de predictor universal. Cada fase tiene pruebas y criterios de aceptación para medir avances concretos.

## Documentación técnica consultada para orientar los prompts

- CesiumJS Quickstart: https://cesium.com/learn/cesiumjs-learn/cesiumjs-quickstart/
- React StrictMode: https://react.dev/reference/react/StrictMode
- FastAPI Tutorial: https://fastapi.tiangolo.com/tutorial/
- Qwen3 documentación oficial: https://github.com/QwenLM/Qwen3/blob/main/README.md

Consulta realizada el 13 de noviembre de 2026. El agente debe volver a comprobar compatibilidad, servicios y métodos en la implementación real. Las fuentes científicas y las limitaciones están detalladas en los dos documentos originales del proyecto.
