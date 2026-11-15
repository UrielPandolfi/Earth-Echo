"""Version-pinned geographic queries. No network I/O or ingestion on click."""
from typing import Annotated
from fastapi import APIRouter, Path, Query, HTTPException
from fastapi.responses import FileResponse, Response
from earth_echo.contracts.predictions import ForecastCatalog, ForecastField, ForecastPoint, ForecastHighlights, PlanetaryForecast, EnsoOutlook
from earth_echo.queries.predictions import forecast_catalog, forecast_field, forecast_point, forecast_highlights, point_csv, retained, planetary_forecast, enso_outlook, enso_csv
from earth_echo.storage.products import products_root

Version = Annotated[str,Path(pattern=r'^[0-9a-f]{64}$')]
Longitude = Annotated[float,Query(ge=-360,le=360,allow_inf_nan=False)]
Latitude = Annotated[float,Query(ge=-90,le=90,allow_inf_nan=False)]


def forecast_routes():
    router=APIRouter(prefix='/v1/forecasts')

    @router.get('/catalog',response_model=ForecastCatalog)
    def catalog(phenomenon_id:Annotated[str|None,Query(pattern=r'^F\d{2}$')]=None):
        result=forecast_catalog()
        if phenomenon_id:
            from earth_echo.catalog.load import load_catalog
            if phenomenon_id not in {m.id for m in load_catalog().modules}:raise HTTPException(404,'Fenómeno no incluido en el catálogo.')
            rows=[f for f in result.forecasts if f.phenomenon_id==phenomenon_id]
            fields=[f for f in rows if f.queryable and f.availability=='available']
            result=result.model_copy(update={'forecasts':rows,'default_d16_id':result.default_d16_id if any(f.id==result.default_d16_id for f in rows) else None,
                'future_fields':sum(f.temporal_state=='future' for f in fields),'current_fields':sum(f.temporal_state=='in_progress' for f in fields),'archived_fields':sum(f.temporal_state=='expired' for f in fields),'own_experiments':0})
        return result

    @router.get('/fields/{version}',response_model=ForecastField)
    def field(version:Version):return forecast_field(version)

    @router.get('/fields/{version}/point',response_model=ForecastPoint)
    def point(version:Version,longitude:Longitude,latitude:Latitude):
        return forecast_point(version,longitude,latitude)

    @router.get('/fields/{version}/point.csv')
    def csv(version:Version,longitude:Longitude,latitude:Latitude):
        return Response(point_csv(forecast_point(version,longitude,latitude)),media_type='text/csv',headers={'Content-Disposition':'attachment; filename=forecast-cell.csv'})

    @router.get('/fields/{version}/highlights',response_model=ForecastHighlights)
    def highlights(version:Version,probability_filter:Annotated[float,Query(ge=0,le=1,allow_inf_nan=False)]=.7,limit:Annotated[int,Query(ge=1,le=40)]=20):
        return forecast_highlights(version,probability_filter,limit)

    @router.get('/fields/{version}/original')
    def original(version:Version):
        p=retained().get(version)
        if p is None or not (products_root()/p.raw_file).is_file():raise HTTPException(404,'Original de esa versión no retenido.')
        return FileResponse(products_root()/p.raw_file,filename=p.raw_file.split('/')[-1])

    @router.get('/planetary/d28-kp',response_model=PlanetaryForecast)
    def kp(version:Annotated[str|None,Query(pattern=r'^[0-9a-f]{64}$')]=None):
        result=planetary_forecast()
        if version and (not result.forecast or result.forecast.id!=version):raise HTTPException(409,'La versión Kp cambió; consultá nuevamente el catálogo planetario. No se sustituyó por otra versión.')
        return result

    @router.get('/planetary/d28-kp/original')
    def kp_original(version:Annotated[str|None,Query(pattern=r'^[0-9a-f]{64}$')]=None):
        import json
        from earth_echo.queries.forecasts import forecast_dir
        from earth_echo.ingest.feeds import feeds_dir
        path=forecast_dir()/'d28-kp-forecast.json'
        if not path.is_file():raise HTTPException(404,'Sin entrada Kp.')
        raw=feeds_dir()/'assets'/'d28-kp-forecast'/f'{version}.json' if version else feeds_dir()/json.loads(path.read_bytes()).get('raw_file','missing')
        if not raw.is_file():raise HTTPException(404,'Original Kp no retenido.')
        return FileResponse(raw,filename=raw.name)

    @router.get('/enso/d48',response_model=EnsoOutlook)
    def enso():
        return enso_outlook()

    @router.get('/enso/d48.csv')
    def enso_export():
        return Response(enso_csv(enso_outlook()),media_type='text/csv',headers={'Content-Disposition':'attachment; filename=f17-enso-roni.csv'})

    return router
