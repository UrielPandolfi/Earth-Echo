# Actualización local de productos reales

La tarea **Earth Echo - Public Data Refresh** está instalada y comprobada en ejecución en este equipo. Inicia con la sesión del usuario, mediante `pythonw.exe -m earth_echo.tools.refresh --watch` y directorio de trabajo del proyecto. No requiere que la interfaz esté abierta; el equipo debe estar encendido y la sesión iniciada. No es un servicio de arranque anterior al inicio de sesión.

Desde PowerShell en la raíz, después de instalar dependencias:

```powershell
& './ops/windows/install-refresh.ps1' -WhatIf
& './ops/windows/install-refresh.ps1'
Get-ScheduledTask -TaskName 'Earth Echo - Public Data Refresh'
```

El instalador verifica la acción de cualquier tarea preexistente con el mismo nombre y rechaza reemplazar otra aplicación. No copia secretos a argumentos. Para detenerla temporalmente: `Stop-ScheduledTask -TaskName 'Earth Echo - Public Data Refresh'`. Para quitar solo esta tarea: `& './ops/windows/remove-refresh.ps1'`. También puede correrse `npm run refresh:watch` en primer plano o la API; comparten el mismo lock.

`.env` y las variables del proceso son del servidor. `EARTH_ECHO_REFRESH_ENABLED=0` desactiva el watcher en su siguiente inicio; reiniciar el proceso después de cambiarlo. No existe cambio automático a DEMO. `GET /v1/operations/refresh` informa estado tipado: último intento, última descarga satisfactoria, último cambio, próximo intento, error y conservación del dato anterior. `last_scan_at`/`recent_scan` identifican que se revisaron vencimientos, aun sin descargar. Un éxito sin novedades no cambia la fecha científica ni crea una revisión.

Cadencias actuales: sismos y OAF 1 h; CAP NTWC/PTWC 15 min; GDACS 6 h; Kp/FIRMS 3 h; IFS/LHASA y derivados IFS 12 h; CRW/OISST/MODIS/MHW/Sentry/IBTrACS/ASIS/RAMSES/reportes GVP/Sentinel-3 24 h; ONI/GVP/RAPID 7 días; DSM/GEBCO/HydroATLAS/RGI7 30 días. Los derivados IFS leen originales retenidos y no vuelven a descargarlos. Proveedores se consultan secuencialmente, cada trabajo con peticiones acotadas y como máximo dos intentos HTTP transitorios. El fallo se reintenta después de 15 minutos. La tarea de Windows reintenta hasta tres reinicios a intervalos de cinco minutos si termina con error.

El estado se persiste antes de I/O. El lock del SO se libera tras una terminación; un trabajo interrumpido vuelve a ser elegible pasados 15 minutos. Los originales, revisiones y puntero actual se publican atómicamente después de verificar. Cuatro revisiones por producto y 256 MB totales por defecto para el almacén nuevo (`EARTH_ECHO_PRODUCT_STORE_MAX_BYTES`, rango aceptado 32 MB–2 GB). Se amplió desde 128 MB tras medir 71,5 MB usados, 47,8 MB de productos actuales y 177,6 GB de disco libre, para permitir revisiones con los nuevos campos. Al agotar el presupuesto se conserva el dato anterior y se informa el error; no se borra historia científica para fingir éxito.

Cada trabajo corre en un proceso hijo sin ventana, con límite total de 180 s (`EARTH_ECHO_REFRESH_JOB_TIMEOUT_SECONDS`, rango 30–600 s). HydroATLAS tiene 420 s por el primer acceso medido de 31,7 MB (`EARTH_ECHO_HYDROATLAS_TIMEOUT_SECONDS`, 30–600 s). El límite incluye DNS, descarga y decodificación: no depende de que el servidor deje de enviar bytes. Al vencer, el padre termina y espera al hijo, registra fallo, conserva la última descarga válida y continúa con la próxima fuente. El padre conserva el lock y el estado; el hijo ejecuta exclusivamente el trabajo registrado, sin otro planificador. Los secretos se heredan por entorno, nunca por argumentos.

Los originales grandes usan rangos HTTPS limitados; el archivo de bloques permite decodificar el subconjunto sin red. El activo descargable indica si es el archivo completo o un archivo de rangos. El historial y experimento SST del Caribe conservan su almacenamiento y su límite científico anteriores.

Comprobación local reproducible (sin descargar otra vez proveedores): `python -m earth_echo.tools.verify_integrations`. Compara referencias, SHA originales almacenados/servidos, detalles API, leyendas, máscaras y consultas de contadores bajo el mismo lock de lectura. Guarda `data/operational/integration_evidence.json`. Es una comprobación de consistencia de integración, no validación predictiva.

RAPID revisa semanalmente la edición fija v2024-2: una edición nueva requiere revisar método/unidades antes de cambiar la URL. La fecha del dato histórico (hasta noviembre 2024) no avanza por descargar de nuevo ni se convierte en pronóstico. El trabajo `d34-amoc-annual-trend` calcula desde ese mismo original retenido, sin descargarlo otra vez, y conserva el resultado anterior si falta o no coincide la entrada. Separa intento, cálculo satisfactorio y cambio de resultado.

ERA5 ARCO (`d08-era5-air-temperature`) revisa semanalmente la última frontera **estable** declarada por el distribuidor. Descarga sólo un bloque horario de temperatura a 2 m y sus ejes/metadatos; no ERA5T ni la forma completa del store. La frontera es distinta del origen real del eje temporal (1900); se coteja la hora CF. Cambios en `last_updated` global o en cobertura de otros datos ERA5T no crean una revisión del mismo campo estable. El archivo ZIP conserva bytes originales/generaciones GCS; ambas bibliotecas de compresión deben coincidir antes de publicar.
