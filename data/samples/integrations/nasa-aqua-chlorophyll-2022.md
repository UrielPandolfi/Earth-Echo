# NASA OceanColor: clorofila Aqua OCI histórica

Se siguió el índice público NOAA/PIFSC y se comprobó [aqua_chla_1d_2018_0](https://oceanwatch.pifsc.noaa.gov/erddap/info/aqua_chla_1d_2018_0/index.html). Identidad nativa NASA/GSFC OBPG, Aqua/MODIS, L3 Mapped, algoritmo OCI, DOI10.5067/AQUA/MODIS/L3M/CHL/2018. El título dice v2018.0, pero el archivo dice **2018.1QLP**: se conserva esa versión quicklook; no se presenta como Science Quality R2022.

Último dato disponible en esta distribución: **31/05/2022 12 UTC**, `A2022151.L3m_DAY_CHL_chlor_a_4km.nc`. Es referencia temporal del agregado diario, no pasada individual/emisión. La fecha permanece de 2022 aunque se descargue en 2026. Acceso anónimo sin Earthdata, sin atribuir actualidad a un archivo antiguo. NASA reciente y otras colecciones siguen pendientes.

Subconjunto NetCDF 267.976 B de 360×180 centros, índices12:24:last sobre malla 1/24° (~4,64 km), vista ~1°. Concentración mg/m³, sin escala/offset adicionales; NaN/rango válido nativo0,001…100. Colorbar0,03…30 no es rango científico: el máximo37,184226989746094 se conserva. 60.677 ausentes/4.123 valores visuales, sin rellenar ni atribuir causa a cada hueco. `l2_flag_names` describe flags aguas arriba, no una máscara numérica L2 descargada. No toxicidad, especie, hipoxia o HAB confirmado.

Longitudes originales0…360 normalizadas a−180…180 y valores reordenados con sus columnas; filas norte→sur. Campo casi mundial: huellas extremas recortadas al límite geográfico; oeste−179,97917°, este180°, sur−90°, norte89,97916°. No interpolación, promedios adicionales o pines.

Comprobación independiente de todos los ejes/valores y NaN: ClassicNetCdf/struct frente a netCDF4. Segundo formato/consulta CSV de un valor máximo a54,479164123535156°N/48,52083969116211°E y un ausente a89,47916412353516°N/180,5208282470703°E. CSV usa decimales cortos que vuelven al mismo Float32: comparación exacta a la precisión nativa, sin tolerancia geográfica arbitraria. Valor y ausencia coinciden, incluidas columnas/unidades/fecha.

Fixture `nasa-aqua-chlorophyll-2022.zip`,280.008B, SHA `760d48e48dccfcf8036e51156f4b819aa7a2a9a071360fb7f69038a186ca6cf6`: NetCDF, metadatos de descubrimiento, URL y ambos CSV auténticos/manifiesto. Sólo se excluyen del checksum científico dos líneas de historia de consulta ERDDAP; se conserva el resto de metadatos y todos los valores/ejes nativos.

Ingestión16:10:47 UTC, repetición automática16:12:57 unchanged; revisión mensual de la edición calificada fija. Si el proveedor cambia fecha/versión se exige revisar esa extensión y se conserva el válido. Presupuestos1,5MB campo/150KB info/10KB por CSV; dos intentos HTTP transitorios. Tres pruebas con bytes reales cubren escala/unidad/versión/QA/WGS84/tiempo, coordenadas y máscara CSV incorrectas, repetición/falla/recuperación/procedencia. Captura auténtica REAL `real-nasa-aqua-archive.jpg`.
