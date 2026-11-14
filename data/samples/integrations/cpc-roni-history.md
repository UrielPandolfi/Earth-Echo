# Historia RONI ERSSTv6

Se reutiliza `definition.html` del ZIP auténtico [CPC ENSO](cpc-roni-outlook-202611.md), sin otra descarga de la misma página. [Fuente oficial](https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/), índice RONI ERSSTv6/base 1991–2020. El ID HTML heredado `roni-v5-table2` no es la versión científica: el encabezado/definición publicados dicen v6. La otra tabla, oculta y vacía, no se lee.

77 años centrales, 1950–2026, 924 posiciones estacionales: **921 números publicados y tres temporadas no publicadas**, SON/OND/NDJ 2026, con value=null. No se sustituyen por cero; MAM 2026 sí publica 0,0 y se conserva. Primer DJF 1950=−1,2°C, intervalo civil [01/12/1949,01/03/1950). Último ASO 2026=2,0°C, [01/08/2026,01/11/2026). El año de la tabla corresponde al mes central; no se inventa fecha de pasada ni emisión UTC.

RONI resta media tropical y ajusta varianza: no es ONI. Serie separada y sin clasificación automática de fase/episodio, regresión, probabilidad o impacto local. Medias de tres meses que se solapan; las fechas no representan observaciones mensuales independientes. CPC advierte que los valores más recientes son estimaciones y pueden revisarse durante dos meses por el filtro de ERSSTv6.

Cada año, cabecera, número y ausencia se coteja entre HTMLParser y extracción independiente directa de las celdas originales. El HTML omite legalmente el cierre del último `tr` antes de `tbody`: el parser maneja ese cierre implícito y conserva 2026 completo, sin perderlo por depender de una etiqueta opcional. Rechaza años duplicados/ausentes, cambio de versión/definición, celdas inválidas o un valor histórico en un trimestre no finalizado.

Activo compartido de 31.348 B, SHA `76ea6e80915a863bd3a3994fc7f25b58c696ce314c2cf98c0491948777124ff8`, el mismo de los tres pronósticos. Checksum científico propio sólo para la historia/definición/método: una revisión del índice no se confunde con una nueva perspectiva. Procesamiento inicial local de los bytes retenidos; recuperación original 16:27:01 UTC, ingestión 16:45:49. Actualización conjunta real 16:47:55 unchanged; cuatro productos comparten una única lectura de las cuatro páginas.

Tres pruebas auténticas cubren último año/cierre implícito, nulos/cero y calendario DJF, rechazo de versiones/años/valores futuros y persistencia/idempotencia con el mismo activo. Prueba de interfaz evita presentar esta historia como tabla de pronóstico; gráfico conserva huecos y definición. Captura REAL `real-roni-history.jpg`.
