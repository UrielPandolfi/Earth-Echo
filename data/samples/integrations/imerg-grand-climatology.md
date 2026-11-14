# Muestra científica IMERG Final V07B

Los dos ZIP son descargas originales exactas de los enlaces NetCDF/GeoTIFF de https://gpm.nasa.gov/data/imerg/precipitation-climatology el 14/11/2026. `imerg-grand-climatology-nc4.zip` corresponde a `IMERG-Final.CLIM.200006-202305.V07B.nc4.zip` (17.903.213 bytes); `imerg-grand-climatology-tif.zip`, al ZIP TIFF homónimo (26.383.365 bytes). Se retiene una sola climatología, no la colección diaria de varios GB. Dominio público declarado por los autores en la documentación enlazada.

Referencia junio 2000–mayo 2023; precipitación media anual, mm/año. No es observación reciente ni forecast. Todos los 6.480.000 nodos y el fill −9999,9 coinciden exactamente entre h5py/NetCDF y rasterio/TIFF, tras transponer/invertir ejes. Los ceros reales se conservan. 24.418 ausentes nativos; vista 1° con 360 ausentes. Muestra nativa −35,55°,−61,55°: 1.020,9791870117188 mm/año.

El WorldFile auxiliar original contiene `***` como paso vertical: se conserva sin corregir y no se utiliza. La georreferenciación interna del TIFF sí coincide con los ejes CF; la ausencia TIFF se toma del fill NetCDF/documentación, no de un tag inexistente. El título NetCDF contiene un error literal `runname[run]`; fuente/versión/período identifican el producto y el manifiesto conserva el texto completo. Creación original 17/01/2024 12:49:44 UTC; descargar en 2026 no cambia la fecha científica.

Pruebas: `python -m pytest services/api/tests/test_imerg_climatology.py`. Mutaciones deliberadas de pruebas (unidad o celda) deben rechazarse; nunca se publican como datos reales. La repetición no duplica revisiones y la falla de red conserva el producto válido.
