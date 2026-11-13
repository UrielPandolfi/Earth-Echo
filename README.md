# Earth Echo

Observatorio ambiental de escritorio. Esta entrega muestra un globo, un escenario DEMO identificable y un subconjunto real: temperatura del mar en el Caribe, sismos, índice Kp, una tendencia y un experimento que no quedó validado. El asistente explica esas herramientas. No anticipa los 31 fenómenos del catálogo.

Los archivos `Earth_Echo_Especificacion.md`, `Earth_Echo_Catalogo.json` y `Earth Echo Global Environmental Observatory.png` son referencias. No los reescribas para implementar una fase. El PNG mide 1672×941 y manda en la composición. Sus números son ilustrativos.

## Requisitos

- Node.js 22 y npm. Este entorno usó Node 22.14.0. Cesium 1.147 declara Node `>=22.17.0`; el aviso no impidió el globo en el navegador.
- Python 3.12 y [uv](https://docs.astral.sh/uv/).
- Un navegador con WebGL.

Docker no está instalado aquí, así que no hay una imagen verificada. En WSL los mismos comandos sirven si existen Node, npm, Python 3.12 y uv. Ejecutalos desde la raíz del repositorio, aunque la ruta tenga espacios.

## Configuración

```powershell
Copy-Item .env.example .env
```

`.env.example` no contiene secretos. Completá en `.env`, no en el chat:

- `EARTHDATA_USERNAME` y `EARTHDATA_PASSWORD` para IMERG o SMAP. Sin ellas esas fuentes quedan bloqueadas.
- `CESIUM_ION_TOKEN` solo si más adelante se usa Cesium ion. No hace falta para Natural Earth II ni para GIBS público, y no debe llevar el prefijo `VITE_`.
- `EARTH_ECHO_LLM_BASE_URL`, `EARTH_ECHO_LLM_MODEL` y, si el endpoint lo pide, `EARTH_ECHO_LLM_API_KEY`. Si quedan vacías, el mapa igual abre.

`VITE_API_BASE` solo cambia la ruta pública del cliente. No guarda tokens.

## Arranque

Desde la raíz, en dos terminales:

```powershell
npm run dev:api
npm run dev:web
```

- Proceso vivo: http://127.0.0.1:8000/health
- Archivos locales, sin sondear proveedores: http://127.0.0.1:8000/ready
- Integraciones conocidas: http://127.0.0.1:8000/providers
- Modelo: http://127.0.0.1:8000/v1/assistant/status
- Pantalla: http://127.0.0.1:5173/

La API escucha en `0.0.0.0` y el puerto `PORT` (8000 por defecto). El navegador usa el proxy `/api` de Vite. El build de la web usa `base: "./"`.

No hay un planificador residente ni Postgres. Las actualizaciones son comandos:

```powershell
npm run ingest:feeds
npm run ingest:d15
npm run ingest:d15-history
```

`ingest:d15-history` pide la serie mensual a NOAA y puede tardar. Un fallo de red no pasa la pantalla a DEMO.

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

## Copia

Detené la API y copiá `data/real`. Ahí están el índice SQLite, la serie mensual, los feeds y los pronósticos archivados. Los NetCDF grandes pueden no estar en Git. Al reponerlos, `GET /ready` distingue archivos presentes de proveedores actualizados. El procedimiento está en `docs/entrega.md`.

## Demostración

1. Abrí http://127.0.0.1:5173/ en DEMO. La ficha de humedad es ilustrativa. Filtrá, buscá y mové el tiempo.
2. Pasá a REAL. La SST, los sismos y el Kp son datos archivados. IMERG sigue bloqueado.
3. En Tendencias, leé la pendiente y hacé un replay: guardar primero, revelar después.
4. Abrí el asistente. Sin modelo, la respuesta cita las herramientas y lo dice.

## Límites

La matriz honesta y el guion están en `docs/entrega.md`. Las decisiones de arquitectura están en `docs/arquitectura.md`. El estado de cada fase está en `PROGRESS.md`.
