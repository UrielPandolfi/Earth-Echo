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

## Asociaciones — siguiente incremento

Pares científicos explícitos a priori: ENSO/SST Caribe y AMOC/SST Caribe. Exigir ventanas comparables, unidades/ámbitos declarados, eliminación explícita de estacionalidad/tendencia y conservación de huecos. Mostrar correlaciones y su sensibilidad temporal, sin búsqueda del mejor desfase, atribución causal o predicción. Usar bloqueo temporal para incertidumbre condicional, sin asumir independencia de trimestres solapados. Si faltan datos/variación, resultado no evaluable.

Credenciales Earthdata, más regiones/fuentes, rediseño visual y modelos predictivos nuevos son ampliaciones separadas. SMAP/GLDAS/IMERG reciente permanecen pendientes por decisión del usuario; [configuración](accesos.md).
