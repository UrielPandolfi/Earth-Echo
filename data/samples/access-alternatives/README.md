# Alternativas públicas examinadas

Metadatos JSON originales descargados de NOAA AOML el 14/11/2026:

- `vibrioriskforecast.json`: [ERDDAP](https://cwcgom.aoml.noaa.gov/erddap/info/vibrioriskforecast/index.html), producto experimental con unidad `Risk Level`, `variable_info=To be Completed`, sin definición/especie suficiente para interpretarlo como la capacidad regional D18 del catálogo. No se convirtió en probabilidad ni se integró como feed.
- `vibriorisk.json`: [ERDDAP](https://cwcgom.aoml.noaa.gov/erddap/info/vibriorisk/index.html), análisis experimental con las mismas carencias semánticas.
- `miamiModisAquaChlor.json`: [ERDDAP](https://cwcgom.aoml.noaa.gov/erddap/info/miamiModisAquaChlor/index.html), archivo regional termina en octubre 2022, sin versión de procesamiento suficiente; no prueba una conexión NASA Ocean Color reciente.

Esto es evidencia de descubrimiento y de bloqueos, no productos integrados ni observaciones adicionales. La ruta GDS GLDAS probada devolvió 410; la colección NASA PFEG R2022 NRT no respondió a conexión desde el equipo. No se extrapola ese resultado a todos los servicios del proveedor ni se inventan requisitos de cuenta para estas URL públicas.
