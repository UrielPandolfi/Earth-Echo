# Inventario RGI7 mundial de atributos

ZIP determinista que conserva los bytes exactos de dos distribuciones públicas, descargadas el 14/11/2026:

- CSV global G de [OGGM](https://cluster.klima.uni-bremen.de/~oggm/rgi/RGI2000-v7.0-G-global-attributes.csv), 74.734.943 bytes, 274.531 registros/19 regiones.
- Tabla CSV de [estadísticas oficiales RGI](https://rgidata.org/user_guide/regions/overview.html), con conteos y áreas regionales independientes.

Manifiesto con URL, tamaño, SHA-256 y estadísticas reproducibles. ZIP de 24.903.281 bytes, SHA-256 `fe1f8499c3bdd11ad042eac95747bc66ed59738907be843f21783ca43e005d1d`. DEFLATE sin pérdida; ambos CSV se recuperan íntegros, no sólo los registros de la vista. No se descargó geometría mundial ni se convirtió una imagen en valores.

Todos los conteos regionales y global coinciden. Área nativa sumada con Decimal: 706.744,049467246904673 km²; estadísticas publicadas redondeadas a 706.744 km². Tolerancia de comparación regional 0,5 km² por ese redondeo. IDs, coordenadas y dominio de área se comprueban en todos los registros.

Vista: 1.851 glaciares con área nativa ≥50 km², 16 regiones. El umbral es cartográfico y no representa peligro; los glaciares menores permanecen en el original. No son centroides: `cenlon/cenlat` son puntos representativos del proveedor. Sin huellas RGI7 descargadas, grandes capas de hielo o Antártida continental. `src_date` literal conserva épocas de imagen sin inventar UTC. Double Glacier `RGI2000-v7.0-G-01-01334`: 132,44631153716037 km²; punto −152,6572955593789°,60,70034149999999°; época nativa 2010-09-12T00:00:00, sin zona. No evento o lectura actual.

Pruebas en `test_glacier_global.py`: estadísticas independientes alteradas, coordenada inválida, identidad, pérdida cero, idempotencia y falla/recuperación. No valida retroceso, GLOF o modelo predictivo. Atribución: RGI 7.0 Consortium (2023), DOI 10.5067/F6JMOVY5NAVZ, CC BY 4.0, y distribución académica OGGM/Universität Bremen.
