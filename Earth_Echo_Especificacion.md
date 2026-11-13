# Especificación de datos y predicción de Earth Echo

Documento de viabilidad e implementación para Uriel Pandolfi. Revisión del 12 de noviembre de 2026. Versión 1.0.

## Conclusión y alcance

Podemos programar un observatorio mundial que reúna observaciones, señales, tendencias y pronósticos. La cobertura mundial es viable para varias variables de gran escala. La capacidad de anticipar eventos concretos cambia mucho entre fenómenos y regiones. Esta especificación conserva las 31 familias discutidas y documenta 48 fuentes y referencias, sin afirmar que ya existe un predictor universal.

El documento está dirigido a Uriel Pandolfi y al equipo que construya la app para NASA Space Apps. Permite decidir qué integrar, qué desarrollar y dónde falta información. Las fichas definen datos y métodos candidatos. Ningún modelo propio fue entrenado, calibrado o evaluado durante este trabajo.

La primera versión puede tener un globo mundial real y varias capas operativas. Una capa con datos globales no garantiza pronósticos locales fiables. El contrato de cada módulo debe declarar su cobertura, unidad espacial, horizonte, fecha de emisión, incertidumbre y evidencia de validación.

Se consultó documentación pública el 12 de noviembre de 2026. Se comprobó acceso HTTP y JSON en una muestra de USGS, NOAA SWPC y NASA JPL CNEOS. Las descargas con credenciales y las integraciones del resto de productos quedan pendientes. Los enlaces y condiciones deben revisarse al implementar porque los proveedores actualizan colecciones y servicios.

## Qué representa cada señal

Observación significa que un instrumento o modelo de análisis estima el estado actual o pasado. Un valor de humedad bajo pertenece a esta clase. Un diagnóstico reconoce un patrón ya presente. Una tendencia describe la dirección de cambio durante un período con incertidumbre estadística.

Un pronóstico estima un resultado futuro en un lugar, una ventana temporal y una variable definidos. Un peligro describe la posibilidad de un fenómeno. El riesgo incorpora además exposición y vulnerabilidad; sin esos datos conviene mostrar peligro, no daños esperados.

Un nowcast describe el presente o una evolución inmediata según el sistema. Una alerta de tsunami puede anticipar la llegada a la costa después de que el fenómeno se inició. Una señal de investigación, como una hipótesis de inestabilidad de la AMOC, requiere otra etiqueta y no se convierte en fecha de catástrofe.

Probabilidad e índice son campos diferentes. Un FWI de cierto valor, un percentil de humedad o una anomalía no autorizan a inventar un porcentaje de ocurrencia. La probabilidad debe venir de un proveedor que la defina o de un modelo calibrado y evaluado.

## Cobertura mundial y datos que faltan

Podemos obtener mallas globales o casi globales de lluvia, temperatura, viento, humedad modelada, temperatura oceánica y otras variables. Esas mallas combinan instrumentos, interpolación y modelos. Una celda con valor no demuestra que exista una medición directa en ese lugar.

La cobertura espacial y la frecuencia de actualización son dimensiones separadas. Un satélite que pasa periódicamente no observa todos los puntos en cada minuto. Una serie mensual sirve para tendencias lentas, pero no para avisar una inundación que tarda veinte minutos en desarrollarse.

Los faltantes críticos aparecen en radar de tormentas, vigilancia geotécnica, gases volcánicos, niveles de lagos, drenaje urbano, manejo de represas, muestras de toxinas, oxígeno y microbiología. Existen redes locales, pero no identificamos una fuente abierta y homogénea mundial que resuelva todos esos campos.

En la interfaz, mostrar dato ausente, dato vencido y región sin modelo válido como estados explícitos. Un área sin reporte no recibe automáticamente color seguro. Un pronóstico regional puede aparecer en el globo mundial sin extender su geometría a todo el planeta.

## Alineación con NASA Space Apps

El desafío Earth System Trend Detective pide seleccionar variables ambientales, investigar regiones, visualizar series y analizar qué cambia, dónde, cuánto y con qué significancia. El pronóstico multifenómeno amplía el producto; no debe desplazar esas funciones centrales. Referencia D40.

La demo debería permitir elegir una región y variable, ver datos e historial, calcular tendencia e incertidumbre y luego abrir un pronóstico o experimento temporal relacionado. Se puede distinguir claramente qué parte usa datos NASA y qué parte integra otros centros científicos.

Para tendencias, proponer pendiente y su intervalo de incertidumbre, además de un método apropiado a estacionalidad y autocorrelación. Comparar meses equivalentes, evaluar Mann Kendall estacional o correcciones pertinentes y controlar comparaciones múltiples si se exploran miles de celdas. Una tendencia estadísticamente significativa no demuestra causa ni capacidad predictiva.

## Matriz de fenómenos

P1, P2 y P3 indican orden de implementación propuesto. No expresan nivel de peligro ni confianza científica.

| ID | Fenómeno | Cobertura del resultado | Prioridad | Fuentes |
| --- | --- | --- | --- | --- |
| F01 | Lluvias extremas | Global aproximado | P1 | D01 D07 D08 |
| F02 | Olas de calor | Global aproximado | P1 | D07 D08 D09 D05 |
| F03 | Olas de frío y heladas | Global aproximado | P2 | D07 D08 D30 |
| F04 | Tormentas severas y granizo | Parcial para eventos locales | P3 | D07 D08 D35 |
| F05 | Tornados | Regional | P3 | D07 D35 |
| F06 | Ciclones tropicales | Global con combinación de centros | P2 | D07 D13 D14 D35 D47 |
| F07 | Marejadas e inundación costera | Parcial para impacto local | P3 | D07 D14 D30 D31 D41 |
| F08 | Nieve y tormentas de hielo | Global aproximado | P2 | D07 D08 D30 |
| F09 | Tormentas de polvo | Global aproximado | P2 | D12 D07 |
| F10 | Contaminación y transporte de humo | Global aproximado | P2 | D12 D06 D07 |
| F11 | Sequías | Global aproximado | P1 | D01 D02 D03 D08 D09 D33 |
| F12 | Crecidas fluviales | Global aproximado en la red modelada | P1 | D10 D32 |
| F13 | Inundaciones repentinas | Regional para predicción útil | P3 | D01 D07 D10 D30 |
| F14 | Escasez de agua | Global para indicadores y parcial para abastecimiento | P2 | D03 D07 D08 D10 D33 |
| F15 | Peligro de incendios | Global aproximado | P1 | D11 D07 D04 D06 |
| F16 | Estrés agrícola | Global para indicadores y regional para rendimiento | P2 | D20 D04 D02 D03 D01 D45 |
| F17 | El Niño y La Niña | Global en influencia con índice del Pacífico | P1 | D13 D14 D09 D48 |
| F18 | Olas de calor marinas | Global con habilidad desigual | P2 | D13 D16 D09 D44 |
| F19 | Estrés térmico de corales | Global para monitoreo térmico | P1 | D15 |
| F20 | Floraciones de algas nocivas | Regional para nocividad y amplio para observación | P3 | D17 D14 D18 |
| F21 | Hipoxia acuática | Regional | P3 | D14 D18 |
| F22 | Condiciones favorables para Vibrio | Regional | P3 | D14 D18 |
| F23 | Langosta del desierto | Área biogeográfica específica | P3 | D19 D01 D04 D07 |
| F24 | Actividad volcánica y erupciones | Global para inventario y local para pronóstico | P3 | D23 D25 D42 |
| F25 | Deslizamientos por lluvia | Global aproximado para peligro | P2 | D24 D01 D02 D30 |
| F26 | Desbordes de lagos glaciares | Amplio para vigilancia y local para alerta | P3 | D25 D26 D30 D32 |
| F27 | Tsunamis | Cobertura por centros responsables | P3 | D27 D21 D31 |
| F28 | Réplicas sísmicas | Parcial en productos y potencialmente ampliable | P3 | D21 D22 D43 |
| F29 | Tormentas geomagnéticas | Global con efectos regionales | P2 | D28 |
| F30 | Impactos de asteroides conocidos | Global para objetos detectados | P3 | D29 |
| F31 | Cambios en la AMOC | Atlántico y proxies incompletos | Investigación | D34 D14 D13 D46 |

## Diccionario de variables

| ID | Variable | Unidad o representación | Fuentes | Tratamiento necesario |
| --- | --- | --- | --- | --- |
| V01 | Precipitación | mm por intervalo o mm/h | D01 D07 D08 | Conservar duración. No sumar tasas sin integrar tiempo. Los acumulados de forecast pueden reiniciarse con cada corrida. |
| V02 | Temperatura del aire a 2 m | K nativo y grados C canónicos | D07 D08 | Separar temperatura instantánea, mínima, máxima y promedio. Convertir Kelvin restando 273,15. |
| V03 | Humedad y punto de rocío | Porcentaje o K según campo | D07 D08 | La humedad relativa puede derivarse de temperatura y rocío con una fórmula documentada. Nunca mezclar humedad específica y relativa. |
| V04 | Viento y ráfaga | m/s y dirección derivada | D07 D08 | Conservar componentes u y v y altura. Viento medio y ráfaga no son intercambiables. |
| V05 | Presión atmosférica | Pa o hPa | D07 D08 | Distinguir presión superficial y reducida al nivel del mar. Para pasar de Pa a hPa, dividir por 100. |
| V06 | Perfiles verticales | K, m/s y humedad por nivel | D07 | Niveles y parámetros dependen del subconjunto abierto. El perfil de presión no incluye automáticamente el detalle de una tormenta. |
| V07 | CAPE y cizalladura | J/kg y m/s | D07 | CAPE mide energía potencial convectiva. La cizalladura requiere definir las alturas. Son condiciones favorables, no confirmación de tornado. |
| V08 | Humedad superficial del suelo | m3/m3 | D02 | Aplicar banderas de calidad y máscara. No comparar directamente una recuperación superficial con agua total de dos metros de suelo. |
| V09 | Agua en capas del suelo | kg/m2 o unidad del producto | D03 | Para convertir almacenamiento a humedad volumétrica hacen falta espesor y densidad del agua. Fijar capa y método. |
| V10 | Evapotranspiración y escorrentía | Tasa o acumulado según producto | D03 D08 | Revisar signo, acumulación y unidad. Una tasa de flujo de agua necesita integración temporal. |
| V11 | NDVI y EVI | Adimensional con escala | D04 | Aplicar factor de escala y QA. El compuesto de 16 días no debe tratarse como 16 observaciones diarias independientes. |
| V12 | Temperatura de superficie | K o grados C | D05 | Diferenciar de aire a 2 m. Registrar día, noche, cielo despejado y ventana del compuesto. |
| V13 | Peligro meteorológico de fuego | FWI y componentes | D11 | Un índice de peligro no es porcentaje de ignición. Conservar la definición del sistema y región de calibración. |
| V14 | Caudal y almacenamiento | m3/s y m3 | D10 D33 y registros locales | Caudal no es profundidad de inundación. Almacenamiento modelado y volumen observado de embalse requieren modelos de datos distintos. |
| V15 | SST y calor acumulado | Grados C y grados C semana | D13 D15 | SST es temperatura superficial del mar. DHW integra estrés térmico con metodología propia, sin equivalencia directa con daño confirmado. |
| V16 | Temperatura salinidad y corrientes | Unidad del NetCDF y m/s | D14 | Elegir profundidad y tiempo. No asumir salinidad en una unidad sin leer standard_name y units. |
| V17 | Clorofila y reflectancia | mg/m3 y unidad óptica | D17 | Controlar nubes, hielo y agua turbia. Clorofila no identifica automáticamente toxina ni especie. |
| V18 | Oxígeno nutrientes y microbiología | Unidades del laboratorio o producto | D18 y proveedor regional pendiente | Faltan series globales suficientes en esta especificación. Seleccionar producto biogeoquímico y muestras antes de habilitar estos predictores. |
| V19 | Partículas y gases atmosféricos | Concentración o carga de columna | D12 | Nivel superficial, columna y promedio temporal son diferentes. Convertir a microgramos/m3 solo cuando la definición lo permita. |
| V20 | Evento sísmico | Magnitud profundidad tiempo y posición | D21 | Magnitudes de distintas escalas no se mezclan sin criterio. Guardar revisiones, estado y umbral de detección. |
| V21 | Deformación y gases volcánicos | Desplazamiento y flujo según sensor | D25 y observatorio pendiente | InSAR observa desplazamiento en línea de visión tras procesamiento. Columna de SO2 satelital y flujo de gas local no son equivalentes. |
| V22 | Geometría y nivel de lagos | m2 y m con datum | D25 D26 D30 y sensores pendientes | Área observada no determina estabilidad del dique. Registrar fecha del contorno y procedencia del nivel. |
| V23 | Elevación y batimetría | m con datum | D30 D31 | Comprobar datum vertical, resolución y tipo de superficie. No mezclar alturas relativas y absolutas. |
| V24 | Viento solar e índices geomagnéticos | km/s nT e índice definido | D28 | Conservar unidades y ventana de cada feed. Un índice previsto y uno observado deben almacenarse en clases distintas. |
| V25 | Solución orbital y riesgo de impacto | Época probabilidad y parámetros | D29 | Conservar unidades y significado de cada campo de API. Un encuentro cercano no constituye un impacto previsto. |
| V26 | Transporte de la AMOC | Sverdrup según serie | D34 | Un Sverdrup representa un millón de m3/s. La sección RAPID no es una observación continua de todo el Atlántico. |

