# Plan de Earth Echo

Diez fases. El estado real está en `PROGRESS.md`. Los criterios siguientes son los de aceptación de cada prompt, no un cronograma.

| Fase | Resultado | Estado |
| --- | --- | --- |
| 01 | Proyecto ejecutable, arquitectura y contratos | Completada en el alcance de este repositorio |
| 02 | Interfaz de escritorio fiel al PNG | Completada como escenario DEMO |
| 03 | Globo geográfico 3D integrado en esa interfaz | Completada con base GIBS y respaldo local |
| 04 | Exploración completa con datos demo identificados | Completada sobre el escenario con semilla |
| 05 | Primer flujo real, del proveedor al globo | Completada para SST de D15; D01 sigue bloqueado por credencial |
| 06 | Series, tendencias e incertidumbre | Completada para la SST del Caribe occidental |
| 07 | Más capas, capacidades y volumen | Completada con matriz, sismos, Kp y una carga sintética |
| 08 | Pronósticos y prueba histórica reproducible | Completada con Kp importado y un experimento de SST sin habilidad extra |
| 09 | Asistente con herramientas | Completada con herramientas; la inferencia de Qwen queda pendiente |
| 10 | Pruebas, rendimiento, operación y entrega | Cerrada en local, con límites explícitos |

## Criterios por fase

1. **Preparación.** Frontend y API arrancan. El globo se monta y se desmonta sin duplicarse. El catálogo se valida sin alterar las referencias. Los contratos separan observación, señal, pronóstico, demo y no disponible. Quedan tiempos, geometría, unidades, procedencia y accesos faltantes.
2. **Interfaz.** La composición se parece al PNG de 1672×941. Tokens comunes, layout de escritorio, ejemplos centralizados e identificados como demo. Ningún control finge una operación real.
3. **Globo.** Tierra geográfica e interactiva, con proveedor y licencia documentados. Cámara, resize, antimeridiano y ciclo de vida comprobados. La fase 04 recibe una interfaz para agregar y quitar capas.
4. **Exploración demo.** Filtros, mapa, contadores e inspector describen el mismo conjunto. La búsqueda, el tiempo y las unidades funcionan con fixtures visibles como demo.
5. **Flujo real.** Un subconjunto real es trazable de archivo a API y mapa. La ingesta no duplica. Faltante, vencido, credencial ausente y error de proveedor son estados distintos. Los datos persisten al reiniciar.
6. **Tendencias.** Selección geográfica, serie, gráfico y tendencia con una pendiente conocida, huecos y casos no evaluables. Cambio, significancia y predictibilidad quedan separados.
7. **Escala.** Varias fuentes usan el mismo modelo de consulta. Los 31 fenómenos aparecen con su estado real. Hay actualización, errores, retención y una medición contra un presupuesto explícito.
8. **Pronósticos.** Un objetivo versionado, particiones sin información futura y un informe con errores, falsas alarmas y omisiones. Un experimento sin habilidad no se etiqueta como validado.
9. **Asistente.** El mapa sigue funcionando si la IA está apagada. Las herramientas están tipadas y el modelo no decide la predicción ni su éxito. Si falta el runtime, la inferencia queda pendiente.
10. **Entrega.** Arranque reproducible, recorridos demo y real en el alcance realmente conectado, sin secretos y con una matriz de capacidades honesta.

## Dirección que ya quedó fijada

## Integraciones posteriores a fase 10

El pedido actual amplía las integraciones del catálogo completo, por incrementos con datos externos y commits. La matriz ejecutable de trabajo y sus evidencias están en `docs/integraciones.md`; las 48 referencias y 31 fenómenos originales permanecen intactos.

- 11A: CRW mundial, sismos/Kp actualizados y planificador persistente.
- 11B: subconjuntos científicos MODIS y campos públicos IFS +24 h.
- 11C: OISST, inventario volcánico, OAF, CAP, Sentry y ONI histórico.
- 11D: LHASA nativo regional, MHW mensual mundial, DSM GLO-90, rangos reproducibles y actualización al iniciar sesión Windows.
- 11E: trayectorias IBTrACS recientes, con calidad nativa y corte del antimeridiano.
- 11F: polígonos CAP de ciclones GDACS y estado operativo en el inspector.
- 11G: batimetría GEBCO_2026 y TID nativos por celda en un recorte verificable.
- 11H: ASIS numérico nativo de Pampa, con estación/máscara y rechazo de overview discrepante.
- 11I: reportes categóricos RAMSES de langosta del desierto, incluidas ausencias, con consulta y selección completa.
- 11J: rapidez del viento y VPD físicos derivados de IFS, trazables y con dominio explícito.
- 11K: límite total por trabajo de actualización, con aislamiento y continuidad tras vencimiento.
- 11L: BasinATLAS nivel 03 de Sudamérica, miembros ZIP acotados y topología visual declarada.
- 11M: FIRMS NOAA-20 público, máscara sin perder registros, agrupación acotada y contadores por naturaleza.
- 11N: reportes históricos GVP cotejados RSS/CAP, con atraso y zonas de emisión explícitos.
- 11O: atributos y puntos representativos RGI7 públicos, con comprobación glaciar/complejo y sin fingir huellas o capacidad GLOF.
- 11P: RAPID AMOC/calor/agua dulce mensuales por descarga pública oficial, con series regionales y sin pronóstico de colapso.
- 11Q: Sentinel-3A OC4Me L3 público con máscara nativa, atribución Copernicus y color logarítmico, sin fingir integración NASA o toxicidad.
- 11R: medias anuales RAPID y pendiente descriptiva 2005–2023, desde el activo compartido, sin prueba de significación ni extrapolación.
- 11S: humedad relativa del aire a 2 m derivada de T/Td IFS, con dominio líquido, porcentaje y máscara explícitos; reutiliza el original VPD.
- Siguiente: subconjuntos de contexto y accesos científicos numéricos pendientes. Mantener bloqueos por credencial, permiso, volumen o definición científica; un paso no cierra otro producto del mismo proveedor.

React, TypeScript y Vite en `apps/web`. CesiumJS como motor del globo, con Natural Earth II mientras no haya una decisión de imaginería con token. FastAPI en `services/api`. PostgreSQL con PostGIS es la dirección de almacenamiento geográfico para cuando exista una fase de datos persistidos; esta fase no lo exige. Redis y colas quedan fuera hasta que haya un trabajo asíncrono concreto.
