"""API mínima: salud, catálogo, muestras y consultas con modo explícito."""

import json
from datetime import datetime, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, FastAPI, HTTPException, Path, Query
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

from earth_echo.api.limit import BodyLimitMiddleware
from earth_echo.catalog.load import load_catalog
from earth_echo.catalog.overlay import integration_status_for, load_overlay
from earth_echo.catalog.validate import normalize_capability, validate_catalog
from earth_echo.catalog.views import PhenomenonList, PhenomenonView, SourceList, CatalogSourceView, VariableList
from earth_echo.connectors.smap_metadata import load_smap_asset
from earth_echo.connectors.usgs_comcat import load_usgs_asset, load_usgs_observation
from earth_echo.contracts.api_models import HealthResponse, ProviderReport, ProviderStatus, ReadyResponse
from earth_echo.ops.readiness import local_readiness
from earth_echo.paths import repo_root
from earth_echo.contracts.records import AssetRecord, ObservationRecord, SignalQueryResult
from earth_echo.ingest.d15_sst import default_store
from earth_echo.queries.real_sst import RealSourceView, SstField, d01_blocked, d15_field, d15_view
from earth_echo.catalog.capabilities import CapabilityMatrix, capability_matrix
from earth_echo.assistant.provider import configured_provider
from earth_echo.assistant.reply import AssistantReply, AssistantRequest, ask
from earth_echo.queries.forecasts import calculate_replay, experiment_report, forecast_dir, reveal_replay
from earth_echo.queries.layers import KpLayer, QuakeLayer, kp_layer, quake_layer
from earth_echo.queries.trend import TrendView, trend_csv, trend_view
from earth_echo.queries.signals import query_signals
from earth_echo.settings import get_settings
from earth_echo.contracts.products import ProductList, ScientificProduct
from earth_echo.contracts.operations import RefreshStatus
from earth_echo.queries.products import product_list
from earth_echo.storage.products import read_product, products_root
from fastapi.responses import FileResponse


def create_app() -> FastAPI:
    settings = get_settings()
    from earth_echo.ops.refresh import lifespan
    app = FastAPI(title="Earth Echo", version="0.1.0", lifespan=lifespan)
    app.add_middleware(BodyLimitMiddleware, max_bytes=settings.max_body_bytes)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["Accept", "Content-Type"],
    )
    app.include_router(_routes())
    app.include_router(_real_routes())
    app.include_router(_analysis_routes())
    app.include_router(_scale_routes())
    return app


