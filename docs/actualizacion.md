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

Cadencias actuales: sismos y OAF 1 h; CAP 15 min; Kp 3 h; IFS/LHASA 12 h; CRW/OISST/MODIS/MHW/Sentry 24 h; ONI/GVP 7 días; DSM 30 días. Proveedores se consultan secuencialmente, cada trabajo con peticiones acotadas y como máximo dos intentos HTTP transitorios. El fallo se reintenta después de 15 minutos. La tarea de Windows reintenta hasta tres reinicios a intervalos de cinco minutos si termina con error.

El estado se persiste antes de I/O. El lock del SO se libera tras una terminación; un trabajo interrumpido vuelve a ser elegible pasados 15 minutos. Los originales, revisiones y puntero actual se publican atómicamente después de verificar. Cuatro revisiones por producto y 128 MB totales para el almacén nuevo. Al agotar el presupuesto se conserva el dato anterior y se informa el error; no se borra historia científica para fingir éxito.

Los originales grandes usan rangos HTTPS limitados; el archivo de bloques permite decodificar el subconjunto sin red. El activo descargable indica si es el archivo completo o un archivo de rangos. El historial y experimento SST del Caribe conservan su almacenamiento y su límite científico anteriores.
