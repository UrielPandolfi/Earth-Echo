# Contornos originales RGI 6.0 — Andes del Sur

`rgi60-southern-andes.zip` conserva los 25.220.396 bytes exactos de `17_rgi60_SouthernAndes.zip`, descargado del [espejo académico OGGM de GLIMS](https://cluster.klima.uni-bremen.de/~oggm/rgi/www.glims.org/RGI/rgi60_files/17_rgi60_SouthernAndes.zip) el 14/11/2026. SHA-256 `31f2ab8477f6f2d0745f11f3a2761692e7e28fbcb1e2c24487db97b269fbc071`. Cinco miembros SHP/SHX/DBF/PRJ/CSV, 50.594.728 bytes expandidos; originales intactos. No es RGI 7.0.

La [ficha oficial de NSIDC](https://nsidc.org/data/nsidc-0770/versions/6) y su informe técnico acreditan versión/unidades/WGS84. La tabla 6 publica 15.908 glaciares y 29.429,080 km² en la región; DBF/CSV coinciden con ambos. Todas las áreas/IDs se comparan entre los dos formatos originales. Las coordenadas/anillos/bbox de los 38 seleccionados se cotejan contra offsets SHP/SHX con una lectura binaria independiente de pyshp.

Selección de visualización: área nativa ≥50 km², Status=0, punto representativo dentro de longitud [-74,5,-72], latitud [-51,-48]. Son 38, no todos los glaciares de Patagonia; sus polígonos se mantienen completos, sin simplificar/recortar. 23.488 vértices nativos. Seis contactos de anillo se normalizan sólo para dibujar, manteniendo área planar relativa a 1e-10 y bbox a 1e-10 grados; no cambia el área científica km². Anillos interiores se conservan. Geometrías fuera del criterio quedan sin dibujo, nunca se reparan de manera irrestricta.

Perito Moreno `RGI60-17.00312`: área original 263,322 km². BgnDate=20009999 y EndDate=20030531: año inicial sin mes/día, rango fuente hasta mayo 2003; no observación UTC actual. Las fechas permanecen como texto. No se infiere retroceso, estabilidad de diques, lagunas, GLOF ni predicción.

Citar RGI Consortium (2017), Randolph Glacier Inventory Version 6, DOI 10.7265/4m1f-gd79, con este subconjunto. Las huellas RGI7 siguen pendientes y son la versión recomendada para trabajo nuevo. Pruebas en `test_glacier_outlines.py`, incluidos desacuerdo de atributos, CRS, rechazo de reparación material, idempotencia y falla/recuperación.