def _routes() -> APIRouter:
    router = APIRouter()

    @router.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            schema_version="1.0",
            status="ok",
            service="earth-echo-api",
            time=datetime.now(timezone.utc),
            checks=["process"],
        )

    @router.get("/ready", response_model=ReadyResponse)
    def ready() -> ReadyResponse:
        assistant = "configured" if configured_provider(get_settings()) is not None else "unavailable"
        return local_readiness(repo_root(), assistant)

    @router.get("/providers", response_model=ProviderReport)
    def providers() -> ProviderReport:
        document = load_catalog()
        names = {item.id: item.name for item in document.sources}
        listed = []
        for source_id, item in load_overlay().sources.items():
            listed.append(
                ProviderStatus(
                    source_id=source_id,
                    name=names.get(source_id, source_id),
                    integration_status=item.integration_status,
                    sample_kind=item.sample_kind,
                    live_status="not_probed",
                    detail=item.detail,
                )
            )
        return ProviderReport(
            schema_version="1.0",
            checked_at=datetime.now(timezone.utc),
            live_probe="not_performed",
            note=(
                "Este listado no es la salud del proceso. Describe integraciones conocidas "
                "y no sondea proveedores en cada consulta. El resto de las fuentes sigue documentado."
            ),
            providers=listed,
        )

    @router.get("/catalog/sources", response_model=SourceList)
    def sources(
        limit: Annotated[int | None, Query(ge=1, le=100)] = None,
    ) -> SourceList:
        items = [
            CatalogSourceView(
                **source.model_dump(),
                integration_status=integration_status_for(source.id),
            )
            for source in load_catalog().sources
        ]
        returned = items if limit is None else items[:limit]
        return SourceList(schema_version="1.0", total=len(items), returned=len(returned), sources=returned)

    @router.get("/catalog/sources/{source_id}", response_model=CatalogSourceView)
    def source(source_id: Annotated[str, Path(pattern=r"^D\d{2}$")]) -> CatalogSourceView:
        found = next((item for item in load_catalog().sources if item.id == source_id), None)
        if found is None:
            raise HTTPException(status_code=404, detail="La fuente no está en el catálogo.")
        return CatalogSourceView(
            **found.model_dump(),
            integration_status=integration_status_for(found.id),
        )

    @router.get("/catalog/phenomena", response_model=PhenomenonList)
    def phenomena(
        limit: Annotated[int | None, Query(ge=1, le=100)] = None,
    ) -> PhenomenonList:
        items = [
            PhenomenonView(
                **module.model_dump(),
                capability_status=normalize_capability(module.implementation_status),
            )
            for module in load_catalog().modules
        ]
        returned = items if limit is None else items[:limit]
        return PhenomenonList(
            schema_version="1.0",
            total=len(items),
            returned=len(returned),
            phenomena=returned,
        )

    @router.get("/catalog/variables", response_model=VariableList)
    def variables(
        limit: Annotated[int | None, Query(ge=1, le=100)] = None,
    ) -> VariableList:
        items = list(load_catalog().variables)
        returned = items if limit is None else items[:limit]
        return VariableList(
            schema_version="1.0",
            total=len(items),
            returned=len(returned),
            variables=returned,
        )

    @router.get("/catalog/validation")
    def validation():
        return validate_catalog()

    @router.get("/samples/d21/observation", response_model=ObservationRecord)
    def usgs_observation() -> ObservationRecord:
        return load_usgs_observation()

    @router.get("/samples/d21/asset", response_model=AssetRecord)
    def usgs_asset() -> AssetRecord:
        return load_usgs_asset()

    @router.get("/samples/d02/asset", response_model=AssetRecord)
    def smap_asset() -> AssetRecord:
        return load_smap_asset()

    @router.get("/signals", response_model=SignalQueryResult)
    def signals(
        phenomenon_id: Annotated[str, Query(pattern=r"^F\d{2}$")],
        mode: Literal["real", "demo"],
    ) -> SignalQueryResult:
        document = load_catalog()
        if phenomenon_id not in {item.id for item in document.modules}:
            raise HTTPException(status_code=404, detail="El fenómeno no está en el catálogo.")
        return query_signals(phenomenon_id, mode, datetime.now(timezone.utc))

    return router