## Fichas de fenómenos

### F01 Lluvias extremas

**Salida.** Pronóstico importado y diagnóstico propio

**Cobertura.** Global aproximado

**Datos necesarios.** D01: lluvia reciente en mm y mm/h. D07: precipitación futura y miembros disponibles. D08: climatología por estación. Radar y pluviómetros locales para detalle.

**Cómo identificar y anticipar.** Detectar acumulados o intensidades que excedan percentiles locales. Para futuro, usar precipitación pronosticada y, si hay ensemble, proporción de miembros sobre el umbral. Corregir sesgos por región antes de llamarla probabilidad calibrada.

**Plazo.** Horas a varios días; detalle local decrece con el plazo.

**Faltantes y límites.** IMERG llega con demora y no resuelve cada tormenta urbana. Sin radar mundial homogéneo, mostrar una zona de riesgo y resolución explícita.

**Cómo comprobarlo.** Comparar con pluviómetros y estimaciones independientes. Medir Brier, precisión y exhaustividad por evento, plazo y región; tolerancia espacial para tormentas desplazadas.

**Fuentes.** [D01 NASA GPM IMERG](https://gpm.nasa.gov/data/imerg), [D07 ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data), [D08 ERA5 histórico](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels).

**Implementación.** Especificado sin implementar. Prioridad P1.

### F02 Olas de calor

**Salida.** Pronóstico y anomalía

**Cobertura.** Global aproximado

**Datos necesarios.** D07: temperatura a 2 m y humedad o punto de rocío. D08: extremos diarios por época. D09: perspectivas estacionales opcionales.

**Cómo identificar y anticipar.** Definir duración y umbral local antes de evaluar. Calcular días consecutivos por encima del umbral térmico y agregar incertidumbre del ensemble. Una ola de calor ambiental no equivale automáticamente a impacto sanitario.

**Plazo.** Días; semanas o meses para anomalías regionales probabilísticas.

**Faltantes y límites.** Las ciudades, interiores y exposición humana requieren datos adicionales. Temperatura MODIS de superficie no sustituye temperatura del aire.

**Cómo comprobarlo.** Verificar temperatura, inicio, duración y eventos fallidos contra estaciones. Comparar con climatología y persistencia; calibrar por estación del año.

**Fuentes.** [D07 ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data), [D08 ERA5 histórico](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels), [D09 C3S pronóstico estacional](https://cds.climate.copernicus.eu/datasets/seasonal-original-single-levels), [D05 NASA MODIS MOD11A2](https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD11A2/).

**Implementación.** Especificado sin implementar. Prioridad P1.

### F03 Olas de frío y heladas

**Salida.** Pronóstico de condiciones

**Cobertura.** Global aproximado

**Datos necesarios.** D07: temperatura mínima, viento, nubosidad y humedad. D08: distribución histórica. Estaciones de superficie y relieve fino si el objetivo es agrícola.

**Cómo identificar y anticipar.** Separar frío anómalo de temperatura bajo un umbral de helada. Calcular frecuencia de miembros que cruzan el umbral en una ventana. Ajustar elevación solo con un método validado.

**Plazo.** Días; el riesgo por lote tiene menor certeza.

**Faltantes y límites.** Helada en cultivo depende de temperatura al nivel de la planta, duración y especie. La malla global no captura todas las inversiones de valle.

**Cómo comprobarlo.** Evaluar mínimos, duración y falsas alertas contra estaciones o sensores agrícolas. Informar errores por altura y tipo de terreno.

**Fuentes.** [D07 ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data), [D08 ERA5 histórico](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels), [D30 Copernicus DEM](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM).

**Implementación.** Especificado sin implementar. Prioridad P2.

### F04 Tormentas severas y granizo

**Salida.** Riesgo de ambiente favorable

**Cobertura.** Parcial para eventos locales

**Datos necesarios.** D07: perfiles de temperatura, humedad y viento, CAPE y cizalladura derivada. Radares, rayos y reportes locales para tormentas específicas.

**Cómo identificar y anticipar.** Crear un diagnóstico de ambiente convectivo y usar avisos autorizados donde existan. Para predecir granizo específico se necesita un sistema convectivo regional o modelo calibrado con observaciones.

**Plazo.** Horas a días para ambientes de riesgo; menor plazo para una celda concreta.

**Faltantes y límites.** No hay una colección abierta homogénea mundial de radar y granizo identificada para este proyecto. CAPE alto no confirma tormenta ni granizo.

**Cómo comprobarlo.** Validar contra radares y reportes con sesgo de cobertura conocido. Separar días sin tormenta, precipitación no severa y eventos severos.

**Fuentes.** [D07 ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data), [D08 ERA5 histórico](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels), [D35 GDACS](https://www.gdacs.org/Documents/2025/GDACS_API_quickstart_v1.pdf).

**Implementación.** Especificado sin implementar. Prioridad P3.

### F05 Tornados

**Salida.** Avisos importados o riesgo ambiental

**Cobertura.** Regional

**Datos necesarios.** Perfiles atmosféricos de D07 para contexto. Radar Doppler y avisos del servicio meteorológico local para detección y evolución de tormentas.

**Cómo identificar y anticipar.** Importar avisos oficiales conservando emisor y geometría. Un detector propio con datos globales solo puede etiquetar ambientes favorables; la predicción localizada requiere sensores y experiencia regionales.

**Plazo.** Riesgo amplio con horas o días; advertencias localizadas suelen tener margen de minutos y pueden faltar.

**Faltantes y límites.** No hay predictor mundial fiable de tornados individuales construido con esta lista. No convertir índices de inestabilidad en puntos exactos de tornado futuro.

**Cómo comprobarlo.** Si se integra un servicio, medir demora y fidelidad de republicación. Un modelo propio necesita verificación regional por evento y falsas alarmas.

**Fuentes.** [D07 ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data), [D35 GDACS](https://www.gdacs.org/Documents/2025/GDACS_API_quickstart_v1.pdf).

**Implementación.** Especificado sin implementar. Prioridad P3.

### F06 Ciclones tropicales

**Salida.** Pronósticos y trayectorias importados

**Cobertura.** Global con combinación de centros

**Datos necesarios.** D07: circulación, ensembles y productos de trayectoria disponibles. D35: eventos y geometrías. D13 o D14: estado oceánico. IBTrACS para historial.

**Cómo identificar y anticipar.** Unificar identificadores y avisos de los centros meteorológicos responsables de cada cuenca. Mostrar trayectorias y distribución espacial cuando el proveedor la publique. Usar un modelo global como complemento.

**Plazo.** Días. Formación, trayectoria e intensidad tienen errores diferentes.

**Faltantes y límites.** GDACS no reemplaza todos los boletines de cada cuenca. IBTrACS es best track histórico, no pronóstico emitido en el pasado.

**Cómo comprobarlo.** Evaluar trayectoria en km, intensidad con unidades normalizadas y plazo. Evitar mezclar vientos sostenidos de 1 y 10 minutos. Comparar contra best tracks revisados.

**Fuentes.** [D07 ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data), [D13 NOAA OISST](https://www.ncei.noaa.gov/products/optimum-interpolation-sst), [D14 Copernicus Marine física oceánica](https://data.marine.copernicus.eu/product/GLOBAL_ANALYSISFORECAST_PHY_001_024/description), [D35 GDACS](https://www.gdacs.org/Documents/2025/GDACS_API_quickstart_v1.pdf), [D47 NOAA IBTrACS](https://www.ncei.noaa.gov/products/international-best-track-archive).

**Implementación.** Especificado sin implementar. Prioridad P2.

### F07 Marejadas e inundación costera

**Salida.** Peligro y pronóstico regional

**Cobertura.** Parcial para impacto local

**Datos necesarios.** D07: viento y presión. D31: batimetría. D30: elevación. Mareas, nivel observado, datum vertical y modelos hidráulicos costeros. D41 como referencia histórica.

**Cómo identificar y anticipar.** Integrar modelos operativos costeros cuando existan. Desarrollar un modelo propio exige resolver mareas, oleaje, marejada e inundación con malla y datum coherentes.

**Plazo.** Horas a días para un evento; años o décadas para escenarios de peligro.

**Faltantes y límites.** D14 no basta para inundación calle por calle. D41 contiene simulaciones históricas y escenarios, sin pronóstico diario futuro. GEBCO y DSM pueden ser insuficientes en costa.

**Cómo comprobarlo.** Comparar niveles con mareógrafos y extensión inundada con evidencia independiente. Separar error del nivel, error del terreno y exposición.

**Fuentes.** [D07 ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data), [D14 Copernicus Marine física oceánica](https://data.marine.copernicus.eu/product/GLOBAL_ANALYSISFORECAST_PHY_001_024/description), [D30 Copernicus DEM](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM), [D31 GEBCO](https://www.gebco.net/data-products/gridded-bathymetry-data), [D41 C3S GTSM nivel costero histórico y escenarios](https://cds.climate.copernicus.eu/datasets/sis-water-level-change-timeseries-cmip6).

**Implementación.** Especificado sin implementar. Prioridad P3.

### F08 Nieve y tormentas de hielo

**Salida.** Pronóstico meteorológico

**Cobertura.** Global aproximado

**Datos necesarios.** D07: perfiles térmicos, precipitación, tipo de precipitación y nieve equivalente en agua. D08 para umbrales y contexto histórico.

**Cómo identificar y anticipar.** Importar precipitación sólida o tipo de precipitación del modelo. La acumulación de nieve en centímetros necesita densidad y condiciones locales; la lluvia engelante requiere perfiles adecuados.

**Plazo.** Días; acumulaciones y límites de fase son sensibles al detalle local.

**Faltantes y límites.** Equivalente en agua no es altura de nieve. No convertir todo con una razón universal. El relieve fino y las superficies tratadas modifican el impacto.

**Cómo comprobarlo.** Verificar fase y acumulación contra estaciones y observación de nieve. Reportar errores cerca del punto de congelación por separado.

**Fuentes.** [D07 ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data), [D08 ERA5 histórico](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels), [D30 Copernicus DEM](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM).

**Implementación.** Especificado sin implementar. Prioridad P2.

### F09 Tormentas de polvo

**Salida.** Pronóstico importado

**Cobertura.** Global aproximado

**Datos necesarios.** D12: polvo y aerosoles por nivel o columna. D07: viento. D08 y datos de superficie para contexto de sequedad.

**Cómo identificar y anticipar.** Usar transporte de polvo del modelo químico atmosférico. Umbrales dependen de si se comunica concentración superficial, visibilidad o carga de columna.

**Plazo.** Horas a cinco días con el producto CAMS considerado.

**Faltantes y límites.** Aerosol óptico de columna no es concentración respirada en superficie. La ubicación y fuerza de fuentes pequeñas pueden estar mal representadas.

**Cómo comprobarlo.** Comparar con estaciones de partículas, visibilidad y redes de aerosoles cuando existan. Evaluar transporte e intensidad por separado.

**Fuentes.** [D12 CAMS composición atmosférica](https://ads.atmosphere.copernicus.eu/datasets/cams-global-atmospheric-composition-forecasts), [D07 ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data).

**Implementación.** Especificado sin implementar. Prioridad P2.

### F10 Contaminación y transporte de humo

**Salida.** Pronóstico de composición

**Cobertura.** Global aproximado

**Datos necesarios.** D12: PM y gases en superficie. D06: incendios detectados como contexto. D07: viento y mezcla atmosférica. Estaciones para calibración.

**Cómo identificar y anticipar.** Importar concentración pronosticada y aplicar promedios y norma explícitos si se publica un índice. La atribución al humo necesita productos o análisis específicos, no solo cercanía a un incendio.

**Plazo.** Horas a cinco días en el producto considerado.

**Faltantes y límites.** No predice exposiciones por calle ni prueba origen industrial o de incendio sin evidencia adicional. Las nuevas emisiones desconocidas generan errores.

**Cómo comprobarlo.** Comparar con monitores de superficie usando la misma unidad y promedio. Verificar sesgo, extremos y cobertura urbana; no validar solo contra otro modelo.

**Fuentes.** [D12 CAMS composición atmosférica](https://ads.atmosphere.copernicus.eu/datasets/cams-global-atmospheric-composition-forecasts), [D06 NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/api/), [D07 ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data).

**Implementación.** Especificado sin implementar. Prioridad P2.

### F11 Sequías

**Salida.** Diagnóstico y pronóstico a validar

**Cobertura.** Global aproximado

**Datos necesarios.** D01: lluvia. D02 y D03: humedad del suelo. D08: base estacional. D09: escenarios futuros. D33 puede complementar almacenamiento de agua.

**Cómo identificar y anticipar.** Definir sequía meteorológica, agrícola o hidrológica. Calcular anomalías y percentiles por estación. Para futuro, calibrar un modelo sencillo o usar escenarios meteorológicos con modelo terrestre; la analogía histórica es un candidato a evaluar.

**Plazo.** Semanas a meses; habilidad desigual según zona y época.

**Faltantes y límites.** SMAP no tiene toda la historia de GLDAS. Un percentil bajo actual es diagnóstico; sin evaluación temporal, el riesgo futuro es experimental.

**Cómo comprobarlo.** Comparar con persistencia y climatología. Usar ventanas futuras sin solapar entre entrenamiento y prueba. Medir probabilidades, eventos omitidos y falsas alarmas.

**Fuentes.** [D01 NASA GPM IMERG](https://gpm.nasa.gov/data/imerg), [D02 NASA SMAP SPL3SMP E](https://nsidc.org/data/spl3smp_e), [D03 NASA GLDAS](https://ldas.gsfc.nasa.gov/gldas/dataset), [D08 ERA5 histórico](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels), [D09 C3S pronóstico estacional](https://cds.climate.copernicus.eu/datasets/seasonal-original-single-levels), [D33 NASA GRACE asimilado para sequía](https://www.drought.gov/data-maps-tools/groundwater-and-soil-moisture-conditions-grace-data-assimilation).

**Implementación.** Especificado sin implementar. Prioridad P1.

### F12 Crecidas fluviales

**Salida.** Pronóstico hidrológico importado

**Cobertura.** Global aproximado en la red modelada

**Datos necesarios.** D10: ensemble de caudal y umbrales. D32: geometría de cuencas. Aforos locales para validación y corrección.

**Cómo identificar y anticipar.** Usar GloFAS para probabilidad de superar umbrales del caudal. Vincular cada tramo a un punto del modelo. Mantener la versión y fecha de corrida.

**Plazo.** Días y perspectivas más largas según producto y cuenca.

**Faltantes y límites.** Las represas y operaciones humanas pueden alterar la relación lluvia y caudal. Caudal elevado no establece por sí solo las viviendas inundadas.

**Cómo comprobarlo.** Evaluar caudal, fecha del pico y superación de umbrales contra aforos y eventos documentados. Usar reforecasts del mismo sistema para calibrar.

**Fuentes.** [D10 Copernicus GloFAS](https://global-flood.emergency.copernicus.eu/general-information/about-glofas), [D32 HydroATLAS](https://www.hydrosheds.org/hydroatlas).

**Implementación.** Especificado sin implementar. Prioridad P1.

### F13 Inundaciones repentinas

**Salida.** Riesgo de respuesta rápida

**Cobertura.** Regional para predicción útil

**Datos necesarios.** Lluvia de D01 como antecedente y D07 como escenario. Radar de alta frecuencia, drenaje, impermeabilización, suelo y D30 como contexto.

**Cómo identificar y anticipar.** Aplicar un modelo regional lluvia y escorrentía o importar avisos locales. Puede elaborarse un índice global exploratorio de susceptibilidad; requiere etiqueta experimental.

**Plazo.** Minutos a horas para avisos locales; a veces sin margen útil.

**Faltantes y límites.** La latencia de IMERG puede ser mayor que el tiempo de respuesta de una cuenca. GloFAS no cubre este problema completo. Falta drenaje urbano global detallado.

**Cómo comprobarlo.** Evaluar con registros de inundación y sensores de lluvia y nivel a frecuencia adecuada. La ausencia de reporte no se toma automáticamente como negativo.

**Fuentes.** [D01 NASA GPM IMERG](https://gpm.nasa.gov/data/imerg), [D07 ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data), [D10 Copernicus GloFAS](https://global-flood.emergency.copernicus.eu/general-information/about-glofas), [D30 Copernicus DEM](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM).

**Implementación.** Especificado sin implementar. Prioridad P3.

### F14 Escasez de agua

**Salida.** Riesgo hidrológico

**Cobertura.** Global para indicadores y parcial para abastecimiento

**Datos necesarios.** D03 y D33: almacenamiento y humedad estimados. D10: caudales. Nieve de D07 o D08. Embalses, extracción, demanda y reservas locales.

**Cómo identificar y anticipar.** Combinar déficit de aportes con almacenamiento y demanda. Publicar indicadores ambientales globales. La predicción de abastecimiento requiere un balance específico por sistema de agua.

**Plazo.** Semanas a meses para perspectivas; escenarios más largos con supuestos.

**Faltantes y límites.** GRACE no mide cada acuífero pequeño. No hay inventario operativo mundial completo de demanda, extracciones y manejo de embalses identificado aquí.

**Cómo comprobarlo.** Comparar con niveles, volúmenes y restricciones observadas en cada sistema. Evaluar por separado aportes naturales y decisiones de gestión.

**Fuentes.** [D03 NASA GLDAS](https://ldas.gsfc.nasa.gov/gldas/dataset), [D07 ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data), [D08 ERA5 histórico](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels), [D10 Copernicus GloFAS](https://global-flood.emergency.copernicus.eu/general-information/about-glofas), [D33 NASA GRACE asimilado para sequía](https://www.drought.gov/data-maps-tools/groundwater-and-soil-moisture-conditions-grace-data-assimilation).

**Implementación.** Especificado sin implementar. Prioridad P2.

### F15 Peligro de incendios

**Salida.** Peligro meteorológico y detección

**Cobertura.** Global aproximado

**Datos necesarios.** D11: FWI y componentes. D07: viento, humedad y temperatura. D04: estado de vegetación como complemento. D06: fuegos ya detectados.

**Cómo identificar y anticipar.** Integrar FWI pronosticado con clases de combustible apropiadas. Mantener separadas las capas de peligro previo, detección de fuego y propagación modelada.

**Plazo.** Hasta diez días para el peligro del sistema GWIS consultado. Detección depende de la pasada.

**Faltantes y límites.** La ignición humana no se deduce del clima. Predecir perímetro futuro requiere combustible, relieve, humedad y estado del incendio con mucho más detalle.

**Cómo comprobarlo.** Evaluar discriminación de días o áreas con fuego bajo sesgo de detección. Una calibración por ecosistema debe preceder a cualquier porcentaje de ignición.

**Fuentes.** [D11 Copernicus GWIS](https://gwis.jrc.ec.europa.eu/applications/data-and-services), [D07 ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data), [D04 NASA MODIS MOD13Q1](https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD13Q1/), [D06 NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/api/).

**Implementación.** Especificado sin implementar. Prioridad P1.

### F16 Estrés agrícola

**Salida.** Diagnóstico y riesgo experimental

**Cobertura.** Global para indicadores y regional para rendimiento

**Datos necesarios.** D20: estrés agrícola procesado. D04: NDVI y EVI. D02 y D03: agua en suelo. Lluvia y temperatura. Calendario, tipo de cultivo y prácticas locales.

**Cómo identificar y anticipar.** Detectar desviaciones de vegetación y humedad respecto de la fase de cultivo. La predicción de caída de rendimiento requiere un modelo adicional y datos de cosecha.

**Plazo.** Semanas o meses según cultivo y etapa; no garantía por parcela.

**Faltantes y límites.** Cosecha, riego y rotación pueden parecer anomalías. El satélite no explica por sí solo si el daño proviene de agua, plaga o manejo.

**Cómo comprobarlo.** Validar indicadores contra observaciones de campo y rendimiento contra estadísticas independientes. Separar años, regiones y cultivos en prueba.

**Fuentes.** [D20 FAO ASIS](https://www.fao.org/giews/earthobservation/access.jsp), [D04 NASA MODIS MOD13Q1](https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD13Q1/), [D02 NASA SMAP SPL3SMP E](https://nsidc.org/data/spl3smp_e), [D03 NASA GLDAS](https://ldas.gsfc.nasa.gov/gldas/dataset), [D01 NASA GPM IMERG](https://gpm.nasa.gov/data/imerg), [D45 Estudio de sequía agrícola argentina](https://hess.copernicus.org/articles/25/2475/2021/).

**Implementación.** Especificado sin implementar. Prioridad P2.

### F17 El Niño y La Niña

**Salida.** Diagnóstico y pronóstico climático

**Cobertura.** Global en influencia con índice del Pacífico

**Datos necesarios.** D13: SST del Pacífico. D14: estado oceánico por profundidad. D09: ensembles estacionales. Boletines ENSO de NOAA para referencia autorizada.

**Cómo identificar y anticipar.** Mostrar el diagnóstico y las probabilidades oficiales de fase con fecha y definición del índice. Un índice de SST propio sirve de contexto, pero debe especificar región, climatología y criterio.

**Plazo.** Meses, con dificultad dependiente de estación e inicialización.

**Faltantes y límites.** Una fase ENSO no determina la lluvia exacta en Rosario ni cada impacto mundial. Los índices y criterios pueden actualizarse; fijar la definición usada.

**Cómo comprobarlo.** Comparar probabilidades archivadas por horizonte y época del año. Para impactos locales se necesita otra validación específica.

**Fuentes.** [D13 NOAA OISST](https://www.ncei.noaa.gov/products/optimum-interpolation-sst), [D14 Copernicus Marine física oceánica](https://data.marine.copernicus.eu/product/GLOBAL_ANALYSISFORECAST_PHY_001_024/description), [D09 C3S pronóstico estacional](https://cds.climate.copernicus.eu/datasets/seasonal-original-single-levels), [D48 NOAA CPC ENSO](https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_advisory/ensodisc.shtml).

**Implementación.** Especificado sin implementar. Prioridad P1.

### F18 Olas de calor marinas

**Salida.** Diagnóstico y pronóstico probabilístico

**Cobertura.** Global con habilidad desigual

**Datos necesarios.** D13: SST diaria e historia estacional. D16: perspectivas existentes. D09: escenarios climáticos si se desarrolla un predictor propio.

**Cómo identificar y anticipar.** Definir evento por umbral estacional y duración. Distinguir temperatura alta respecto del clima histórico de la anomalía respecto de una base reciente. Importar forecast validado o evaluar un método propio.

**Plazo.** Semanas a meses; ciertos estudios hallan habilidad más larga en condiciones particulares.

**Faltantes y límites.** La habilidad no es uniforme entre océanos. El acceso numérico automatizado de D16 queda pendiente de verificar. No asumir que la precisión de una celda costera es la del océano abierto.

**Cómo comprobarlo.** Evaluar inicio, duración, intensidad y probabilidad contra SST posterior. Comparar con persistencia y climatología, sin usar futuros años en el umbral.

**Fuentes.** [D13 NOAA OISST](https://www.ncei.noaa.gov/products/optimum-interpolation-sst), [D16 NOAA pronóstico de olas de calor marinas](https://psl.noaa.gov/marine-heatwaves/), [D09 C3S pronóstico estacional](https://cds.climate.copernicus.eu/datasets/seasonal-original-single-levels), [D44 Estudio de predictibilidad de calor marino](https://repository.library.noaa.gov/view/noaa/45151).

**Implementación.** Especificado sin implementar. Prioridad P2.

### F19 Estrés térmico de corales

**Salida.** Indicadores y outlook importados

**Cobertura.** Global para monitoreo térmico

**Datos necesarios.** D15: HotSpot, DHW y alertas térmicas; outlook de blanqueamiento. Ubicación de arrecifes y observaciones biológicas para validar daño.

**Cómo identificar y anticipar.** Integrar indicadores y perspectivas de Coral Reef Watch conservando sus categorías. Explicar calor acumulado y plazo del pronóstico. La confirmación de blanqueamiento es un dato distinto.

**Plazo.** Actualización diaria de monitoreo; perspectivas hasta cuatro meses según producto.

**Faltantes y límites.** Temperatura no determina por sí sola susceptibilidad de todas las especies. La geometría de arrecifes y el forecast tienen resoluciones diferentes.

**Cómo comprobarlo.** Comparar forecast con estrés térmico observado. Para blanqueamiento real, usar censos y reportes biológicos; reportar su cobertura limitada.

**Fuentes.** [D15 NOAA Coral Reef Watch](https://coralreefwatch.noaa.gov/product/5km/index.php).

**Implementación.** Especificado sin implementar. Prioridad P1.

### F20 Floraciones de algas nocivas

**Salida.** Detección y pronóstico regional

**Cobertura.** Regional para nocividad y amplio para observación

**Datos necesarios.** D17: clorofila y reflectancia. D14: corrientes, temperatura y salinidad. D18: sistemas regionales. Nutrientes y muestras de especies o toxinas.

**Cómo identificar y anticipar.** Detectar anomalías ópticas como observación. Para nocividad, usar modelos regionales validados con muestreo. El transporte previsto de una floración detectada requiere corrientes y dinámica biológica.

**Plazo.** Días y perspectivas estacionales donde existe un sistema específico.

**Faltantes y límites.** Clorofila elevada no confirma toxinas. No se identificó una base abierta mundial con muestreo toxicológico suficiente para todas las especies y costas.

**Cómo comprobarlo.** Validar especie y toxina con muestras. Evaluar por región, especie y plazo. La validación óptica y la de riesgo sanitario son tareas separadas.

**Fuentes.** [D17 NASA Ocean Color](https://oceandata.sci.gsfc.nasa.gov/), [D14 Copernicus Marine física oceánica](https://data.marine.copernicus.eu/product/GLOBAL_ANALYSISFORECAST_PHY_001_024/description), [D18 NOAA pronósticos ecológicos regionales](https://oceanservice.noaa.gov/ecoforecasting/).

**Implementación.** Especificado sin implementar. Prioridad P3.

### F21 Hipoxia acuática

**Salida.** Pronóstico de oxígeno con modelo especializado

**Cobertura.** Regional

**Datos necesarios.** Oxígeno disuelto medido y perfiles. Nutrientes y aportes de ríos. D14 para física y mezcla; productos biogeoquímicos a seleccionar. D18 como ejemplo de sistemas existentes.

**Cómo identificar y anticipar.** Integrar un sistema regional de oxígeno o desarrollar un modelo acoplado de física y biogeoquímica. Temperatura y estratificación son factores explicativos, no mediciones directas de oxígeno.

**Plazo.** Días o perspectivas estacionales según región y producto.

**Faltantes y límites.** No hay una ingestión mundial validada de todos los insumos definida en este documento. Requiere elegir producto biogeoquímico, profundidad y umbral de oxígeno.

**Cómo comprobarlo.** Comparar concentración, profundidad y extensión con campañas, boyas y sensores. Validar extremos y errores de muestreo espacial.

**Fuentes.** [D14 Copernicus Marine física oceánica](https://data.marine.copernicus.eu/product/GLOBAL_ANALYSISFORECAST_PHY_001_024/description), [D18 NOAA pronósticos ecológicos regionales](https://oceanservice.noaa.gov/ecoforecasting/).

**Implementación.** Especificado sin implementar. Prioridad P3.

### F22 Condiciones favorables para Vibrio

**Salida.** Idoneidad ambiental o forecast importado

**Cobertura.** Regional

**Datos necesarios.** D14: temperatura y salinidad; datos costeros de mayor detalle y muestreos microbiológicos. D18: modelos regionales publicados.

**Cómo identificar y anticipar.** Importar un modelo específico por especie y ambiente. En otras regiones, una regla térmica solo puede indicar condiciones favorables hasta validarse con muestras.

**Plazo.** Días en los sistemas regionales que lo ofrecen.

**Faltantes y límites.** Agua cálida no confirma presencia, dosis, infección ni riesgo individual. El modelo de una bahía no se extrapola automáticamente a todas las costas.

**Cómo comprobarlo.** Verificar contra muestras y protocolos de laboratorio compatibles. Evaluar calibración por especie, salinidad, estación y región.

**Fuentes.** [D14 Copernicus Marine física oceánica](https://data.marine.copernicus.eu/product/GLOBAL_ANALYSISFORECAST_PHY_001_024/description), [D18 NOAA pronósticos ecológicos regionales](https://oceanservice.noaa.gov/ecoforecasting/).

**Implementación.** Especificado sin implementar. Prioridad P3.

### F23 Langosta del desierto

**Salida.** Vigilancia y perspectivas importadas

**Cobertura.** Área biogeográfica específica

**Datos necesarios.** D19: observaciones de campo y boletines. D01: lluvia. D04: vegetación. D07: viento para trayectorias. Temperatura para desarrollo biológico.

**Cómo identificar y anticipar.** Unir reportes y condiciones favorables de reproducción. Utilizar perspectivas FAO con fecha. Un pronóstico propio necesita dinámica de población y movimiento, además del hábitat.

**Plazo.** Semanas a meses según etapa y observaciones disponibles.

**Faltantes y límites.** La cobertura corresponde a langosta del desierto, no todas las especies. El muestreo de campo es esencial y no está distribuido uniformemente.

**Cómo comprobarlo.** Comparar con relevamientos posteriores y expansión reportada, considerando esfuerzo de observación. Evaluar llegada y reproducción por separado.

**Fuentes.** [D19 FAO Locust Watch y Locust Hub](https://www.fao.org/locust-watch/activities/dlis-home/early-warning/en), [D01 NASA GPM IMERG](https://gpm.nasa.gov/data/imerg), [D04 NASA MODIS MOD13Q1](https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD13Q1/), [D07 ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data).

**Implementación.** Especificado sin implementar. Prioridad P3.

### F24 Actividad volcánica y erupciones

**Salida.** Actividad y avisos importados

**Cobertura.** Global para inventario y local para pronóstico

**Datos necesarios.** D23: catálogo e historia. D25: imágenes y gases observables. Observatorio local: sismicidad, GNSS, deformación, gases y señales térmicas.

**Cómo identificar y anticipar.** Mostrar actividad y nivel de alerta del observatorio. La predicción exige interpretar cambios persistentes respecto de la línea base de cada volcán, con un modelo o criterio específico validado.

**Plazo.** Algunos eventos admiten aviso de horas o días. La agitación puede persistir años sin erupción.

**Faltantes y límites.** No hay red mundial abierta y uniforme con todos estos sensores. El catálogo de volcanes no aporta esos precursores. Una señal de SO2 o calor no basta para anunciar una erupción.

**Cómo comprobarlo.** Evaluar episodios con y sin erupción. Separar escalada de alerta, inicio, magnitud y duración. Revisión experta necesaria para un predictor nuevo.

**Fuentes.** [D23 Smithsonian Global Volcanism Program](https://volcano.si.edu/database/webservices.cfm), [D25 Copernicus Data Space](https://documentation.dataspace.copernicus.eu/APIs.html), [D42 USGS señales precursoras volcánicas](https://www.usgs.gov/faqs/how-can-we-tell-when-a-volcano-will-erupt).

**Implementación.** Especificado sin implementar. Prioridad P3.

### F25 Deslizamientos por lluvia

**Salida.** Nowcast o forecast según producto

**Cobertura.** Global aproximado para peligro

**Datos necesarios.** D24: producto LHASA. D01: precipitación. D02: humedad antecedente. D30: relieve. Geología y susceptibilidad según modelo.

**Cómo identificar y anticipar.** Priorizar integración de LHASA y conservar su definición de salida. Si se construye un predictor, modelar probabilidad de actividad en una unidad espacial y ventana definidas.

**Plazo.** Condiciones actuales y plazos cortos donde exista forecast documentado.

**Faltantes y límites.** No resuelve cada ladera, deslizamiento lento ni falla de roca. La calidad varía con geología y reporte de eventos. Nowcast no se debe presentar como anticipación futura.

**Cómo comprobarlo.** Validar contra inventarios independientes separados por región y evento de lluvia. Medir omisiones, falsas alarmas y resolución real.

**Fuentes.** [D24 NASA LHASA](https://gpm.nasa.gov/applications/landslides), [D01 NASA GPM IMERG](https://gpm.nasa.gov/data/imerg), [D02 NASA SMAP SPL3SMP E](https://nsidc.org/data/spl3smp_e), [D30 Copernicus DEM](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM).

**Implementación.** Especificado sin implementar. Prioridad P2.

### F26 Desbordes de lagos glaciares

**Salida.** Susceptibilidad y detección de cambios

**Cobertura.** Amplio para vigilancia y local para alerta

**Datos necesarios.** D25: imágenes ópticas y SAR para extensión del lago y cambios. D26: glaciares. D30: relieve. Nivel del lago, dique, sismicidad y caudal con sensores locales.

**Cómo identificar y anticipar.** Detectar crecimiento y cambios de la cuenca para priorizar inspección. Una alerta de rotura o propagación requiere sensores rápidos y modelo hidráulico del valle.

**Plazo.** Meses o años para vigilancia de peligro; minutos u horas de margen tras detectar una liberación, según lugar.

**Faltantes y límites.** La pasada satelital no detecta continuamente una rotura súbita. El inventario RGI no contiene niveles ni estabilidad de diques. No hay fecha de rotura mundial deducible solo del tamaño del lago.

**Cómo comprobarlo.** Validar contornos y cambios contra imágenes de mayor detalle. Para alerta, probar detección, demora y tiempo de llegada con casos y simulaciones de sitio.

**Fuentes.** [D25 Copernicus Data Space](https://documentation.dataspace.copernicus.eu/APIs.html), [D26 Randolph Glacier Inventory](https://rgidata.org/), [D30 Copernicus DEM](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM), [D32 HydroATLAS](https://www.hydrosheds.org/hydroatlas).

**Implementación.** Especificado sin implementar. Prioridad P3.

### F27 Tsunamis

**Salida.** Alertas y llegada importadas

**Cobertura.** Cobertura por centros responsables

**Datos necesarios.** D27: mensajes CAP y Atom. D21: sismo detectado como contexto. Redes de nivel del mar y boyas. D31: batimetría para modelado específico.

**Cómo identificar y anticipar.** Integrar mensajes autorizados y sus cancelaciones. Mostrar tiempo de arribo solo si el emisor lo ofrece. Un modelo independiente requiere caracterizar la fuente y propagar ondas con datos adecuados.

**Plazo.** Minutos a horas antes de llegar a una costa, después de iniciada la fuente; puede no haber margen cercano.

**Faltantes y límites.** No predice el terremoto. Los centros NOAA no cubren por sí solos todos los ámbitos del mundo. Un sismo fuerte no confirma que se haya generado un tsunami.

**Cómo comprobarlo.** Verificar integridad de mensajes, tiempo de ingestión y cancelaciones. Para pronóstico propio, contrastar altura y arribo con mareógrafos y boyas.

**Fuentes.** [D27 NOAA Tsunami Warning Centers](https://www.tsunami.gov/?page=productRetrieval), [D21 USGS ComCat y FDSN](https://earthquake.usgs.gov/fdsnws/event/1/), [D31 GEBCO](https://www.gebco.net/data-products/gridded-bathymetry-data).

**Implementación.** Especificado sin implementar. Prioridad P3.

### F28 Réplicas sísmicas

**Salida.** Probabilidades tras un sismo

**Cobertura.** Parcial en productos y potencialmente ampliable

**Datos necesarios.** D21: secuencia sísmica y completitud. D22: productos de forecast. Parámetros tectónicos y de red para un modelo propio.

**Cómo identificar y anticipar.** Importar la probabilidad publicada para magnitud y ventana concretas. Si se desarrolla un modelo, calibrar una familia tipo ETAS o frecuencia temporal para la región y evaluar fuera de muestra.

**Plazo.** Días a meses según ventana. Siempre condicionado a un evento y estado de la secuencia.

**Faltantes y límites.** No garantiza hora o lugar de la próxima réplica. Los productos públicos no existen para todos los eventos del mundo. Revisiones del catálogo afectan la evaluación retrospectiva.

**Cómo comprobarlo.** Usar puntuaciones probabilísticas y comparación con un modelo base. Evaluar secuencias completas que no se hayan usado para ajustar parámetros.

**Fuentes.** [D21 USGS ComCat y FDSN](https://earthquake.usgs.gov/fdsnws/event/1/), [D22 USGS pronóstico de réplicas](https://earthquake.usgs.gov/data/oaf/overview.php), [D43 USGS límites de predicción sísmica](https://www.usgs.gov/faqs/can-you-predict-earthquakes).

**Implementación.** Especificado sin implementar. Prioridad P3.

### F29 Tormentas geomagnéticas

**Salida.** Observación y pronóstico importados

**Cobertura.** Global con efectos regionales

**Datos necesarios.** D28: eyecciones observadas, viento solar, campo magnético e índices. Avisos y modelos operativos SWPC.

**Cómo identificar y anticipar.** Integrar watch, warning y forecast manteniendo producto, escala y emisor. Explicar qué señales sostienen la perspectiva y qué se mide al acercarse a la Tierra.

**Plazo.** Horas a días en casos favorables. La precisión aumenta o cambia al llegar nuevas mediciones.

**Faltantes y límites.** El impacto depende de orientación magnética y dinámica espacial. Una fulguración visible no permite anticipar con antelación su propia radiación en la Tierra.

**Cómo comprobarlo.** Comparar nivel y ventana previstos con índices observados. Guardar emisiones históricas y revisiones; medir falsas alertas y eventos omitidos.

**Fuentes.** [D28 NOAA SWPC](https://www.swpc.noaa.gov/content/data-access).

**Implementación.** Especificado sin implementar. Prioridad P2.

### F30 Impactos de asteroides conocidos

**Salida.** Evaluación orbital importada

**Cobertura.** Global para objetos detectados

**Datos necesarios.** D29: Scout y Sentry con soluciones, probabilidades y épocas de observación. Seguimiento astronómico realizado por las redes de observatorios.

**Cómo identificar y anticipar.** Publicar la evaluación CNEOS conservando incertidumbre y fecha. El mecanismo es cálculo orbital, no analogía con catástrofes pasadas. Separar riesgo de impacto y mero acercamiento.

**Plazo.** Desde horas hasta plazos largos, según descubrimiento, observaciones y geometría orbital.

**Faltantes y límites.** Un cuerpo no descubierto queda fuera. Probabilidades pueden subir o bajar al incorporar datos. No convertir diámetro incierto en daños exactos.

**Cómo comprobarlo.** Comparar evolución de soluciones y, cuando existe impacto, momento y región observados. El pequeño número de impactos anticipados limita una evaluación estadística general.

**Fuentes.** [D29 NASA JPL CNEOS](https://ssd-api.jpl.nasa.gov/doc/index.php).

**Implementación.** Especificado sin implementar. Prioridad P3.

### F31 Cambios en la AMOC

**Salida.** Tendencias y análisis exploratorio

**Cobertura.** Atlántico y proxies incompletos

**Datos necesarios.** D34: transporte observado. D14: temperatura, salinidad y corrientes modeladas. D13: SST como contexto y posibles proxies con respaldo científico.

**Cómo identificar y anticipar.** Mostrar variabilidad, tendencia e incertidumbre. Las señales exploratorias de pérdida de estabilidad requieren hipótesis y pruebas frente a ruido y cambios de observación; no producen fecha operativa de colapso.

**Plazo.** Variabilidad de años a décadas; sin cuenta regresiva fiable al colapso.

**Faltantes y límites.** Historia instrumental relativamente corta y proxies no equivalentes a observación directa. No hay suficientes colapsos modernos observados para entrenar y validar un clasificador convencional.

**Cómo comprobarlo.** Evaluar estabilidad de resultados con ventanas, métodos y proxies. Usar simulaciones para investigación y comunicar que no validan una predicción operativa del mundo real.

**Fuentes.** [D34 RAPID AMOC](https://rapid.ac.uk/data/data-download), [D14 Copernicus Marine física oceánica](https://data.marine.copernicus.eu/product/GLOBAL_ANALYSISFORECAST_PHY_001_024/description), [D13 NOAA OISST](https://www.ncei.noaa.gov/products/optimum-interpolation-sst), [D46 Met Office sobre AMOC](https://weather.metoffice.gov.uk/learn-about/weather/oceans/amoc).

**Implementación.** Especificado sin implementar. Prioridad Investigación.

## Catálogo de fuentes

Los campos siguientes distinguen el dato disponible del uso propuesto. Los métodos de las fichas son un diseño a evaluar, salvo cuando se integran productos existentes con su metodología.

### D01 NASA GPM IMERG

[Documentación oficial](https://gpm.nasa.gov/data/imerg)

**Datos.** Tasa y acumulación de precipitación. Elegir producto y unidad nativa antes de convertir a mm por intervalo.

**Cobertura y resolución.** Malla global de 0,1 grados del producto actual. La calidad cambia con latitud, nieve, relieve y disponibilidad de observaciones.

**Frecuencia e historia.** Intervalos de 30 minutos. Early Run tiene latencia nominal de unas 4 horas. Late y Final priorizan otras necesidades; Final no es tiempo real.

**Acceso.** Earthdata o PPS según distribución. HTTPS y formatos científicos; el directorio ofrece derivados GeoTIFF. Registrar colección y versión.

**Límites.** Es precipitación estimada, no futura. Las diferencias entre Early y Final importan en pruebas históricas. No usar Final como si hubiese estado disponible ese día.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D02 NASA SMAP SPL3SMP E

[Documentación oficial](https://nsidc.org/data/spl3smp_e)

**Datos.** Humedad volumétrica superficial del suelo en m3/m3 y banderas de calidad.

**Cobertura y resolución.** Malla EASE Grid de 9 km. Malla no equivale a resolución efectiva independiente. Recuperaciones inválidas en ciertas superficies y condiciones.

**Frecuencia e historia.** Producto diario con cobertura dependiente de pasadas. Consultar fechas de cada gránulo y latencia efectiva.

**Acceso.** Cuenta Earthdata gratuita. Buscar por short name SPL3SMP_E en CMR y descargar el producto con earthaccess.

**Límites.** No observa directamente toda la zona radicular. Excluir suelo congelado, nieve, agua y recuperaciones rechazadas. No rellenar huecos como mediciones reales.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D03 NASA GLDAS

[Documentación oficial](https://ldas.gsfc.nasa.gov/gldas/dataset)

**Datos.** Humedad del suelo por capas, evapotranspiración, escorrentía, temperatura y forzantes. Revisar unidades de cada variable.

**Cobertura y resolución.** Superficie terrestre modelada. GLDAS Noah 2.1 tiene producto de 0,25 grados; no representa parcelas ni sistemas urbanos.

**Frecuencia e historia.** Campos de 3 horas y mensuales; 2.1 desde 2000. Producto principal y Early Product tienen disponibilidad diferente.

**Acceso.** GES DISC, Earthdata, descargas y subconjuntos. Giovanni sirve para explorar series. Fijar GLDAS_NOAH025_3H y versión.

**Límites.** Es salida de un modelo con observaciones asimiladas o forzantes, no una medición satelital directa. No combinar series 2.0 y 2.1 sin evaluar discontinuidades.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D04 NASA MODIS MOD13Q1

[Documentación oficial](https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD13Q1/)

**Datos.** NDVI, EVI y calidad. Aplicar escala y máscara del producto.

**Cobertura y resolución.** Vegetación terrestre global en mosaicos de 250 m, sujeto a nubes y calidad.

**Frecuencia e historia.** Compuestos de 16 días. La ventana del compuesto no es una observación instantánea ni una latencia.

**Acceso.** CMR y Earthdata con archivos HDF. Identificador MOD13Q1, colección 6.1 documentada.

**Límites.** Un cambio de verdor puede deberse a cosecha, estación, incendio o nubes. No prueba sequía, pérdida de rendimiento ni mortalidad por sí solo.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D05 NASA MODIS MOD11A2

[Documentación oficial](https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD11A2/)

**Datos.** Temperatura de superficie terrestre diurna y nocturna, emisividad y calidad. Kelvin y factor de escala según metadatos.

**Cobertura y resolución.** Superficie terrestre global a 1 km en mosaicos.

**Frecuencia e historia.** Promedios de 8 días. No es lectura continua ni reemplazo del termómetro a 2 m.

**Acceso.** Earthdata y LAADS. Archivos de la colección MOD11A2.

**Límites.** Contaminación por nubes y muestreo de cielo despejado. Temperatura de superficie y temperatura del aire tienen significados distintos.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D06 NASA FIRMS

[Documentación oficial](https://firms.modaps.eosdis.nasa.gov/api/)

**Datos.** Detecciones de anomalías térmicas o fuego activo, tiempo de adquisición, confianza y potencia radiativa según sensor.

**Cobertura y resolución.** Cobertura mundial con MODIS y VIIRS. La detección depende del tamaño, nubes, humo y pasada.

**Frecuencia e historia.** Productos globales NRT disponibles nominalmente dentro de 3 horas de la observación, no cada 3 horas sobre cada punto.

**Acceso.** API CSV con MAP_KEY gratuita y límites de transacciones. Consultar data_availability antes de pedir intervalos.

**Límites.** Detecta fuego o calor existente. Un punto no es el perímetro completo ni una predicción de ignición. Conservar identificador del sensor.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D07 ECMWF Open Data

[Documentación oficial](https://www.ecmwf.int/en/forecasts/datasets/open-data)

**Datos.** Temperatura, punto de rocío, viento, presión, precipitación, perfiles, CAPE y otros parámetros del subconjunto. Verificar códigos disponibles.

**Cobertura y resolución.** Pronóstico atmosférico mundial. IFS publica mallas 0,25 y 0,1 grados según documentación vigente; no resuelve cada tormenta local.

**Frecuencia e historia.** Ciclos y pasos según stream. Productos de alcance medio; guardar initialization time y forecast step.

**Acceso.** GRIB2 público con ecmwf-opendata. CC BY 4.0 y términos ECMWF. Existe archivo rodante corto; guardar las corridas usadas.

**Límites.** No todo parámetro de IFS está en el subconjunto abierto. Productos históricos, ensembles y servicios de entrega deben revisarse por separado.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D08 ERA5 histórico

[Documentación oficial](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels)

**Datos.** Temperatura a 2 m, viento, presión, precipitación, nieve y variables de superficie. Pedir niveles de presión aparte si hacen falta.

**Cobertura y resolución.** Reanálisis mundial. Malla atmosférica publicada de 0,25 grados.

**Frecuencia e historia.** Horario, desde 1940. Hay retraso de publicación y revisiones. No es pronóstico archivado.

**Acceso.** Cuenta CDS, aceptación de licencia del dataset y API CDS. Subconjuntos por área, fecha y variable.

**Límites.** Reconstruye el pasado usando información posterior. Sirve como referencia histórica; no demuestra qué se podía saber en tiempo real. La precipitación acumulada necesita tratamiento temporal correcto.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D09 C3S pronóstico estacional

[Documentación oficial](https://cds.climate.copernicus.eu/datasets/seasonal-original-single-levels)

**Datos.** Ensembles de precipitación, temperatura y variables oceánicas o atmosféricas según centro y colección.

**Cobertura y resolución.** Mallas mundiales con habilidad desigual según región, estación, variable y horizonte.

**Frecuencia e historia.** Corridas estacionales. Revisar centros, meses de inicialización, horizonte y reforecasts disponibles.

**Acceso.** CDS API con cuenta y términos aceptados. Conservar centro, sistema, versión, miembro y fecha de corrida.

**Límites.** Predice distribuciones estacionales. No permite afirmar qué día lloverá dentro de seis meses. Calibrar contra reforecasts compatibles.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D10 Copernicus GloFAS

[Documentación oficial](https://global-flood.emergency.copernicus.eu/general-information/about-glofas)

**Datos.** Caudal de ríos y pronósticos hidrológicos probabilísticos. Unidades de caudal m3/s; umbrales según producto.

**Cobertura y resolución.** Red fluvial global modelada. Cobertura útil condicionada por tamaño de cuenca, regulación y calidad local.

**Frecuencia e historia.** Productos operativos y perspectivas a distintos plazos. Elegir una versión y confirmar frecuencia y plazo en el catálogo actual.

**Acceso.** Productos cems-glofas-historical, cems-glofas-forecast y cems-glofas-reforecast a resolver en CDS y documentación CEMS.

**Límites.** No es un pronóstico global de inundación urbana, costera ni de toda inundación repentina. Caudal alto no da automáticamente profundidad de agua sobre una calle.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D11 Copernicus GWIS

[Documentación oficial](https://gwis.jrc.ec.europa.eu/applications/data-and-services)

**Datos.** Fire Weather Index y componentes de peligro meteorológico de incendio, además de capas de combustibles según servicio.

**Cobertura y resolución.** Productos globales de peligro. La aplicabilidad depende del ecosistema y combustible.

**Frecuencia e historia.** Pronóstico de peligro hasta 10 días en el sistema documentado. Históricos y reanálisis por vías diferentes.

**Acceso.** Portal GWIS y documentación CEMS Fire Data access. Confirmar exportación, licencia y acceso del campo numérico elegido.

**Límites.** FWI no es probabilidad calibrada de que comience un incendio. Un servicio de mapas puede no permitir descargar toda la serie analítica.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D12 CAMS composición atmosférica

[Documentación oficial](https://ads.atmosphere.copernicus.eu/datasets/cams-global-atmospheric-composition-forecasts)

**Datos.** Aerosoles, polvo, PM y gases según variable. Distinguir concentración superficial de cantidad integrada en columna.

**Cobertura y resolución.** Modelos mundiales. Documentación ADS describe malla regular 0,4 grados; comprobar versión seleccionada.

**Frecuencia e historia.** Dos corridas diarias con pronósticos de cinco días. Archivo operativo distinto del reanálisis de larga duración.

**Acceso.** ADS API y cuenta con licencia aceptada. Solicitar unidades y niveles correctos.

**Límites.** No reproduce exposición individual ni diferencias por calle. La conversión a índice de calidad del aire exige norma y ventana de promediado explícitas.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D13 NOAA OISST

[Documentación oficial](https://www.ncei.noaa.gov/products/optimum-interpolation-sst)

**Datos.** Temperatura de superficie del mar y variables auxiliares del producto. Grados Celsius según metadatos.

**Cobertura y resolución.** Grilla oceánica mundial de 0,25 grados construida con satélites y mediciones in situ.

**Frecuencia e historia.** Diario desde septiembre de 1981, con publicación y revisiones propias.

**Acceso.** NCEI y servidores NOAA enlazados en la ficha; archivos NetCDF.

**Límites.** Campo interpolado y suavizado. No resuelve todos los estuarios, arrecifes ni cambios subsuperficiales.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D14 Copernicus Marine física oceánica

[Documentación oficial](https://data.marine.copernicus.eu/product/GLOBAL_ANALYSISFORECAST_PHY_001_024/description)

**Datos.** Temperatura, salinidad, corrientes, nivel del mar y otras variables por profundidad.

**Cobertura y resolución.** Océano global a 1/12 de grado nominal. Estuarios y costa requieren productos regionales más detallados.

**Frecuencia e historia.** Pronóstico de 10 días actualizado diariamente según ficha. Ventana operativa móvil; los reanálisis son otros productos.

**Acceso.** Copernicus Marine Toolbox, CLI o Python API. Revisar cuenta, versión y licencia del producto.

**Límites.** No convertir nivel marino modelado en inundación costera sin mareas, datum, batimetría y elevación local compatibles.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D15 NOAA Coral Reef Watch

[Documentación oficial](https://coralreefwatch.noaa.gov/product/5km/index.php)

**Datos.** SST, anomalías, HotSpot, Degree Heating Weeks y Bleaching Alert Area. DHW integra estrés térmico.

**Cobertura y resolución.** Monitoreo oceánico global a 5 km; enfocar arrecifes y controles de calidad.

**Frecuencia e historia.** Monitoreo diario y producto separado Four Month Coral Bleaching Outlook. Resolución y frecuencia del outlook son propias.

**Acceso.** NetCDF vía HTTP y servidores indicados. Metodología y catálogo de pronósticos disponibles en el portal.

**Límites.** Estrés térmico y riesgo de blanqueamiento no confirman daño biológico observado. No asignar automáticamente los 5 km al pronóstico de cuatro meses.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D16 NOAA pronóstico de olas de calor marinas

[Documentación oficial](https://psl.noaa.gov/marine-heatwaves/)

**Datos.** Diagnóstico oceánico y perspectivas probabilísticas basadas en NMME y CFSv2.

**Cobertura y resolución.** Perspectiva mundial con habilidad dependiente de región, estación y estado climático.

**Frecuencia e historia.** Estacional. Confirmar última emisión y disponibilidad del archivo numérico; no asumir API estable por existir un gráfico.

**Acceso.** Portal NOAA PSL y documentación científica. Para ingestión masiva, resolver enlace de datos y permiso vigente.

**Límites.** En esta especificación está verificado el producto público, no la automatización del archivo numérico. Alternativa: desarrollar y validar un modelo con D09 y D13.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D17 NASA Ocean Color

[Documentación oficial](https://oceandata.sci.gsfc.nasa.gov/)

**Datos.** Clorofila a en mg/m3 y reflectancias, además de banderas de calidad según sensor.

**Cobertura y resolución.** Observaciones amplias del océano. Hay huecos por nubes, hielo, geometría y condiciones ópticas costeras.

**Frecuencia e historia.** Productos por órbita y compuestos de varios intervalos; elegir colección y fecha efectiva de disponibilidad.

**Acceso.** OB DAAC y Earthdata, descargas de Level 2 y Level 3 con NetCDF según producto.

**Límites.** Clorofila alta no identifica una especie tóxica ni una toxina. El agua turbia costera puede sesgar las recuperaciones.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D18 NOAA pronósticos ecológicos regionales

[Documentación oficial](https://oceanservice.noaa.gov/ecoforecasting/)

**Datos.** Productos regionales de algas nocivas, hipoxia y condiciones favorables para patógenos costeros.

**Cobertura y resolución.** Regiones específicas, principalmente de Estados Unidos. No equivale a un servicio mundial completo.

**Frecuencia e historia.** Depende del sistema: boletines, productos de corto plazo y perspectivas estacionales.

**Acceso.** Resolver datos o servicio de cada programa desde el portal. Un boletín público no garantiza API numérica.

**Límites.** La extrapolación mundial exige observaciones y calibración nuevas. No inferir toxicidad o enfermedad humana desde temperatura del agua.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D19 FAO Locust Watch y Locust Hub

[Documentación oficial](https://www.fao.org/locust-watch/activities/dlis-home/early-warning/en)

**Datos.** Observaciones de langosta del desierto, reproducción, lluvia, vegetación y trayectorias de viento.

**Cobertura y resolución.** Área biogeográfica de la langosta del desierto y países vigilados. No cubre todas las plagas del mundo.

**Frecuencia e historia.** Boletines y observaciones con frecuencia propia. Revisar fecha y esfuerzo de muestreo.

**Acceso.** Portal y https://locust-hub-hqfao.hub.arcgis.com/ para explorar capas. Confirmar metadatos, exportación y términos de cada capa.

**Límites.** Un satélite no cuenta directamente las langostas. Ausencia de observaciones de campo no prueba ausencia de plaga.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D20 FAO ASIS

[Documentación oficial](https://www.fao.org/giews/earthobservation/access.jsp)

**Datos.** Indicadores de estrés agrícola, vegetación y condiciones de sequedad ya procesados.

**Cobertura y resolución.** Rásteres globales de 1 km indicados en el portal; interpretar por calendario y máscara agrícola.

**Frecuencia e historia.** Histórico desde 1984 según portal; frecuencia y ventana según indicador.

**Acceso.** Image services y recursos de acceso publicados por FAO; revisar licencia y capacidad de descarga por capa.

**Límites.** Indicador de estrés no equivale a toneladas de cosecha perdidas. El rendimiento necesita estadísticas de producción y prácticas agrícolas.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D21 USGS ComCat y FDSN

[Documentación oficial](https://earthquake.usgs.gov/fdsnws/event/1/)

**Datos.** Eventos sísmicos, magnitud, profundidad, hora, coordenadas, calidad y revisiones.

**Cobertura y resolución.** Catálogo mundial con capacidad de detección desigual. Los sismos pequeños faltan en muchas regiones.

**Frecuencia e historia.** Feeds recientes y consultas históricas. La información cambia al revisarse los eventos.

**Acceso.** API FDSN GET, GeoJSON y otros formatos sin clave para consultas públicas. Para mapa reciente, usar feeds recomendados.

**Límites.** Un catálogo de sismos no permite predecir el próximo terremoto. Guardar versión y completitud de la secuencia.

**Verificación.** Documentación consultada y una petición HTTP pública con JSON válido comprobada. Sin validar el modelo ni el flujo completo.

### D22 USGS pronóstico de réplicas

[Documentación oficial](https://earthquake.usgs.gov/data/oaf/overview.php)

**Datos.** Probabilidades de réplicas por umbral de magnitud y ventana temporal.

**Cobertura y resolución.** Eventos y regiones para los que USGS publica el producto. No prometer un pronóstico para cada sismo mundial.

**Frecuencia e historia.** Actualizaciones después del evento principal y ventanas temporales propias.

**Acceso.** Productos enlazados a las páginas de eventos de USGS. Confirmar formato y vínculo de cada producto.

**Límites.** Si se implementa un modelo propio en otras regiones, se necesita calibración tectónica y estimar el umbral de completitud.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D23 Smithsonian Global Volcanism Program

[Documentación oficial](https://volcano.si.edu/database/webservices.cfm)

**Datos.** Ubicación de volcanes, características e historial de erupciones.

**Cobertura y resolución.** Catálogo mundial conocido. No es una red mundial homogénea de sensores en tiempo real.

**Frecuencia e historia.** Actualizaciones de base e informes de actividad. No inferir frecuencia continua del catálogo.

**Acceso.** WFS con GetCapabilities y GetFeature. Exporta CSV, GML, GeoJSON, KML y Shapefile. Respetar cita y términos Smithsonian.

**Límites.** No incluye todos los datos locales necesarios de gases, deformación y sismicidad para pronosticar una erupción.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D24 NASA LHASA

[Documentación oficial](https://gpm.nasa.gov/applications/landslides)

**Datos.** Peligro de deslizamientos por lluvia con precipitación, humedad antecedente y susceptibilidad del terreno.

**Cobertura y resolución.** Cobertura global nominal del modelo, con máscaras y desempeño regional propios.

**Frecuencia e historia.** Nowcasts y otros productos según versión. Confirmar si la capa concreta es diagnóstico actual o pronóstico futuro.

**Acceso.** Acceso enlazado a NASA Landslides y GPM Viewer. Revisar archivos y servicios disponibles de la versión elegida.

**Límites.** No predice el colapso de cada ladera ni sustituye sensores geotécnicos locales. El inventario de eventos tiene sesgo de reporte.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D25 Copernicus Data Space

[Documentación oficial](https://documentation.dataspace.copernicus.eu/APIs.html)

**Datos.** Sentinel 1 SAR para cambios y deformación; Sentinel 2 óptico para agua y vegetación; Sentinel 5P para gases según producto.

**Cobertura y resolución.** Misiones de alcance amplio. Adquisición, resolución, nubes, bandas y geometría varían por misión y lugar.

**Frecuencia e historia.** Por pasada y procesamiento. Revisar hora de adquisición y publicación de cada escena.

**Acceso.** Catálogos STAC y OData. Descargas y procesamiento pueden requerir cuenta, token y cuotas. Usar documentación actual.

**Límites.** InSAR necesita series SLC compatibles y correcciones. Una imagen SAR no es una medición directa de deformación. SO2 atmosférico no reemplaza el flujo de gas medido en un volcán.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D26 Randolph Glacier Inventory

[Documentación oficial](https://rgidata.org/)

**Datos.** Contornos de glaciares e identificadores de inventario.

**Cobertura y resolución.** Inventario mundial de glaciares fuera de las grandes capas de hielo, según versión.

**Frecuencia e historia.** Versiones de inventario, sin actualización continua. Cada geometría representa una época.

**Acceso.** Archivos y documentación RGI; GLIMS ofrece información complementaria por fecha.

**Límites.** No incluye nivel de cada lago, estabilidad de cada dique ni disparadores de una rotura. Es una capa de contexto.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D27 NOAA Tsunami Warning Centers

[Documentación oficial](https://www.tsunami.gov/?page=productRetrieval)

**Datos.** Mensajes de tsunami, regiones afectadas y tiempos previstos cuando están disponibles.

**Cobertura y resolución.** Ámbitos de responsabilidad de los centros emisores. Para cobertura mundial hay que sumar otros centros autorizados.

**Frecuencia e historia.** Por evento, con actualizaciones y cancelaciones.

**Acceso.** Atom y CAP XML publicados. Leer emisor, estado, validez, zona y mensaje de cancelación.

**Límites.** La alerta suele comenzar después de detectarse la fuente. No predice el terremoto. La demora de difusión puede importar en costas cercanas.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D28 NOAA SWPC

[Documentación oficial](https://www.swpc.noaa.gov/content/data-access)

**Datos.** Viento solar, campo magnético, índices geomagnéticos, avisos y productos de modelo.

**Cobertura y resolución.** Entorno espacial de la Tierra. Productos globales y regionales como aurora tienen geometrías distintas.

**Frecuencia e historia.** Observaciones y productos con cadencias propias. Hay JSON recientes y archivos de corta retención.

**Acceso.** Servicios públicos https://services.swpc.noaa.gov/json/ y /products/. Registrar esquema y producto.

**Límites.** Una señal solar no determina exactamente la intensidad terrestre. Las previsiones dependen de trayectoria, orientación magnética y actualización del viento solar.

**Verificación.** Documentación consultada y una petición HTTP pública con JSON válido comprobada. Sin validar el modelo ni el flujo completo.

### D29 NASA JPL CNEOS

[Documentación oficial](https://ssd-api.jpl.nasa.gov/doc/index.php)

**Datos.** Scout para objetos recién observados; Sentry para evaluación de posibles impactos. Probabilidades y órbitas con incertidumbre.

**Cobertura y resolución.** Objetos descubiertos y modelados. No cubre cuerpos que todavía no se detectaron.

**Frecuencia e historia.** Actualiza según nuevas observaciones. Cada solución puede cambiar o eliminar un riesgo anterior.

**Acceso.** JSON en scout.api y sentry.api, con documentación específica. JPL pide una sola petición a la vez y uso moderado con caché.

**Límites.** Acercamiento no significa impacto. Conservar fecha de solución y unidad. La documentación de cada API prevalece sobre supuestos de una clave NASA genérica.

**Verificación.** Documentación consultada y una petición HTTP pública con JSON válido comprobada. Sin validar el modelo ni el flujo completo.

### D30 Copernicus DEM

[Documentación oficial](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM)

**Datos.** Elevación y productos auxiliares del modelo digital de superficie.

**Cobertura y resolución.** Instancias globales GLO 30 y GLO 90 con condiciones del producto. Resolución no es exactitud vertical.

**Frecuencia e historia.** Producto estático por edición, sin cadencia meteorológica.

**Acceso.** Copernicus Data Space y distribuidores documentados. Seleccionar instancia libre y conservar licencia y atribución.

**Límites.** Es DSM, incluye vegetación y construcciones. No sustituye un modelo de terreno urbano o una topografía hidráulica de alta precisión.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D31 GEBCO

[Documentación oficial](https://www.gebco.net/data-products/gridded-bathymetry-data)

**Datos.** Elevación y profundidad oceánica en metros; Type Identifier Grid describe origen del dato.

**Cobertura y resolución.** Malla mundial de 15 segundos de arco en la edición consultada, con detalle real desigual.

**Frecuencia e historia.** Ediciones, sin actualización de nivel del mar en tiempo real.

**Acceso.** Descarga global y subconjuntos desde el portal GEBCO. NetCDF y opciones de distribución documentadas.

**Límites.** Gran parte de la profundidad se estima o interpola. No es suficiente para resolver inundación en cada puerto. Revisar datum y licencia de la edición.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D32 HydroATLAS

[Documentación oficial](https://www.hydrosheds.org/hydroatlas)

**Datos.** Cuencas, tramos de río, lagos y atributos hidroambientales.

**Cobertura y resolución.** Compendio global, con restricciones y calidad propias de la versión base.

**Frecuencia e historia.** Ediciones estáticas. No son caudales ni niveles actuales.

**Acceso.** Descargas BasinATLAS, RiverATLAS y LakeATLAS, con licencia de cada producto.

**Límites.** Un atributo estático no describe cambios recientes de cauce, obras, diques o drenaje urbano.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D33 NASA GRACE asimilado para sequía

[Documentación oficial](https://www.drought.gov/data-maps-tools/groundwater-and-soil-moisture-conditions-grace-data-assimilation)

**Datos.** Percentiles de humedad superficial, zona radicular y agua subterránea derivados mediante asimilación.

**Cobertura y resolución.** Producto global y productos regionales. La malla de salida no equivale a la resolución de observación de GRACE.

**Frecuencia e historia.** Indicadores semanales. Forecasts disponibles deben verificarse por región; no asumir que la perspectiva estadounidense es mundial.

**Acceso.** Enlaces NASA y Drought.gov; colección global GRACEDADM_CLSM025GL_7D documentada. Revisar Earthdata y formato.

**Límites.** El satélite observa cambios integrados de masa. La estimación de agua subterránea depende de un modelo y no mide cada pozo.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D34 RAPID AMOC

[Documentación oficial](https://rapid.ac.uk/data/data-download)

**Datos.** Transporte meridional de la circulación atlántica en la sección observada, expresado habitualmente en Sverdrups.

**Cobertura y resolución.** Red observacional en una sección del Atlántico, no mapa mundial completo de circulación.

**Frecuencia e historia.** Series desde 2004 con versiones y retraso de publicación. Revisar cobertura exacta de la edición.

**Acceso.** Archivos de datos y README con DOI. Respetar atribución al proyecto y condiciones de uso.

**Límites.** Serie relativamente corta para inferir un punto de quiebre secular. No produce una fecha confiable de colapso.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D35 GDACS

[Documentación oficial](https://www.gdacs.org/Documents/2025/GDACS_API_quickstart_v1.pdf)

**Datos.** Eventos, geometrías y alertas de múltiples amenazas.

**Cobertura y resolución.** Sistema global con criterios de inclusión propios y cobertura no exhaustiva.

**Frecuencia e historia.** Actualización por evento. Interpretar fecha de emisión y estado.

**Acceso.** API documentada en https://www.gdacs.org/gdacsapi/swagger/index.html y feeds XML.

**Límites.** Integrar una alerta no equivale a haber predicho el evento. Puede haber estimaciones automáticas y revisiones; no es verdad de referencia completa.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D36 NASA GIBS

[Documentación oficial](https://nasa-gibs.github.io/gibs-api-docs/access-basics/)

**Datos.** Teselas visuales de capas de observación de la Tierra.

**Cobertura y resolución.** Según capa y proyección; catálogo con fechas y resoluciones disponibles.

**Frecuencia e historia.** Cadencia y demora propias de cada visualización.

**Acceso.** WMTS y servicios indicados en https://gibs.earthdata.nasa.gov. Leer capabilities y metadatos.

**Límites.** Los colores de un PNG no reemplazan el archivo científico. Usar para el globo y descargar valores analíticos por la ruta del dataset.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D37 NASA earthaccess y CMR

[Documentación oficial](https://earthaccess.readthedocs.io/en/latest/api/)

**Datos.** Metadatos de colecciones y gránulos y enlaces a archivos científicos.

**Cobertura y resolución.** Catálogo de NASA Earthdata con múltiples proveedores. No todo dato ambiental del mundo está allí.

**Frecuencia e historia.** Disponibilidad según colección. Consultar fechas y versiones.

**Acceso.** earthaccess para autenticación, búsqueda y descarga. CMR permite filtrar short_name, versión, área y tiempo.

**Límites.** CMR es descubrimiento, no predictor ni API universal de series. Revisar el proveedor y las credenciales del dato final.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D38 Qwen documentación oficial

[Documentación oficial](https://github.com/QwenLM/Qwen3/blob/main/README.md)

**Datos.** Modelo de lenguaje para consultas, clasificación de intención y explicaciones apoyadas en resultados.

**Cobertura y resolución.** Sin cobertura científica propia. Depende de las herramientas y documentos que se le entregan.

**Frecuencia e historia.** Versión de modelo fijada por el proyecto; nunca tratar la salida como sensor actualizado.

**Acceso.** Pesos abiertos y despliegue local documentado, por ejemplo mediante Ollama. Revisar licencia del checkpoint.

**Límites.** No valida causalidad ni fabrica probabilidades. La inferencia local evita tarifa de API pero consume hardware, energía y mantenimiento.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D39 Validación temporal con scikit learn

[Documentación oficial](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit)

**Datos.** Particiones ordenadas en el tiempo y separación entre entrenamiento y evaluación.

**Cobertura y resolución.** Método de evaluación, no fuente ambiental.

**Frecuencia e historia.** Depende de la frecuencia del conjunto usado.

**Acceso.** Documentación y biblioteca de código abierto. El diseño también debe separar regiones y eventos correlacionados.

**Límites.** La división cronológica por sí sola no evita fuga por reanálisis, normalización global, ventanas solapadas o selección de casos.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D40 NASA Space Apps Earth System Trend Detective

[Documentación oficial](https://www.spaceappschallenge.org/2026/challenges/earth-system-trend-detective/)

**Datos.** Requisitos del desafío sobre variables ambientales, regiones, series y significancia de tendencias.

**Cobertura y resolución.** Aplicación a variables y regiones elegidas por el equipo.

**Frecuencia e historia.** Edición del desafío consultada para 2026.

**Acceso.** Página pública. El contenido se consultó también mediante indexación; el acceso directo tuvo fallas intermitentes.

**Límites.** La predicción multiamenaza es una ampliación del reto. Debe conservar selección de variables, visualización y análisis estadístico como funciones centrales.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D41 C3S GTSM nivel costero histórico y escenarios

[Documentación oficial](https://cds.climate.copernicus.eu/datasets/sis-water-level-change-timeseries-cmip6)

**Datos.** Series modeladas de mareas, marejada y nivel del mar con forzantes históricas y escenarios.

**Cobertura y resolución.** Ubicaciones costeras globales según producto, no cada metro de costa.

**Frecuencia e historia.** Series históricas y proyecciones del producto. No es un servicio de pronóstico meteorológico en vivo.

**Acceso.** CDS API con cuenta y licencia. Revisar coordenadas, datum, unidades y escenarios.

**Límites.** Una simulación hasta 2050 no predice la marejada de una fecha futura. Sirve para estudiar peligro y escenarios, o como referencia retrospectiva.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D42 USGS señales precursoras volcánicas

[Documentación oficial](https://www.usgs.gov/faqs/how-can-we-tell-when-a-volcano-will-erupt)

**Datos.** Fundamento de sismicidad, gases, deformación y calor como indicadores de actividad.

**Cobertura y resolución.** Marco científico para volcanes vigilados, con comportamiento distinto en cada sistema.

**Frecuencia e historia.** Señales pueden durar semanas o años y terminar sin erupción.

**Acceso.** Explicación pública; las series operativas se buscan en el observatorio correspondiente.

**Límites.** Algunas erupciones ocurren con poca o ninguna advertencia. La presencia de precursores no determina la fecha ni el tamaño de una erupción.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D43 USGS límites de predicción sísmica

[Documentación oficial](https://www.usgs.gov/faqs/can-you-predict-earthquakes)

**Datos.** Diferencia entre predicción determinista y probabilidades de peligro sísmico.

**Cobertura y resolución.** Límite científico general.

**Frecuencia e historia.** No aplica como flujo de datos.

**Acceso.** Explicación pública de USGS.

**Límites.** No existe un método fiable para predecir fecha, lugar y magnitud de un terremoto individual. Alerta temprana detecta un evento ya iniciado.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D44 Estudio de predictibilidad de calor marino

[Documentación oficial](https://repository.library.noaa.gov/view/noaa/45151)

**Datos.** Evaluación retrospectiva de pronósticos estacionales de olas de calor marinas.

**Cobertura y resolución.** Habilidad distinta por región, estación y modo climático.

**Frecuencia e historia.** Analiza décadas de pronósticos retrospectivos; no constituye un sensor.

**Acceso.** Trabajo científico y datos asociados indicados por NOAA.

**Límites.** Resultados favorables en algunas condiciones no garantizan habilidad uniforme para todos los océanos ni todos los horizontes.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D45 Estudio de sequía agrícola argentina

[Documentación oficial](https://hess.copernicus.org/articles/25/2475/2021/)

**Datos.** Precipitación, humedad del suelo y rendimiento de cultivos con sus etapas sensibles.

**Cobertura y resolución.** Región agrícola central argentina; no modelo mundial transferible sin evaluación.

**Frecuencia e historia.** Análisis histórico de varias décadas.

**Acceso.** Artículo de investigación con métodos y fuentes de datos.

**Límites.** Relacionar indicadores con rendimiento requiere calendario y cultivo. No demuestra la precisión de un modelo que aún no construimos.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D46 Met Office sobre AMOC

[Documentación oficial](https://weather.metoffice.gov.uk/learn-about/weather/oceans/amoc)

**Datos.** Funcionamiento, observaciones e incertidumbre de cambios en la circulación atlántica.

**Cobertura y resolución.** Atlántico y efectos climáticos relacionados.

**Frecuencia e historia.** Cambios interanuales y de largo plazo; revisión científica.

**Acceso.** Información científica pública y referencias.

**Límites.** Separar debilitamiento, variabilidad y colapso. No convertir una señal estadística exploratoria en una fecha de colapso.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D47 NOAA IBTrACS

[Documentación oficial](https://www.ncei.noaa.gov/products/international-best-track-archive)

**Datos.** Trayectorias e intensidades históricas de ciclones tropicales de múltiples agencias.

**Cobertura y resolución.** Compilación mundial con calidad y disponibilidad distintas según época y cuenca.

**Frecuencia e historia.** Best tracks históricos y actualizaciones. Revisar versión y estados provisionales.

**Acceso.** Archivos públicos y formatos enlazados en NCEI. Conservar agencia y definición de viento.

**Límites.** No contiene todos los pronósticos emitidos originalmente. No reemplaza un archivo histórico de forecasts para validar anticipación.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

### D48 NOAA CPC ENSO

[Documentación oficial](https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_advisory/ensodisc.shtml)

**Datos.** Diagnóstico y perspectivas probabilísticas de ENSO con explicación del estado oceánico y atmosférico.

**Cobertura y resolución.** Índice climático del Pacífico y efectos potenciales regionales.

**Frecuencia e historia.** Boletines y productos con fechas propias. Archivar cada emisión.

**Acceso.** Página y recursos asociados NOAA. Confirmar archivo numérico y criterio del índice vigente antes de automatizar.

**Límites.** Una probabilidad de fase no es probabilidad de inundación local. Las asociaciones climáticas admiten excepciones y requieren validación regional.

**Verificación.** Documentación pública consultada el 12 de noviembre de 2026. Ingestión pendiente.

## Diseño de implementación

### Arquitectura de implementación

El globo es la capa de presentación. Una arquitectura razonable separa adaptadores de proveedores, almacenamiento científico, transformación, módulos de fenómeno, evaluación y API. El navegador consume teselas y resúmenes preparados; no descarga todos los NetCDF o GRIB mundiales.

Propuesta de stack para evaluar: frontend TypeScript con un motor de globo como Cesium o Three.js; API Python con FastAPI; trabajos programados y cola; PostgreSQL con PostGIS para entidades y geometrías; almacenamiento de objetos para archivos originales y rásteres. Son decisiones de diseño, no requisitos de los proveedores ni un benchmark de rendimiento.

Cada adaptador implementa discover, fetch, decode y normalize. Cada módulo recibe entradas verificadas, declara compute_observation y, solo si corresponde, compute_forecast, y devuelve resultados con procedencia. Un adaptador de mapas visuales no sustituye al adaptador de valores científicos.

Separar fuentes y fenómenos evita duplicar descargas. La precipitación puede alimentar lluvia extrema, sequía, agricultura y deslizamientos. Una misma fecha de corrida se almacena una vez y los módulos referencian su identificador.

Guardar datos originales inmutables con checksum y versión. Mantener un registro de transformaciones y archivos resultantes. Las revisiones del proveedor se agregan como versiones; no deben borrar la evidencia usada en un pronóstico anterior.

### Modelo común de datos

Para cada entrada guardar source_id, collection_id, product_version, variable, units, geometry o grid_id, observation_start, observation_end, issued_at cuando aplique, available_at, ingested_at, quality_flags, license_url y original_asset. El tiempo de observación puede ser un intervalo; no inventar una hora puntual para un compuesto.

Para cada salida guardar phenomenon_id, output_type, model_id, model_version, run_id, issued_at, valid_from, valid_to, spatial_support, source_asset_ids, result_value, result_unit, probability, probability_definition, uncertainty y validation_reference. Si no hay probabilidad calibrada, probability queda null.

Usar además coverage_status, data_freshness y operational_state. Estados propuestos: specified, source_connected, historical_ready, experimental_forecast y validated_for_scope. Son estados de desarrollo del proyecto, no niveles de peligro. Todos los módulos entregados están specified.

Distinguir tres tiempos esenciales: cuándo ocurrió la observación, cuándo se publicó y cuándo la aplicación la obtuvo. Para un forecast, sumar cuándo se inicializó y para cuándo es válido. Estos campos hacen posible una prueba histórica honesta.

Conservar unidades nativas y convertir mediante funciones explícitas probadas con metadatos. Reproyectar y remuestrear según tipo de variable. No usar interpolación visual como evidencia de mayor resolución. Los acumulados de agua exigen conservar totales y duración.

### Acceso a los datos y costos

No existe una API que entregue todos los insumos y todos los pronósticos mundiales. NASA Earthdata ayuda a descubrir y descargar muchas colecciones; Copernicus tiene CDS, ADS, Marine y Data Space con cuentas y protocolos distintos; NOAA, USGS, Smithsonian y FAO publican servicios independientes.

Los datos abiertos reducen la compra de licencias, pero no hacen gratuita toda la app. Hay costos de cómputo, almacenamiento, transferencia, caché, mantenimiento y eventualmente proveedores locales. Verificar términos de cada producto y servicio, conservar atribución y no exponer tokens en el navegador.

Como orden de magnitud ilustrativo, una malla de 0,25 grados con 1440 por 721 posiciones contiene 1.038.240 celdas. Un campo float32 ocupa unos 4,15 MB decimales sin comprimir. Diez variables por cuarenta plazos son unos 1,66 GB por corrida; cincuenta miembros los elevan a unos 83 GB. No incluye metadatos ni otros campos y no representa una factura ni el tamaño real de GRIB comprimido.

Para controlar volumen, procesar regiones o variables prioritarias, recortar por área y tiempo, almacenar resúmenes y teselas, y mantener resolución de vista adaptable. El modo mundial puede usar una malla más gruesa; el detalle se solicita al acercarse.

Propuesta de frecuencia de consulta: según la publicación de cada fuente y con caché. No sondear cada segundo productos diarios. En JPL CNEOS respetar una sola petición simultánea. Implementar reintentos moderados, backoff, límite por proveedor y registro de fallas.

### Prueba histórica y validación

Definir antes del ajuste qué evento se intenta anticipar, unidad espacial, ventana, antelación y umbral. En sequía podría ser humedad de suelo anormalmente baja durante el mes siguiente. Esa definición debe tener versión para que un cambio posterior no mejore artificialmente los resultados.

Separar años antiguos para ajuste, años intermedios para selección de método y períodos posteriores intactos para evaluación. Agregar separación espacial cuando se afirme capacidad de transferencia. Si varias filas pertenecen al mismo desastre o a ventanas solapadas, mantenerlas en la misma partición.

Ajustar normalización, climatología, umbrales y búsqueda de análogos solo con el entrenamiento correspondiente. Un antecedente solo es utilizable si su desenlace completo se conocía antes de la fecha simulada. Estación, región y cambio climático pueden alterar comparabilidad.

Para pruebas que pretendan simular tiempo real, filtrar por available_at. IMERG Final, reanálisis revisados, best tracks de ciclones y series reconstruidas no estaban necesariamente disponibles en esa fecha. Si no se conserva el archivo emitido entonces, llamar al resultado experimento retrospectivo con datos reconstruidos y documentar la limitación.

Comparar con climatología, persistencia y el producto científico existente cuando aplique. Un porcentaje de acierto alto puede resultar de acertar muchos días sin evento. Publicar también eventos omitidos, falsas alarmas, anticipación útil y desempeño por región y época.

Para probabilidades, medir calibración, Brier y capacidad de distinguir eventos con métricas apropiadas a su rareza. Para cantidades continuas, MAE y sesgo; para trayectorias o llegadas, error espacial y temporal. La incertidumbre de las métricas depende del número de eventos independientes.

Los eventos raros requieren especial cuidado. Un solo caso famoso sirve como demostración, no como prueba general. Combinar física, experiencia del dominio y bases históricas, evaluar episodios de señales sin desenlace y comunicar cuando hay evidencia insuficiente. Recurrencia de cien años no significa que el evento ocurra puntualmente cada cien años.

La IA de lenguaje no es el evaluador del desenlace. Puede conocer el evento histórico por entrenamiento. La prueba usa código, entradas temporalmente restringidas, resultados guardados antes de revelar el futuro y métricas reproducibles.

### Uso de IA y modelos de lenguaje

Qwen puede ser una capa conversacional que traduzca preguntas a consultas, encuentre fichas y explique resultados estructurados. Un modelo local de pesos abiertos evita tarifa por token de un proveedor, pero requiere equipo y recursos. La elección de checkpoint y tamaño se hace con un benchmark propio de latencia y memoria.

El modelo recibe datos con IDs, unidades, fecha, alcance e incertidumbre. La respuesta debe citar esas entradas y poder abstenerse cuando faltan. Para cálculos y pronósticos debe invocar módulos deterministas o científicos aprobados para su alcance; no generar porcentajes sin modelo.

Un sistema de recuperación sobre este catálogo permite responder de dónde sale una señal y qué falta para predecirla. Separar documentación estática, datos vivos y experimentos. Un texto de noticias puede ayudar a investigar un evento, pero no es una medición numérica ni prueba de causalidad.

Vibecodear es viable para construir adaptadores, UI y orquestación. Para hacerlo revisable, implementar un módulo por vez contra un contrato y una muestra real. Que el código compile no demuestra capacidad científica. Los modelos propios necesitan evaluación independiente del generador de código.

### Presentación del globo y señales

Usar capas de valores continuos para variables ambientales y entidades seleccionables para eventos, cuencas, arrecifes o volcanes. Al alejarse, agrupar símbolos por área; al acercarse, revelar detalle. Un globo lleno de información puede seguir siendo legible si distingue magnitud, tipo de salida y estado del dato.

Cada ficha en el globo debe mostrar observación o forecast, intervalo válido, actualización, fuente, explicación del indicador, resolución, límite y evidencia de evaluación. La leyenda de color necesita una definición por fenómeno. No sumar índices incompatibles en un puntaje global arbitrario.

El control temporal ofrece pasado observado, última información y futuro estimado. La línea que separa observación y forecast debe ser visible. El modo de simulación histórica carga solo activos disponibles en la fecha elegida y registra el resultado antes de mostrar el desenlace.

Representar conexiones como relaciones documentadas o hipótesis identificadas. El Niño puede modificar probabilidades regionales, pero no se dibuja una cadena causal garantizada desde un índice hasta una inundación específica. Las alertas importadas conservan emisor, validez y cancelación.

### Secuencia de desarrollo propuesta

Primera entrega: globo mundial, catálogo, fuentes y estado de datos, selección de región, series y tendencias. Conectar un conjunto pequeño de fuentes NASA y una fuente de pronóstico. Mantener accesibles las fichas del catálogo completo con su estado de implementación.

Primer conjunto de módulos candidatos: lluvia extrema F01, calor F02, sequía F11 como experimento, crecidas fluviales F12, peligro de incendio F15 y estrés térmico de corales F19. Comparten insumos disponibles y muestran diferencias entre observación, peligro y forecast. Su selección es una recomendación de producto, no certificación de precisión.

Segunda entrega: completar credenciales, muestras, normalización y procedencia. Incorporar clima oceánico y atmósfera cuando el acceso esté comprobado. Para cada módulo nuevo publicar cobertura y evaluación propia o documentación del proveedor.

Tercera entrega: añadir fenómenos regionales con proveedores locales y asesoramiento del dominio. Volcanes, inundación urbana, lagos glaciares, toxinas y oxígeno requieren resolver insumos específicos. La AMOC permanece en exploración científica.

Criterio para habilitar un forecast propio: datos disponibles en el momento correcto, objetivo definido, modelo versionado, pruebas fuera de muestra, comparación base, evidencia de habilidad para el alcance declarado y manejo de datos faltantes. Integrar un forecast externo exige respetar su alcance y medir fidelidad y demora de ingestión.

No se fija un plazo universal de entrega ni presupuesto sin medir volumen, cuota, equipo y número de módulos. La jam puede demostrar un flujo completo y verificable; cubrir operativamente las 31 familias es una evolución de producto.

## Comprobaciones realizadas

Las tres comprobaciones siguientes se ejecutaron durante este trabajo con peticiones públicas pequeñas. Demuestran acceso puntual y sintaxis JSON válida. No prueban continuidad de servicio, exactitud científica, latencia operativa ni un pipeline completo.

USGS: consulta acotada de un evento histórico, HTTP 200 y objeto GeoJSON con type, metadata y features.

NOAA SWPC: resumen público de velocidad del viento solar, HTTP 200 y JSON válido. Es un feed reciente pequeño, no un archivo de forecasts históricos.

NASA JPL CNEOS: consulta Sentry de resumen, HTTP 200 y JSON válido con data, signature y count. La petición se realizó secuencialmente.

No se iniciaron sesiones Earthdata, CDS, ADS o Copernicus Marine ni se descargaron colecciones mundiales. Los accesos protegidos y los servicios de exportación específicos deben comprobarse en la fase de conectores. Este documento no declara validada ninguna predicción propia.

### Consultas públicas comprobadas

- USGS: [consulta utilizada](https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2024-09-01&endtime=2024-09-02&minmagnitude=6&limit=1). Estado 200.

- SWPC: [consulta utilizada](https://services.swpc.noaa.gov/products/summary/solar-wind-speed.json). Estado 200.

- CNEOS: [consulta utilizada](https://ssd-api.jpl.nasa.gov/sentry.api). Estado 200.

## Pendientes para convertir la especificación en un sistema operativo

1. Abrir las cuentas necesarias y aceptar términos de los productos seleccionados.
2. Descargar una muestra por colección y fijar versión, unidades, máscara y fechas.
3. Resolver exportación automatizada de los productos que solo se verificaron como portal o boletín.
4. Incorporar proveedores locales donde la matriz marca faltantes.
5. Definir objetivos y evaluar modelos propios con datos temporalmente válidos.
6. Medir recursos, retención, frecuencia de procesamiento y costo del despliegue.
7. Mantener historial de fuentes y condiciones para actualizar este catálogo.

El archivo JSON adjunto expresa el mismo catálogo con identificadores estables. Es una especificación inicial para el código y no contiene claves, pesos de modelo ni predicciones calculadas.
