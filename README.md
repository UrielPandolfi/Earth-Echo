# Earth Echo

Observatorio ambiental mundial. Esta fase deja el proyecto ejecutable: interfaz técnica, globo Cesium y API con contratos. El diseño de la referencia visual llega en la fase 02.

Los archivos `Earth_Echo_Especificacion.md`, `Earth_Echo_Catalogo.json` y `Earth Echo Global Environmental Observatory.png` son referencias. No los reescribas para implementar una fase.

## Requisitos

- Node.js 22 y npm. Este entorno usó Node 22.14.0. Cesium 1.147 declara Node `>=22.17.0`; el paquete se instaló con un aviso y el globo funcionó en el navegador.
- Python 3.12 y [uv](https://docs.astral.sh/uv/).
- Un navegador con WebGL.

Docker no está instalado aquí, así que no hay una imagen verificada. En WSL los mismos comandos sirven si existen Node, npm, Python 3.12 y uv. Ejecutalos desde la raíz del repositorio, aunque la ruta tenga espacios.

## Configuración

```powershell
Copy-Item .env.example .env
```

`.env.example` no contiene secretos. Para descargar el HDF de SMAP (D02) más adelante hacen falta `EARTHDATA_USERNAME` y `EARTHDATA_PASSWORD` en el entorno local o en un `.netrc`. No las pegues en el chat. `CESIUM_ION_TOKEN` no hace falta para esta fase y no debe llevar el prefijo `VITE_`.

## Arranque

Desde la raíz del repositorio, en dos terminales:

```powershell
npm run dev:api
npm run dev:web
```

- API: http://127.0.0.1:8000/health
- Pantalla: http://127.0.0.1:5173/

La API escucha en `0.0.0.0` y el puerto `PORT` (8000 por defecto). El navegador usa el proxy `/api` de Vite.

## Comprobaciones

```powershell
npm run test:api
npm run test:web
npm run typecheck
npm run build:web
npm run contracts:check
```

`contracts:check` compara el esquema y los tipos TypeScript con los modelos Pydantic. Para regenerarlos:

```powershell
uv run --directory services/api python -m earth_echo.contracts.schema_export --write
```

## Qué hay hoy

La pantalla de escritorio monta el globo con Natural Earth II, incluido en CesiumJS, sin Cesium ion. El escenario visible es DEMO. La API distingue la salud del proceso de la disponibilidad de proveedores. El modo `real` no cae al modo `demo` cuando falta una fuente.

La documentación de decisiones está en `docs/arquitectura.md`. El estado de la fase está en `PROGRESS.md`.
