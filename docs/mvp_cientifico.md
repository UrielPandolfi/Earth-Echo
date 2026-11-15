# MVP científico demostrable

Prioridad fijada por el usuario15/11/2026: usar las series científicas ya disponibles para anomalías, tendencias y asociaciones, manteniendo diseño y trazabilidad. No requiere Earthdata ni nuevas fuentes. El catálogo completo y sus31fenómenos siguen como alcance mayor; este MVP no equivale a31detectores o predicción mundial.

## Anomalías históricas SST — implementado

`/v1/analyses/d15-anomalies`, producto `d15-sst-seasonal-departures`, sección **Tendencias → Anomalías históricas** en el inspector existente.144meses CoralTemp v3.1,2014–2025,21×21celdas0,05°; soporte real derivado de centros nativos≈16,50–17,55N/67,50–66,45O. ERDDAP elige extremos nearest, por lo que la solicitud nominal1° no es la huella exacta. Se mantienen las441celdas originales y la media ponderada, sin recortar datos para ajustar metadatos.

Referencia fijada2014–2021 por mes calendario, mínimo8años válidos y≥80%días por mes. Para2022–2025: `d=SST−mediana_ref`, `MAD=mediana(|SST_ref−mediana_ref|)`, `M=0,6745*d/MAD`; candidato si`|M|>3,5`. Regla descriptiva de [NIST/Iglewicz–Hoaglin](https://www.itl.nist.gov/div898/handbook/eda/section3/eda35h.htm), fijada antes de contar candidatos. Ocho años no son una normal climática ni permiten interpretar el score como probabilidad. MAD0/referencia insuficiente/ausente dejan score null, sin epsilon o relleno. Los años de referencia no se evalúan como casos nuevos. No se eliminan candidatos del registro.

Resultado real:48meses evaluables,9candidatos cálidos,0fríos,0meses no evaluables. Son resultados históricos de una regla exploratoria, no alarmas actuales, olas de calor marinas de cinco días, blanqueamiento, error de observación confirmado o riesgo probabilístico. Un mes dentro del umbral tampoco acredita ausencia de estrés. HotSpot/DHW y el experimento predictivo SST mantienen sus definiciones/estados propios.

Se cotejaron los144agregados contra todos los NetCDF originales retenidos, con biblioteca distinta del lector clásico inicial: SHA/tamaño, fechas, unidad/rango/máscara, coordenadas, ponderación cos(lat) y mínimo de días. NumPy verifica medianas/MAD/scores. Entrada agregada exacta54.762B, SHA`dba09d3d2a7bb9e4ecaf9b3fc99045b43de4e2867bc153125ac719885b258d60`, incluye144checksums nativos; no nueva descarga. API del producto permite recuperar entrada y parámetros. Tests verifican referencia congelada, huecos/MAD0, corrupción, aritmética, persistencia idempotente, estado no disponible, entrada obsoleta conservada y cambios de dependencia.

Actualización registrada `d15-sst-anomalies`: diaria y al cambiar hash de`data/real/d15/monthly_series.json`, con el scheduler/lock/plazo/retención existentes. Actualizar el análisis no inventa observaciones posteriores a2025; ampliar historia es un trabajo explícito distinto. Ante pérdida/cambio de entrada se conserva el producto anterior y el resumen declara obsolescencia. Los9candidatos se cuentan en ese análisis; no incrementan el contador de eventos calculados como si fueran desastres.

## Tendencias — base existente, mejoras pendientes

SST mensual Caribe dispone de pendiente/intervalo por bloques y exportación CSV; RAPID dispone de medias anuales/pendiente descriptiva2005–2023. Resta revisar ajuste estacional, tratamiento de huecos e incertidumbre y cerrar el recorrido demostrable. Ninguna pendiente constituye pronóstico o causa.

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
