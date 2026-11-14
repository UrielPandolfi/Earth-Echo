# GWIS: exportación numérica aún no calificada

Respuestas reales obtenidas del endpoint oficial `https://maps.effis.emergency.copernicus.eu/gwis`, 14/11/2026. No se publican como producto ni suman fuentes conectadas.

- `capabilities.xml`: WMS 1.3.0 GetCapabilities. `ecmwf.fwi` no es queryable; su dimensión time no informa emisión/ciclo. `wcs-capabilities.xml`: WCS 1.0.0; `fwi-description.xml`: DescribeCoverage de `ecmwf.fwi` devuelve CoverageNotDefined. `fwi-metadata.xml`: GetMetadata de esa capa.
- TIFF: WMS 1.1.1 GetMap, LAYERS=ecmwf.fwi, FORMAT=image/tiff, STYLES vacío, SRS=EPSG:4326, TIME=2026-11-15. `fwi-global.tif`: bbox -180,-90,180,90, 360×180, TRANSPARENT=true. `fwi-pampa-probe.tif`: bbox -63,-36,-61,-34, 16×16. `fwi-pampa-expanded.tif`: bbox -64,-37,-60,-33, 32×32, TRANSPARENT=true.
- El TIFF sí tiene una banda Float32 numérica, escala 1, offset 0 y WGS84. Pero nodata es None, máscara todo válido, 51.330 ceros en la vista mundial y cero sobre océano. No permite distinguir fondo de FWI=0 físico. Un control con BGCOLOR blanco no cambió esos valores. No se inventó una máscara científica desde colores o geografía aproximada.
- El centro 16×16 del recorte ampliado difiere en 192 celdas del recorte previo, máximo 3,09734 unidades. No se determinó si hubo cambio de ciclo entre peticiones o un efecto del muestreo del servidor; no se declara cotejo independiente satisfactorio. No hay emisión/ciclo embebido en el TIFF, y la fecha de la consulta no sustituye ese dato.

Falta un producto nativo con máscara, ciclo/validez y remuestreo acreditados para cerrar esta integración. La documentación oficial distingue tiempo real GWIS/EFFIS de historia/estacionales por EWDS: <https://confluence.ecmwf.int/spaces/CEMS/pages/382667784/CEMS-Fire+Data+access>. Licencia: <https://gwis.jrc.ec.europa.eu/about-gwis/data-license>. Solicitud manual de datos, si se necesita: <https://forest-fire.emergency.copernicus.eu/apps/data.request.form/>; no se envió ningún formulario.

`evidence.json` conserva tamaños/SHA y diagnóstico. Son pruebas de acceso real y de una limitación, no valores científicos calificados para alimentar un detector.
