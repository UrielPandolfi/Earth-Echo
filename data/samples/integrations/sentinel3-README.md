# Muestra científica original Sentinel-3A

NetCDF ERDDAP original, no imagen: chlor_a, 10/11/2026 12:00 UTC (Time Baseline del agregado L3), superficie 0 m, stride 24 de centros nativos 0,0375°. Campo visual 400×200 de 0,9°; 7.132 celdas finitas y 72.868 ausentes. OC4Me Experimental, unidades mg m^-3; rango científico 0,01–315,09097. La escala de color del proveedor termina en 64,7 y no se usó para recortar datos.

Fuente original Copernicus Sentinel-3A OLCI, redistribución/modificación NOAA CoastWatch: https://coastwatch.noaa.gov/erddap/info/noaacwS3AOLCIchlaDaily/index.html. Atribución obligatoria: **Contains modified Copernicus Sentinel data.** No es NASA OceanColor, escena Sentinel-2, toxicidad, hipoxia o confirmación de HAB. graphics es overlay, no QA.

`sentinel3-check.csv` es una segunda respuesta original del proveedor: mismo día/altitud, centro 36,65625° N / 87,28125° O y máximo 315,09097 mg m^-3. Encabezados y fila de unidades intactos; no se reconstruyó el CSV desde el NetCDF. Las pruebas rechazan unidades, fecha, coordenadas o valor distintos y comprueban idempotencia/conservación/recuperación al simular una falla de transporte. Sólo la respuesta mínima de descubrimiento usada como control de la prueba es generada; los valores y archivos científicos son auténticos.
