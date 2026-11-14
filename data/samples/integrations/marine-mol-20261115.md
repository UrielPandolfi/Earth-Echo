# Nivel del mar MOL nativo, referencia y componentes

[D14 original](https://data.marine.copernicus.eu/product/GLOBAL_ANALYSISFORECAST_PHY_001_024/description), colección `cmems_mod_glo_phy_anfc_merged-sl_PT1H-i_202411`, archivo `MOL_20261115_R20261114.nc`. Acceso público anónimo HEAD/Range por CloudFerro; objeto469.785.711B, ETag fuerte multipart`908e62d8c32a7e9ee5d0f36a553c43db-57`, Last-Modified14/11/2026 02:37:23GMT. No archivo completo descargado ni MD5/SHA del objeto entero afirmado. ZIP conserva URL exacta, rangos, ETag, SHA, definiciones y método. No cuentas/contratos aceptados.

Primero se comprobó encabezado y punto nativo Caribe(-88°,18°), total0,1396484375m, barómetro inverso−0,0224609375m, nivel dinámico0,1435546875m y marea−0,060546875m. Los chunks de esa muestra abarcan cuadrante5–90°N/180–0°O; luego se seleccionaron180×85centros1° desde malla1/12°, sin otra descarga de esos mismos chunks. No promedio/interpolación espacial o extremos entre centros conservados. Cada campo visible10.875válidos/4.425missing. Rango de vista total−3,8349609375…2,6748046875m; barómetro−0,28125…0,4833984375m; dinámico−1,1162109375…0,8662109375m; marea−3,416015625…2,748046875m.

Metadatos CF1.6 originales:

- `total_sea_level`, `sea_surface_height_above_geoid`: total sobre geoide, suma publicada de marea oceánica+barómetro inverso+altura dinámica+variación estérica media+variación media por masa/volumen. No MSL local, LAT, altura sobre calle, profundidad de inundación o cambio respecto de hoy.
- `invert_barometer`, `change_in_sea_surface_height_due_to_change_in_air_pressure`: aporte de presión, no todo el nivel o marejada de todos los forzantes.
- `sea_surface_height`, `ocean_dynamic_sea_level`: componente calculada sin marea ni forzamiento de presión superficial; no se sustituye por el total.
- `ocean_tide`, `sea_surface_height_above_geoid_due_to_ocean_tide`: elevación por marea oceánica.
- Variación estérica0,009179115295410156m y por masa0,06963543593883514m constantes sobre soporte retenido, referencias del modelo al estado20161005. Se mantienen en manifiesto/original, no una tendencia observada, indicador de aumento actual o inicialización de esta corrida.

Seis ventanas nativas (13.219.200Float32 incluidos rellenos) coinciden bit a bit entre HDF5/h5py y decodificación independiente de chunks crudos zlib/deshacer shuffle. Suma de cinco componentes cotejada en1.565.400centros conjuntos: residual máximo0,0016661137342453003m, no se corrige el original. Cota por celda4/(2×1024)+2/(2×2^34)+8epsFloat32×(abs(total)+sumaabs(componentes))m; cuatro campos con least_significant_digit3, offsets10. Muestra Decimal50 independiente coincide con residual NumPy; aritmética/consistencia no valida habilidad predictiva.

Ejes también cuantizados nativamente: fórmula regular1/12°→Float32→round(x×1024)/1024 coincide bit a bit; error respecto de retícula ideal hasta0,000325521°. La última longitud179,9169921875° supera el valid_max previo179,9167022705078°: se conserva coordenada original, sin extrapolar desde atributo redondeado. Centros visibles enteros+0,5 exactos. Coordenada depth auxiliar0,494140625m cuantizada, no altitud de sensor o datum del nivel. `_FillValue=-9999`, no finitos→null, cero/negativos válidos, sin otros flags de calidad.

Media horaria según título, primera coordenada CF673848,5horas desde1950-01-01/gregorian→15/11/2026 00:30UTC, cotejada con timedelta/netCDF4 y fecha de archivo. Sin time_bounds, inicialización o emisión exactas: no se inventan extremos del promedio ni se tomaR/Last-Modified como emisión. Un solo plazo/hora, sin serie de escenarios.

ZIP auténtico6.652.699B SHA256`5308bb2a8f56714fe47c69eadaedf37895c064bd8805605b425d46418fbc9164`,54bloques/6.970.479B de rangos necesarios, compartido por cuatro productos. Recuperación consolidada14/11 22:13:09,544787UTC, ingestión22:16:00,507079UTC. Revisión diaria `d14-mol-native`,12MiB/96peticiones/240s, HEAD/versionado/cache conservan recuperación al no cambiar objeto; falla conserva último válido/REAL. Atribución CMEMS/Mercator/FES2014 y licencia accesibles. No es GTSM D41, tsunami, aviso, inundación, escenario climático, probabilidad o modelo propio validado.
