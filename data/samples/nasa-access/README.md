# Preparación de acceso NASA, sin integración científica

Consulta pública real retenida el14/11/2026 23:57UTC. Los JSON CMR son respuestas originales exactas, no ejemplos inventados. `readiness.json` contiene URL oficial, hora, tamaño y SHA256 por respuesta. Ningún valor científico, encabezado autenticado, cookie, contraseña, Bearer o URL firmada fue descargado/guardado. D02 y D03 siguen pendientes y no elevan los contadores de fuentes/productos.

| ID | Producto descubierto | Cobertura temporal del metadato | Resultado |
| --- | --- | --- | --- |
| D02 | SPL3SMP_E versión006; G4411996879-NSIDC_CPRD |13/11/2026 00:00–23:59:59.999UTC |credentials_missing |
| D03 | GLDAS_NOAH025_3H versión2.1; G4378063394-GES_DISC |31/07/2026 21:00UTC; inicio y fin iguales en CMR |credentials_missing |

El sufijo `_001` del nombre SMAP no es versión1: la versión006 está en la distribución/colección. Los tiempos de un gránulo no acreditan tiempos de adquisición por píxel ni intervalos de promedio. GLDAS2.1 tiene latencia real; no se sustituyó por Early Product. Sin leer datos no se afirma unidad, máscara, escala o georreferenciación comprobadas.

Reproducir desde `E:\Earth Echo`, PowerShell:

```powershell
& './services/api/.venv/Scripts/python.exe' -m earth_echo.tools.nasa_access --verify-header --retain
```

Sin credenciales retorna2, conserva sólo metadatos públicos y no intenta login. Con `EARTHDATA_USERNAME`/`EARTHDATA_PASSWORD` o `EARTHDATA_TOKEN` existente, y autorización manual de cada DAAC, intenta HEAD/primer bloque128KiB y firma HDF5. Aun si funciona, se informa `header_only`, nunca integración científica. Tope global120s, dos intentos moderados sólo para fallas transitorias, sin retry de401/403. Se rechazan HTML de login, redirecciones ajenas, versiones ambiguas, ETag débil, archivo cambiado, rango ignorado o transporte comprimido. El reporte sanea errores para no registrar secretos.

Pruebas sin credenciales reales verifican metadatos auténticos, versiones/UTC, rechazo previo a login, SDK environment/persist=False, token vacío, ausencia de filtración de secretos, TLS/rangos/límites, S3 sin Bearer, replay/cache, fallas y no publicación. Es evidencia de preparación técnica, no de acceso autenticado ni de valores. [Configuración y enlaces oficiales](../../../docs/accesos.md).