def _real_routes() -> APIRouter:
    router = APIRouter(prefix="/v1/sources")

    @router.get("/D01", response_model=RealSourceView)
    def imerg_status() -> RealSourceView:
        return d01_blocked()

    @router.get("/D15", response_model=RealSourceView)
    def coral_status() -> RealSourceView:
        return d15_view()

    @router.get("/D15/observations/{observation_id}", response_model=ObservationRecord)
    def coral_observation(observation_id: Annotated[str, Path(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")]) -> ObservationRecord:
        found = next((item for item in d15_view().observations if item.id == observation_id), None)
        if found is None:
            raise HTTPException(status_code=404, detail="Esa observación no está en el subconjunto vigente.")
        return found

    @router.get("/D15/observations/{observation_id}/field", response_model=SstField)
    def coral_field(observation_id: Annotated[str, Path(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")]) -> SstField:
        field = d15_field(observation_id)
        if field is None:
            raise HTTPException(status_code=404, detail="No hay una malla vigente para esa observación.")
        return field

    @router.get("/D15/assets/{asset_id}", response_model=AssetRecord)
    def coral_asset(asset_id: Annotated[str, Path(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")]) -> AssetRecord:
        found = default_store().asset(asset_id)
        if found is None:
            raise HTTPException(status_code=404, detail="Ese activo no está en el índice.")
        return found

    return router


def _analysis_routes() -> APIRouter:
    router = APIRouter(prefix="/v1/analyses")

    @router.get("/d15-sst", response_model=TrendView)
    def sst_trend(
        region_id: str = "caribe-occidental",
        cutoff_year: Annotated[int | None, Query(ge=1985, le=2100)] = None,
        cutoff_month: Annotated[int | None, Query(ge=1, le=12)] = None,
    ) -> TrendView:
        if region_id != "caribe-occidental":
            blocked = trend_view()
            return blocked.model_copy(
                update={
                    "status": "unavailable",
                    "reason": "Esa región no tiene cobertura en este subconjunto. No se usó el escenario DEMO.",
                    "slope_c_per_year": None,
                    "series": [],
                    "trend_line": [],
                    "interval_low_line": [],
                    "interval_high_line": [],
                    "narrative": "Esa región no tiene cobertura en este subconjunto. No se usó el escenario DEMO.",
                }
            )
        if (cutoff_year is None) != (cutoff_month is None):
            raise HTTPException(status_code=422, detail="El corte necesita año y mes.")
        cutoff = None if cutoff_year is None or cutoff_month is None else (cutoff_year, cutoff_month)
        return trend_view(cutoff)

    @router.get("/d15-sst.csv")
    def sst_trend_csv(region_id: str = "caribe-occidental") -> Response:
        if region_id != "caribe-occidental":
            raise HTTPException(status_code=404, detail="Esa región no tiene una serie exportable.")
        return Response(
            content=trend_csv(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=d15-sst-tendencia.csv"},
        )

    return router


def _scale_routes() -> APIRouter:
    router = APIRouter(prefix="/v1")

    @router.get('/operations/refresh',response_model=RefreshStatus)
    def refresh_status():
        from earth_echo.ops.refresh import status
        return status()

    @router.get('/products', response_model=ProductList)
    def products(summaries: bool = False) -> ProductList:
        return product_list(summaries)

    @router.get('/products/{key}', response_model=ScientificProduct)
    def product(key: Annotated[str, Path(pattern=r'^[a-z0-9-]+$')]) -> ScientificProduct:
        found = read_product(key)
        if found is None:
            raise HTTPException(404, 'Producto real no disponible')
        return found

    @router.get('/products/{key}/original')
    def original(key: Annotated[str, Path(pattern=r'^[a-z0-9-]+$')]):
        found = read_product(key)
        if found is None:
            raise HTTPException(404, 'Archivo científico no disponible')
        return FileResponse(products_root() / found.raw_file, filename=found.raw_file.split('/')[-1])

    @router.get("/capabilities", response_model=CapabilityMatrix)
    def capabilities() -> CapabilityMatrix:
        return capability_matrix()

    @router.get("/layers/d21-events", response_model=QuakeLayer)
    def quakes() -> QuakeLayer:
        return quake_layer()

    @router.get("/layers/d28-kp", response_model=KpLayer)
    def kp() -> KpLayer:
        return kp_layer()

    @router.get("/forecasts/d28-kp")
    def kp_forecast() -> dict:
        path = forecast_dir() / "d28-kp-forecast.json"
        if not path.is_file():
            raise HTTPException(status_code=404, detail="No hay un pronóstico de Kp archivado.")
        return json.loads(path.read_text(encoding="utf-8"))

    @router.get("/experiments/sst-anomaly")
    def sst_experiment() -> dict:
        return experiment_report()

    @router.post("/experiments/sst-anomaly/replay")
    def sst_replay(
        year: Annotated[int, Query(ge=2022, le=2025)],
        month: Annotated[int, Query(ge=1, le=12)],
    ) -> dict:
        return calculate_replay((year, month))

    @router.post("/experiments/sst-anomaly/reveal")
    def sst_reveal(
        year: Annotated[int, Query(ge=2022, le=2025)],
        month: Annotated[int, Query(ge=1, le=12)],
    ) -> dict:
        return reveal_replay((year, month))

    @router.get("/assistant/status")
    def assistant_status() -> dict[str, object]:
        provider = configured_provider(get_settings())
        if provider is None:
            return {
                "configured": False,
                "status": "unavailable",
                "model": None,
                "reason": "No están definidas EARTH_ECHO_LLM_BASE_URL y EARTH_ECHO_LLM_MODEL. El mapa sigue disponible.",
            }
        return {
            "configured": True,
            "status": "configured",
            "model": provider.model_name,
            "reason": "El modelo solo puede parafrasear el resultado de las herramientas.",
        }

    @router.post("/assistant/ask", response_model=AssistantReply)
    def assistant_ask(body: AssistantRequest) -> AssistantReply:
        return ask(body.question, body.context, configured_provider(get_settings()))

    return router
