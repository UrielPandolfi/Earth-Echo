# Progreso

## Fase 01 — completada

El repositorio solo tenía la especificación, el catálogo, el PNG y los prompts. No había Git ni aplicación. Quedó una base que arranca, con contratos y una prueba real del globo.

### Hecho

- React, Vite y Cesium en `apps/web`, con un visor que se crea y se destruye.
- FastAPI en `services/api`, salud del proceso separada de proveedores.
- Catálogo validado sin modificar los archivos de referencia.
- Esquema JSON y tipos TypeScript generados desde Pydantic.
- Muestra pública de D21 y metadatos públicos de D02. El HDF de SMAP no se descargó.
- Un fixture demo de F11 que el modo real no devuelve.

### Evidencia

- `uv run --directory services/api pytest`: 23 pruebas pasaron.
- `npm --prefix apps/web test`: 2 pruebas pasaron, incluido el remonte sin una segunda instancia.
- `npm --prefix apps/web run typecheck` y `npm --prefix apps/web run build` terminaron sin error. El build copió workers y Natural Earth a `dist/cesium`.
- En http://127.0.0.1:5173/ el globo mostró América del Sur, el crédito «Natural Earth» y «Instancias activas: 1» antes y después de desmontar. Había un solo canvas. No hubo pedidos a `cesium.com`.
- http://127.0.0.1:8000/health respondió `checks: ["process"]`. `/providers` dejó `live_probe` en `not_performed`. D02 está `credential_required` y D21 `sample_retrieved`.
- La textura local respondió 200 en `/cesium/Assets/Textures/NaturalEarthII/tilemapresource.xml`.

### Limitaciones

- Node 22.14.0 es anterior al `>=22.17.0` que declara Cesium 1.147. El aviso no impidió la prueba en el navegador.
- jsdom quedó en 26.1.0 porque la versión 31 no arranca en este Node.
- Docker no está instalado, así que no se verificó un contenedor.
- D02 no tiene archivo científico. F11 real permanece no disponible.
- D21 no es humedad del suelo ni una conexión operativa.
- Las tres comprobaciones HTTP antiguas del catálogo (USGS, SWPC y CNEOS) no se volvieron a ejecutar como sondeo vivo. Esta fase repitió USGS y consultó CMR para SMAP.
- Los 31 fenómenos siguen especificados, no conectados ni validados.
- El PNG de referencia mide 1672×941, no 1920×1080.

## Siguiente paso

Fase 02: construir la interfaz de escritorio sobre esta pantalla, conservando `mountGlobe` y los contratos. No conectar proveedores reales en esa fase. Para el primer flujo científico sigue haciendo falta Earthdata si la fuente es D02.
