# Matriz de integraciones reales

Generada desde los 48 IDs originales con `python -m earth_echo.tools.integration_report`. Estado y evidencia son del alcance efectivamente descargado, no del proveedor entero. Accesos: [accesos.md](accesos.md).

| ID | Fuente | Clasificación | Estado / evidencia | Bloqueo o siguiente paso |
| --- | --- | --- | --- | --- |
| D01 | NASA GPM IMERG | Fuente de observaciones | pending | Earthdata: EARTHDATA_USERNAME, EARTHDATA_PASSWORD; falta descarga autenticada |
| D02 | NASA SMAP SPL3SMP E | Fuente de observaciones | pending | Earthdata: EARTHDATA_USERNAME, EARTHDATA_PASSWORD; falta descarga autenticada |
| D03 | NASA GLDAS | Pronóstico o producto científico existente | pending | Earthdata: EARTHDATA_USERNAME, EARTHDATA_PASSWORD; falta descarga autenticada |
| D04 | NASA MODIS MOD13Q1 | Fuente de observaciones | /v1/products/d04-evi-amazonia, /v1/products/d04-evi-pampa, /v1/products/d04-ndvi-amazonia, /v1/products/d04-ndvi-pampa | Índice de verdor; no confirma sequía ni rendimiento agrícola. |
| D05 | NASA MODIS MOD11A2 | Fuente de observaciones | /v1/products/d05-lst-day-amazonia, /v1/products/d05-lst-day-pampa, /v1/products/d05-lst-night-amazonia, /v1/products/d05-lst-night-pampa | Temperatura de superficie de cielo despejado, diurna/nocturna; no es temperatura del aire ni ola de calor. |
| D06 | NASA FIRMS | Fuente de observaciones | pending | Consultar producto real; descubrimiento no cuenta como integración |
| D07 | ECMWF Open Data | Pronóstico o producto científico existente | /v1/products/d07-ifs-10u-24h, /v1/products/d07-ifs-10v-24h, /v1/products/d07-ifs-2d-24h, /v1/products/d07-ifs-2t-24h, /v1/products/d07-ifs-tp-24h | Pronóstico determinista externo, un plazo +24 h. Sin probabilidades ni detector de ola de calor, tormenta o inundación.  ; Pronóstico determinista externo, un plazo +24 h. Sin probabilidades ni detector de ola de calor, tormenta o inundación. Acumulado desde la inicialización, convertido m→mm; no es tasa ni profundidad de inundación. |
| D08 | ERA5 histórico | Dataset histórico | pending | CDSAPI_KEY + licencia manual ERA5 |
| D09 | C3S pronóstico estacional | Pronóstico o producto científico existente | pending | CDSAPI_KEY + licencia manual estacional |
| D10 | Copernicus GloFAS | Pronóstico o producto científico existente | pending | EWDSAPI_KEY + licencia y colección GloFAS vigente |
| D11 | Copernicus GWIS | Pronóstico o producto científico existente | pending | Exportación numérica GWIS/CEMS y licencia; no alcanza WMS |
| D12 | CAMS composición atmosférica | Pronóstico o producto científico existente | pending | ADSAPI_KEY + licencia CAMS |
| D13 | NOAA OISST | Fuente de observaciones; Dataset histórico | /v1/products/d13-oisst-global | SST analizada e interpolada, preliminar cuando así lo identifica NOAA. No es temperatura del aire, un evento de calor marino ni diagnóstico ENSO. |
| D14 | Copernicus Marine física oceánica | Pronóstico o producto científico existente | pending | COPERNICUSMARINE_SERVICE_USERNAME, COPERNICUSMARINE_SERVICE_PASSWORD |
| D15 | NOAA Coral Reef Watch | Fuente de observaciones; Pronóstico o producto científico existente | /v1/products/d15-dhw-global, /v1/products/d15-hotspot-global, /v1/products/d15-sst-global | HotSpot: diferencia positiva de SST respecto de Maximum Monthly Mean; DHW: acumulación del estrés ≥1 °C durante 12 semanas. Indicadores importados de NOAA, sin confirmar blanqueamiento biológico ni pronóstico. ; SST analizada: no es temperatura del aire ni diagnóstico de ola de calor marina. |
| D16 | NOAA pronóstico de olas de calor marinas | Pronóstico o producto científico existente | /v1/products/d16-mhw-month-1, /v1/products/d16-mhw-month-2, /v1/products/d16-mhw-month-3 | Producto externo experimental de investigación. Probabilidad mensual de SST sobre umbral estacional percentil 90 de 1991–2020, con tendencia retenida; lead=1.5 meses (centro del mes). Modelos: CanESM5, GEM5.2-NEMO, GFDL-SPEAR-regridded, NASA-GEOSS2S, COLA-RSMAS-CCSM4, COLA-RSMAS-CESM1, NCEP-CFSv2. No representa un evento diario Hobday ni una probabilidad de daño biológico. 6067657 bytes retenidos en 47 rangos de un archivo de 268867017; no se descargó toda la historia. ; Producto externo experimental de investigación. Probabilidad mensual de SST sobre umbral estacional percentil 90 de 1991–2020, con tendencia retenida; lead=2.5 meses (centro del mes). Modelos: CanESM5, GEM5.2-NEMO, GFDL-SPEAR-regridded, NASA-GEOSS2S, COLA-RSMAS-CCSM4, COLA-RSMAS-CESM1, NCEP-CFSv2. No representa un evento diario Hobday ni una probabilidad de daño biológico. 6067657 bytes retenidos en 47 rangos de un archivo de 268867017; no se descargó toda la historia. ; Producto externo experimental de investigación. Probabilidad mensual de SST sobre umbral estacional percentil 90 de 1991–2020, con tendencia retenida; lead=3.5 meses (centro del mes). Modelos: CanESM5, GEM5.2-NEMO, GFDL-SPEAR-regridded, NASA-GEOSS2S, COLA-RSMAS-CCSM4, COLA-RSMAS-CESM1, NCEP-CFSv2. No representa un evento diario Hobday ni una probabilidad de daño biológico. 6067657 bytes retenidos en 47 rangos de un archivo de 268867017; no se descargó toda la historia. |
| D17 | NASA Ocean Color | Fuente de observaciones | pending | Earthdata: EARTHDATA_USERNAME, EARTHDATA_PASSWORD; falta descarga autenticada |
| D18 | NOAA pronósticos ecológicos regionales | Pronóstico o producto científico existente | pending | Seleccionar servicio regional, variable/especie y archivo numérico |
| D19 | FAO Locust Watch y Locust Hub | Fuente de observaciones | pending | Resolver capa FAO exportable y términos; Schistocerca gregaria solamente |
| D20 | FAO ASIS | Pronóstico o producto científico existente | pending | Resolver exportación numérica/máscara agrícola; imagen no acredita valor |
| D21 | USGS ComCat y FDSN | Fuente de observaciones | /v1/layers/d21-events | Consultar producto real; descubrimiento no cuenta como integración |
| D22 | USGS pronóstico de réplicas | Pronóstico o producto científico existente | /v1/products/d22-oaf-recent | Probabilidades importadas, no hora/lugar garantizados de la próxima réplica. Un solo evento reciente publicado; el producto no existe para todos los sismos. Modelo del proveedor: Reasenberg-Jones (1989, 1994) aftershock model (Bayesian Combination). |
| D23 | Smithsonian Global Volcanism Program | Dataset histórico; Geometría o contexto estático | /v1/products/d23-holocene-inventory | Contexto estático, no una red de sensores ni un pronóstico de erupción. Elevación y año de última erupción conservan la definición del inventario. |
| D24 | NASA LHASA | Pronóstico o producto científico existente | /v1/products/d24-lhasa-bc | Nowcast/modelo importado, no un deslizamiento observado ni una alerta geotécnica de cada ladera. La fecha es la referencia del archivo NRT, no hora de un evento. Se transfirieron 1048576 bytes en 8 rangos de un GeoTIFF de 146876470 bytes; se conservan esos rangos, no el archivo mundial completo. |
| D25 | Copernicus Data Space | Servicio de descubrimiento o visualización | pending | Catálogo público; escena científica y procesamiento aún pendientes |
| D26 | Randolph Glacier Inventory | Geometría o contexto estático | pending | Elegir edición y subconjunto RGI con época de geometría |
| D27 | NOAA Tsunami Warning Centers | Pronóstico o producto científico existente | /v1/products/d27-tsunami-messages | Mensajes oficiales con emisor, estado, actualización/cancelación y expiración. Un mensaje informativo no confirma tsunami. No se infiere llegada ni área afectada desde el epicentro. Geometrías CAP originales preservadas en cada mensaje. |
| D28 | NOAA SWPC | Fuente de observaciones; Pronóstico o producto científico existente | /v1/layers/d28-kp, /v1/forecasts/d28-kp | Consultar producto real; descubrimiento no cuenta como integración |
| D29 | NASA JPL CNEOS | Pronóstico o producto científico existente | /v1/products/d29-sentry | No incluye objetos no descubiertos. Un acercamiento no es un impacto; las evaluaciones pueden retirarse o cambiar. No se inventa una fecha o lugar de desastre. |
| D30 | Copernicus DEM | Geometría o contexto estático | /v1/products/d30-dem-pampa | Contexto estático de superficie; alturas ortométricas EGM2008 según Product Handbook 5.0 de Copernicus DEM (https://dataspace.copernicus.eu/sites/default/files/media/files/2024-06/geo1988-copernicusdem-spe-002_producthandbook_i5.0.pdf). Sin fecha de adquisición por píxel en este COG. No es terreno desnudo, altura elipsoidal, nivel del agua ni modelo hidráulico. Distribuidor identifica colección 2021; la edición DGED no está codificada en la tesela: se identifica archivo por ETag y SHA-256. |
| D31 | GEBCO | Geometría o contexto estático | pending | Subconjunto GEBCO y Type Identifier Grid con datum |
| D32 | HydroATLAS | Geometría o contexto estático | pending | Subconjunto y licencia HydroATLAS; no son caudales |
| D33 | NASA GRACE asimilado para sequía | Pronóstico o producto científico existente | pending | Earthdata: EARTHDATA_USERNAME, EARTHDATA_PASSWORD; falta descarga autenticada |
| D34 | RAPID AMOC | Fuente de observaciones; Dataset histórico | pending | Archivo RAPID y README/DOI pendientes |
| D35 | GDACS | Pronóstico o producto científico existente | pending | Resolver productos, geometrias, cancelación y validez |
| D36 | NASA GIBS | Servicio de descubrimiento o visualización | pending | Consultar producto real; descubrimiento no cuenta como integración |
| D37 | NASA earthaccess y CMR | Servicio de descubrimiento o visualización | pending | Consultar producto real; descubrimiento no cuenta como integración |
| D38 | Qwen documentación oficial | Documentación, método o referencia científica | reference_only | Consultar producto real; descubrimiento no cuenta como integración |
| D39 | Validación temporal con scikit learn | Documentación, método o referencia científica | reference_only | Consultar producto real; descubrimiento no cuenta como integración |
| D40 | NASA Space Apps Earth System Trend Detective | Documentación, método o referencia científica | reference_only | Consultar producto real; descubrimiento no cuenta como integración |
| D41 | C3S GTSM nivel costero histórico y escenarios | Dataset histórico | pending | CDSAPI_KEY + licencia GTSM |
| D42 | USGS señales precursoras volcánicas | Documentación, método o referencia científica | reference_only | Consultar producto real; descubrimiento no cuenta como integración |
| D43 | USGS límites de predicción sísmica | Documentación, método o referencia científica | reference_only | Consultar producto real; descubrimiento no cuenta como integración |
| D44 | Estudio de predictibilidad de calor marino | Documentación, método o referencia científica | reference_only | Consultar producto real; descubrimiento no cuenta como integración |
| D45 | Estudio de sequía agrícola argentina | Documentación, método o referencia científica | reference_only | Consultar producto real; descubrimiento no cuenta como integración |
| D46 | Met Office sobre AMOC | Documentación, método o referencia científica | reference_only | Consultar producto real; descubrimiento no cuenta como integración |
| D47 | NOAA IBTrACS | Dataset histórico | /v1/products/d47-cyclone-tracks | Historia compilada, incluida posición provisional. No es trayectoria futura ni archivo de pronósticos emitidos. Viento WMO en nudos sin armonizar promedios 1/3/10 minutos; cada registro conserva agencia, IFLAG, tipo y presión mb. Faltantes nativos siguen null. Se dibujan centros publicados, con cortes de visualización al antimeridiano; sin inventar observaciones en los bordes. |
| D48 | NOAA CPC ENSO | Pronóstico o producto científico existente | /v1/products/d48-oni-history | Historia ONI, medias móviles de tres meses y climatología definida por CPC. No se convierte automáticamente en fase ENSO vigente, perspectiva probabilística ni lluvia local. El diagnóstico operativo puede usar otro índice como RONI. |

## Capacidades de los 31 fenómenos

Observación puede ser parcial; un dato de contexto no habilita un detector. «specified», «blocked» o «research» no son capacidades operativas. «partial» describe exactamente el alcance indicado en la API.

| ID | Fenómeno | Observación | Indicador | Tendencia | Pronóstico externo | Modelo propio |
| --- | --- | --- | --- | --- | --- | --- |
| F01 | Lluvias extremas | blocked | specified | specified | partial | specified |
| F02 | Olas de calor | partial | specified | specified | partial | specified |
| F03 | Olas de frío y heladas | specified | specified | specified | partial | specified |
| F04 | Tormentas severas y granizo | partial | specified | specified | specified | specified |
| F05 | Tornados | specified | specified | specified | specified | specified |
| F06 | Ciclones tropicales | specified | specified | specified | specified | specified |
| F07 | Marejadas e inundación costera | specified | specified | specified | specified | specified |
| F08 | Nieve y tormentas de hielo | specified | specified | specified | specified | specified |
| F09 | Tormentas de polvo | specified | specified | specified | specified | specified |
| F10 | Contaminación y transporte de humo | specified | specified | specified | specified | specified |
| F11 | Sequías | blocked | specified | specified | specified | specified |
| F12 | Crecidas fluviales | blocked | specified | specified | specified | specified |
| F13 | Inundaciones repentinas | specified | specified | specified | specified | specified |
| F14 | Escasez de agua | specified | specified | specified | specified | specified |
| F15 | Peligro de incendios | specified | specified | specified | specified | specified |
| F16 | Estrés agrícola | partial | specified | specified | specified | specified |
| F17 | El Niño y La Niña | specified | partial | specified | specified | specified |
| F18 | Olas de calor marinas | partial | specified | specified | partial | specified |
| F19 | Estrés térmico de corales | partial | partial | partial | specified | experimental |
| F20 | Floraciones de algas nocivas | specified | specified | specified | specified | specified |
| F21 | Hipoxia acuática | specified | specified | specified | specified | specified |
| F22 | Condiciones favorables para Vibrio | specified | specified | specified | specified | specified |
| F23 | Langosta del desierto | specified | specified | specified | specified | specified |
| F24 | Actividad volcánica y erupciones | partial | specified | specified | specified | specified |
| F25 | Deslizamientos por lluvia | specified | partial | specified | specified | specified |
| F26 | Desbordes de lagos glaciares | specified | specified | specified | specified | specified |
| F27 | Tsunamis | partial | specified | specified | specified | specified |
| F28 | Réplicas sísmicas | partial | specified | specified | partial | specified |
| F29 | Tormentas geomagnéticas | connected | specified | specified | partial | specified |
| F30 | Impactos de asteroides conocidos | specified | specified | specified | partial | specified |
| F31 | Cambios en la AMOC | research | specified | research | research | specified |
