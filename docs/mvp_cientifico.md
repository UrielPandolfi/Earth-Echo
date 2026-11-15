# MVP científico demostrable

Prioridad fijada por el usuario15/11/2026: usar las series científicas ya disponibles para anomalías, tendencias y asociaciones, manteniendo diseño y trazabilidad. No requiere Earthdata ni nuevas fuentes. El catálogo completo y sus31fenómenos siguen como alcance mayor; este MVP no equivale a31detectores o predicción mundial.

## Anomalías históricas SST — implementado

`/v1/analyses/d15-anomalies`, producto `d15-sst-seasonal-departures`, sección **Tendencias → Anomalías históricas** en el inspector existente.144meses CoralTemp v3.1,2014–2025,21×21celdas0,05°; soporte real derivado de centros nativos≈16,50–17,55N/67,50–66,45O. ERDDAP elige extremos nearest, por lo que la solicitud nominal1° no es la huella exacta. Se mantienen las441celdas originales y la media ponderada, sin recortar datos para ajustar metadatos.

Referencia fijada2014–2021 por mes calendario, mínimo8años válidos y≥80%días por mes. Para2022–2025: `d=SST−mediana_ref`, `MAD=mediana(|SST_ref−mediana_ref|)`, `M=0,6745*d/MAD`; candidato si`|M|>3,5`. Regla descriptiva de [NIST/Iglewicz–Hoaglin](https://www.itl.nist.gov/div898/handbook/eda/section3/eda35h.htm), fijada antes de contar candidatos. Ocho años no son una normal climática ni permiten interpretar el score como probabilidad. MAD0/referencia insuficiente/ausente dejan score null, sin epsilon o relleno. Los años de referencia no se evalúan como casos nuevos. No se eliminan candidatos del registro.

Resultado real:48meses evaluables,9candidatos cálidos,0fríos,0meses no evaluables. Son resultados históricos de una regla exploratoria, no alarmas actuales, olas de calor marinas de cinco días, blanqueamiento, error de observación confirmado o riesgo probabilístico. Un mes dentro del umbral tampoco acredita ausencia de estrés. HotSpot/DHW y el experimento predictivo SST mantienen sus definiciones/estados propios.

Se cotejaron los144agregados contra todos los NetCDF originales retenidos, con biblioteca distinta del lector clásico inicial: SHA/tamaño, fechas, unidad/rango/máscara, coordenadas, ponderación cos(lat) y mínimo de días. NumPy verifica medianas/MAD/scores. Entrada agregada exacta54.762B, SHA`dba09d3d2a7bb9e4ecaf9b3fc99045b43de4e2867bc153125ac719885b258d60`, incluye144checksums nativos; no nueva descarga. API del producto permite recuperar entrada y parámetros. Tests verifican referencia congelada, huecos/MAD0, corrupción, aritmética, persistencia idempotente, estado no disponible, entrada obsoleta conservada y cambios de dependencia.

Actualización registrada `d15-sst-anomalies`: diaria y al cambiar hash de`data/real/d15/monthly_series.json`, con el scheduler/lock/plazo/retención existentes. Actualizar el análisis no inventa observaciones posteriores a2025; ampliar historia es un trabajo explícito distinto. Ante pérdida/cambio de entrada se conserva el producto anterior y el resumen declara obsolescencia. Los9candidatos se cuentan en ese análisis; no incrementan el contador de eventos calculados como si fueran desastres.

## Anomalía diaria mundial — implementado

Campo`d13-oisst-anomaly-global`, derivado de la variable **anom publicada por NOAA** dentro del mismo NetCDF ya retenido para SST. No nueva fuente, descarga o climatología propia. Permite ver el estado diario disponible además del análisis histórico. La referencia1971–2000 y la condición preliminar están explícitas, separadas de2014–2021. Original nativo0,25°/SST/anom/err/ice compartido, con todas las escalas/máscaras y fecha CF comprobadas por dos lecturas. [Evidencia/fixture](../data/samples/integrations/oisst-anomaly-20261113.md).

Vista de medias1°cos(lat), mínimo8de16celdas válidas por bloque; costa sin soporte queda ausente y se conserva conteo por celda. Máscara primero, escala después: el fill−999 está dentro del valid_range y no se vuelve−9,99°C. Comparación independiente completa de64.800medias. Colores divergentes centrados en cero físico, leyenda simétrica/valores reales, nulos transparentes; ninguna celda se transforma en señal detectada. El inspector conserva unidad/fecha/resolución/QA/original y el resumen histórico ofrece **Ver campo diario en el globo**, selección explícita sin cambiar cámara. Último procesamiento se separa de recuperación del original y de fecha del dato.

Revisión`d13-current-anomaly` diaria y por cambio de`d13-oisst-global`, después de esa entrada, sin HTTP propio. Idempotencia y conservación del válido usan el mismo almacén/lock/retención/presupuesto. Campo de un día no confirma evento MHW de cinco días, umbral percentil90, daño coralino o riesgo de calor del aire. El experimento predictivo sigue experimental.

## Tendencias — implementado y revisado

SST mensual usa `sst-seasonal-fixed-effects-calendar-block-v2`: SST absoluta contra doce interceptos de mes calendario y una pendiente lineal común, estimada por sumas centradas dentro de mes. Mínimo96meses válidos/6años por mes; el gráfico resta media2014–2021 (mínimo8años por mes), pero esa precorrección no interviene en la pendiente. La línea gráfica es la componente lineal común anclada a la media de anomalías. El recorte está al sur de Puerto Rico; se conserva el identificador regional heredado`caribe-occidental`, sin cambiar las coordenadas para hacerlas coincidir con ese nombre.

Resultado2014–2025:144meses, pendiente0,06815495338°C/año. Intervalo condicional95% con12meses:0,02665672194…0,10905991707; sensibilidad24meses:0,02615383366…0,11051116545. Correlación de residuos adyacentes0,84370387165, diagnóstico de dependencia que no se trata como datos independientes. Una serie de12años de este recorte no acredita tendencia secular mundial, causa o capacidad de extrapolación.

Bootstrap de residuos en bloques **calendario completos**,1000réplicas por longitud, semilla20261115+longitud. La máscara se mantiene en sus posiciones originales al reconstruir/ajustar cada réplica: no se eliminan huecos antes de definir bloques o tiempo. Mínimo8inicios de bloque completos; los inicios elegibles pueden solaparse y no se consideran independientes. Si hay meses válidos suficientes pero ningún bloque completo, se publica pendiente con intervalo null. Intervalos aproximados, condicionales a estacionalidad/tendencia ajustadas, sin incertidumbre de instrumentos/climatología/período; suponen residuos aproximadamente estacionarios y dependencia suficientemente corta respecto al bloque. Se muestra sensibilidad, sin escoger la longitud más favorable. No se interpreta excluir cero como atribución causal o validación predictiva.

El verificador compara pendiente contra diseño explícito de12interceptos+tiempo por SVD NumPy; casos conocidos prueban ciclo estacional+pendiente, huecos reales en calendario, dispersión nula, serie corta y ausencia de bloques. CSV mantiene valores/huecos y añade unidad, referencia, versión/método, ejecución y SHA; admite el mismo corte año/mes que JSON. Corte futuro se limita a datos disponibles. Una región no cubierta devuelve todos los valores de tendencia/intervalo nulos, sin reutilizar otra región. Tipos frontend generados desde Pydantic. Anomalías/asociaciones siguen accesibles si falla únicamente la consulta de tendencia.

La ingestión histórica original, método v1 y experimento predictivo SST no se modificaron; siguen reproducibles y el experimento permanece experimental sin evidencia adicional sobre persistencia. RAPID mantiene medias anuales/pendiente descriptiva2005–2023, con sus límites y sin convertirla en pronóstico de colapso.

## Asociaciones históricas — implementado

`/v1/analyses/associations`, **Tendencias → Conexiones exploratorias**. Dos pares explícitos a priori, desfase0 sin buscar el mayor coeficiente: RONI/SST Caribe2014–2025 (48pares) y RAPID-AMOC/SST Caribe2014–2023 (40pares). Ventanas JFM/AMJ/JAS/OND no solapadas. RONI conserva el trimestre publicado ERSSTv6/base1991–2020; no se sustituye por ONI. SST y AMOC usan media con igual peso de tres medias mensuales válidas, sin ponderación diaria ni cierre de huecos. Las unidades °C(RONI), Sv y °C, versiones/ámbitos y límites permanecen distintos.

Se muestran [Pearson](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/correlat.htm) crudo y de residuos. Cada serie se ajusta contra cuatro interceptos de trimestre calendario más pendiente lineal, en el soporte conjunto del período completo. Ajuste principal por sumas centradas dentro de trimestre; comprobación independiente por diseño explícito y SVD NumPy, incluidos todos los residuos. Mínimo32trimestres y6años por trimestre. Sin variación residual o soporte suficiente: null/no evaluable, sin epsilon en el denominador. Eje temporal denso conserva trimestres ausentes.

| Par | r crudo | r ajustado | Intervalo condicional95%, bloque4 | Sensibilidad bloque8 |
| --- | --- | --- | --- | --- |
| RONI–SST |−0,051256 |0,244073 |−0,118742…0,502253 |−0,177589…0,518297 |
| AMOC–SST |0,571922 |0,189734 |−0,176175…0,540197 |−0,215382…0,532163 |

Bootstrap circular de residuos **emparejados**,1000réplicas/semilla20261115+longitud, bloques4y8trimestres: sensibilidad mostrada sin elegir el intervalo favorable. Método basado en [remuestreo de observaciones estacionarias dependientes](https://doi.org/10.1214/aos/1176347265). Intervalos aproximados condicionales a los ajustes, sin incorporar incertidumbre de instrumentos, climatología o tendencias estimadas. Exigen residuos aproximadamente estacionarios/dependencia limitada al bloque;40/48trimestres no garantizan esas hipótesis. Se exigen900réplicas válidas; si no, intervalo null. No p-valor, prueba de significación, corrección por dos pares, habilidad predictiva o conclusión de causalidad. Ambos intervalos incluyen cero; eso tampoco demuestra ausencia de relación física.

RONI resta una media tropical que incluye el Caribe: parte de una asociación puede ser acoplamiento matemático o entradas compartidas. AMOC es transporte integrado de una sección26,5N y contiene procesamiento/reanálisis del proveedor; no medida mundial directa. Factores comunes, dirección y mecanismos causales siguen sin identificar. No se convierte correlación en conexión causal confirmada, probabilidad o futuro.

Las entradas se verifican otra vez contra sus originales retenidos (CPC HTML/ZIP y RAPID NetCDF), además del cotejo144meses CoralTemp. No nueva descarga ni duplicación de activos. Informe tipado versionado en`data/real/analyses/associations`, hasta4revisiones/2MBpor informe, incluido en presupuesto científico512MB junto a productos; los puntos emparejados completos permiten repetir aritmética de cada revisión. CSV conserva ventanas UTC, valores/residuos/unidades y execution_id. Una falla conserva el último informe; API advierte entradas cambiadas/ausentes. Revisión diaria y al cambiar cualquiera de los tres productos de entrada; puesto después de sus dependencias. Capacidades agregan columna Asociación para31fenómenos, parcial sólo F17/F19/F31 en los alcances descritos.

Verificación reproducible con API encendida: `& './services/api/.venv/Scripts/python.exe' -m earth_echo.tools.verify_scientific_mvp --retain`. Recalcula comprobaciones nativas y compara resultados persistidos/API/CSV; escribe`data/operational/mvp_scientific_evidence.json`. No certifica modelos científicos. Capturas nuevas de este incremento permanecen pendientes mientras el controlador del navegador no pueda inicializar sus archivos; no se sustituye por imágenes generadas.

Credenciales Earthdata, más regiones/fuentes, rediseño visual y modelos predictivos nuevos son ampliaciones separadas. SMAP/GLDAS/IMERG reciente permanecen pendientes por decisión del usuario; [configuración](accesos.md).

## Asistente y recorrido demostrable

El asistente consulta los resultados persistidos: anomalías históricas/campo diario, asociaciones exploratorias y pendiente AMOC con unidades de transporte. Son resúmenes de herramientas, sin recalcular ciencia o inventar cifras. Para estos resúmenes y capacidades científicas F17/F19/F31 no se llama al proveedor de texto aunque esté configurado: estado `not_used`, mostrado explícitamente. Los demás recorridos conservan su comportamiento previo. No necesita Qwen/API externa para demostrar el núcleo. Un contexto de replay impide entregar estos análisis completos o llamar a un modelo que pueda revelar información posterior al corte.

El resumen sísmico también toma la consulta definida del dato, sin fijar magnitud≥5cuando el operador configuró otra; fuente ausente no se comunica como cero sismos. El inspector de anomalía diaria comunica una falla de descarga de su fuente aunque el procesamiento local haya sido correcto, conservando las fechas originales y REAL.

Con la API y la web iniciadas ([arranque](../README.md)):

1. Abrir[Earth Echo local](http://127.0.0.1:5173/) y elegir REAL. Mantener vista amplia; no se requieren credenciales para este recorrido.
2. Elegir **Tendencias**. Ver la pendiente SST2014–2025, los intervalos12/24meses y diagnóstico residual. **Ver serie** muestra la anomalía/gráfico y advertencias; **Exportar CSV** incluye versión, referencia y SHA.
3. En **Anomalías históricas**, expandir serie/tabla:9meses candidatos de48evaluados. Revisar referencia corta y región. **Ver campo diario en el globo** selecciona explícitamente OISST; leyenda/fecha/soporte/unidad/original en el inspector. La cámara permanece amplia hasta pedir encuadre.
4. Volver a **Tendencias → Conexiones exploratorias** y expandir ambos pares. Comparar coeficiente crudo/ajustado, dispersión e intervalos/sensibilidad. Exportar los pares CSV con ventanas UTC/unidades/ejecución. No hay afirmación causal o predictiva.
5. En **Asistente**, preguntar «¿Qué anomalías SST hay?», «¿Qué relación hay entre AMOC y SST?» o «¿Cuál es la tendencia de AMOC?». Abrir datos/procedencia desde los enlaces y comparar con el inspector. Un replay activo bloquea los análisis completos; no revela desenlace nuevo.
6. Ejecutar el verificador anterior. Comprueba todos los originales/cálculos/JSON/CSV y estos recorridos del asistente mediante la API local, sin nuevas descargas externas.

Las pruebas automáticas y verificaciones numéricas/API están ejecutadas. La revisión visual nueva y sus capturas siguen pendientes: el controlador de navegador falla antes de inicializar sus archivos (`system cannot find the path specified`). Se conservaron las capturas auténticas anteriores y no se generaron imágenes para aparentar esa aprobación. Este es el bloqueo de cierre visual; las credenciales NASA no bloquean las capacidades centrales descritas.
