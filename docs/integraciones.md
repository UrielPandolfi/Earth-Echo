# Matriz de integraciones reales

Generada desde los 48 IDs originales con `python -m earth_echo.tools.integration_report`. Estado y evidencia son del alcance efectivamente descargado, no del proveedor entero. Accesos: [accesos.md](accesos.md).

| ID | Fuente | Clasificación | Estado / evidencia | Bloqueo o siguiente paso |
| --- | --- | --- | --- | --- |
| D01 | NASA GPM IMERG | Fuente de observaciones | pending | Earthdata: EARTHDATA_USERNAME, EARTHDATA_PASSWORD; falta descarga autenticada |
| D02 | NASA SMAP SPL3SMP E | Fuente de observaciones | pending | Earthdata: EARTHDATA_USERNAME, EARTHDATA_PASSWORD; falta descarga autenticada |
| D03 | NASA GLDAS | Pronóstico o producto científico existente | pending | Earthdata: EARTHDATA_USERNAME, EARTHDATA_PASSWORD; falta descarga autenticada |
| D04 | NASA MODIS MOD13Q1 | Fuente de observaciones | pending | Consultar producto real; descubrimiento no cuenta como integración |
| D05 | NASA MODIS MOD11A2 | Fuente de observaciones | pending | Consultar producto real; descubrimiento no cuenta como integración |
| D06 | NASA FIRMS | Fuente de observaciones | pending | Consultar producto real; descubrimiento no cuenta como integración |
| D07 | ECMWF Open Data | Pronóstico o producto científico existente | pending | Consultar producto real; descubrimiento no cuenta como integración |
| D08 | ERA5 histórico | Dataset histórico | pending | CDSAPI_KEY + licencia manual ERA5 |
| D09 | C3S pronóstico estacional | Pronóstico o producto científico existente | pending | CDSAPI_KEY + licencia manual estacional |
| D10 | Copernicus GloFAS | Pronóstico o producto científico existente | pending | EWDSAPI_KEY + licencia y colección GloFAS vigente |
| D11 | Copernicus GWIS | Pronóstico o producto científico existente | pending | Exportación numérica GWIS/CEMS y licencia; no alcanza WMS |
| D12 | CAMS composición atmosférica | Pronóstico o producto científico existente | pending | ADSAPI_KEY + licencia CAMS |
| D13 | NOAA OISST | Fuente de observaciones; Dataset histórico | pending | Consultar producto real; descubrimiento no cuenta como integración |
| D14 | Copernicus Marine física oceánica | Pronóstico o producto científico existente | pending | COPERNICUSMARINE_SERVICE_USERNAME, COPERNICUSMARINE_SERVICE_PASSWORD |
| D15 | NOAA Coral Reef Watch | Fuente de observaciones; Pronóstico o producto científico existente | /v1/products/d15-dhw-global, /v1/products/d15-hotspot-global, /v1/products/d15-sst-global | Consultar producto real; descubrimiento no cuenta como integración |
| D16 | NOAA pronóstico de olas de calor marinas | Pronóstico o producto científico existente | pending | Resolver archivo numérico de perspectivas, sin inferir datos desde imagen |
| D17 | NASA Ocean Color | Fuente de observaciones | pending | Earthdata: EARTHDATA_USERNAME, EARTHDATA_PASSWORD; falta descarga autenticada |
| D18 | NOAA pronósticos ecológicos regionales | Pronóstico o producto científico existente | pending | Seleccionar servicio regional, variable/especie y archivo numérico |
| D19 | FAO Locust Watch y Locust Hub | Fuente de observaciones | pending | Resolver capa FAO exportable y términos; Schistocerca gregaria solamente |
| D20 | FAO ASIS | Pronóstico o producto científico existente | pending | Resolver exportación numérica/máscara agrícola; imagen no acredita valor |
| D21 | USGS ComCat y FDSN | Fuente de observaciones | /v1/layers/d21-events | Consultar producto real; descubrimiento no cuenta como integración |
| D22 | USGS pronóstico de réplicas | Pronóstico o producto científico existente | pending | Consultar producto real; descubrimiento no cuenta como integración |
| D23 | Smithsonian Global Volcanism Program | Dataset histórico; Geometría o contexto estático | pending | WFS respondió HTTP 403; inventario no es precursor |
| D24 | NASA LHASA | Pronóstico o producto científico existente | pending | Resolver versión y archivo numérico LHASA |
| D25 | Copernicus Data Space | Servicio de descubrimiento o visualización | pending | Catálogo público; escena científica y procesamiento aún pendientes |
| D26 | Randolph Glacier Inventory | Geometría o contexto estático | pending | Elegir edición y subconjunto RGI con época de geometría |
| D27 | NOAA Tsunami Warning Centers | Pronóstico o producto científico existente | pending | Consultar producto real; descubrimiento no cuenta como integración |
| D28 | NOAA SWPC | Fuente de observaciones; Pronóstico o producto científico existente | /v1/layers/d28-kp, /v1/forecasts/d28-kp | Consultar producto real; descubrimiento no cuenta como integración |
| D29 | NASA JPL CNEOS | Pronóstico o producto científico existente | pending | Consultar producto real; descubrimiento no cuenta como integración |
| D30 | Copernicus DEM | Geometría o contexto estático | pending | Seleccionar mosaico DSM/datum/licencia |
| D31 | GEBCO | Geometría o contexto estático | pending | Subconjunto GEBCO y Type Identifier Grid con datum |
| D32 | HydroATLAS | Geometría o contexto estático | pending | Subconjunto y licencia HydroATLAS; no son caudales |
| D33 | NASA GRACE asimilado para sequía | Pronóstico o producto científico existente | pending | Earthdata: EARTHDATA_USERNAME, EARTHDATA_PASSWORD; falta descarga autenticada |
| D34 | RAPID AMOC | Fuente de observaciones; Dataset histórico | pending | Archivo RAPID y README/DOI pendientes |
| D35 | GDACS |  | pending | Resolver productos, geometrias, cancelación y validez |
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
| D47 | NOAA IBTrACS | Dataset histórico | pending | Best tracks históricos, versión y agencia pendientes |
| D48 | NOAA CPC ENSO | Pronóstico o producto científico existente | pending | Consultar producto real; descubrimiento no cuenta como integración |
