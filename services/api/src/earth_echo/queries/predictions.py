"""One version-pinned adapter for fields, clicks, CSV and exploration highlights.

GETs never download, publish, backdate or mutate scientific products. The existing
four-revision retention/budget bounds the archive and its original shared assets.
"""
import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from earth_echo.contracts.products import ScientificProduct
from earth_echo.contracts.predictions import (ForecastDescriptor, ForecastCatalog, ForecastField, ForecastPoint,
    ForecastHighlights, ForecastHighlight, PlanetaryForecast, PlanetaryWindow)
from earth_echo.contracts.operations import RefreshStatus
from earth_echo.contracts.types import parse_utc
from earth_echo.science.forecast_grid import CELL_RULE, HIGHLIGHT_RULE, locate, cell_at, components, normalize_longitude
from earth_echo.storage.products import products_root, all_products

ADAPTER_VERSION='retained-forecast-cell-v1'
IDENTITY_BASIS='ID local SHA256 de fuente/colección/variable/corrida/período/método/contenido y SHA del original retenido; no es un ID oficial del proveedor.'
FIRST_SEEN_BASIS='Mínima ingested_at de esta identidad en revisiones locales retenidas; primera captura local, no publicación del proveedor.'


def clock():
    return datetime.now(timezone.utc)


def temporal_state(start, end, now):
    if start is None:return 'unknown'
    if start>now:return 'future'
    if end is None:return 'expired' if start<now else 'in_progress'
    return 'in_progress' if now<end else 'expired'


def identity(p: ScientificProduct):
    # Exclude slot ID and processing/retrieval dates. Slot1 can later name another
    # month; a retained forecast can move slot without changing its identity.
    scientific=p.model_dump(mode='json',include={'source_id','collection_id','variable','unit','initialized_at','issued_at',
        'valid_from','valid_to','method_version','checksum_sha256','scientific_checksum_sha256','grid','calculation'})
    scientific['adapter_version']=ADAPTER_VERSION
    return hashlib.sha256(json.dumps(scientific,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


@lru_cache(maxsize=80)
def _read(path: str, mtime: int, size: int):
    p=ScientificProduct.model_validate_json(Path(path).read_bytes())
    return p,identity(p)


def _adapted(p):
    return (p.source_id=='D16' and p.variable=='mhw_probability' and p.collection_id=='NOAA PSL NMME_prob90_latest (with trend)' or p.source_id=='D07' and p.kind=='forecast') and p.grid is not None


def retained(root=None):
    active=root or products_root()
    versions={}
    paths=sorted(active.glob('d16-*/revisions/*.json'))+sorted(active.glob('d07-*/revisions/*.json'))
    paths+=sorted(active.glob('d16-*/current.json'))+sorted(active.glob('d07-*/current.json'))
    for path in paths:
        try:
            stat=path.stat();p,key=_read(str(path),stat.st_mtime_ns,stat.st_size)
        except (OSError,ValueError):continue
        if not _adapted(p):continue
        if key not in versions or p.ingested_at<versions[key].ingested_at:versions[key]=p
    return versions


def _operations():
    from earth_echo.ops.refresh import status
    return RefreshStatus.model_validate(status())


def descriptor(p, now, operations=None, *, version=None, root=None):
    key=version or identity(p)
    d16=p.source_id=='D16' and p.variable=='mhw_probability'
    d07=p.source_id=='D07'
    queryable=_adapted(p)
    if d16:
        title='Calor marino previsto · mensual'
        event='Anomalía de SST media mensual por encima del p90 estacional del proveedor, con tendencia retenida.'
        threshold='p90 específico del mes: anomalías de SST en una ventana de tres meses (mes anterior, objetivo y siguiente), referencia 1991–2020.'
    elif d07:
        title={'2t':'Temperatura prevista · aire a 2 m','wind_speed_10m':'Viento previsto · rapidez a 10 m','tp':'Precipitación prevista · acumulación 0–24 h'}.get(p.variable,p.title)
        event='Valor meteorológico de modelo; sin umbral de evento de desastre. '+('Acumulación total del intervalo, no probabilidad de lluvia ni intensidad instantánea.' if p.variable=='tp' else 'Viento medio a 10 m, no ráfaga.' if p.variable=='wind_speed_10m' else '')
        threshold=None
    else:
        title=p.title;event='Producto externo existente; consulta geográfica normalizada todavía no implementada.';threshold=None
    missing=not ((root or products_root())/p.raw_file).is_file()
    job_name='d16-mhw-monthly' if d16 else 'd07-ifs-24h' if d07 else 'd14-smoc-native' if p.id.startswith('d14-smoc-') else 'd14-mol-native' if p.id.startswith('d14-mol-') else {'D09':'d09-seas5-monthly','D10':'d10-glofas-discharge','D12':'d12-cams-global','D48':'d48-roni-outlook-tables','D22':'d22-oaf-recent'}.get(p.source_id,p.id)
    job=operations.jobs.get(job_name) if operations else None
    state=temporal_state(p.valid_from,p.valid_to,now)
    semantics='monthly_interval' if d16 else 'accumulation_interval' if d07 and p.variable=='tp' else 'instant' if p.valid_from and p.valid_to is None else 'published_interval' if p.valid_to else 'unknown'
    spatial='field' if p.grid else 'published_region' if p.regions else 'regional_series' if p.representation=='time_series' else 'table'
    return ForecastDescriptor(id=key,product_id=p.id,source_id=p.source_id,phenomenon_id='F18' if d16 else 'F28' if p.source_id=='D22' else 'F17' if p.source_id=='D48' else None,
        title=title,provider=p.attribution,result_type='imported_probability' if d16 else 'derived_indicator' if p.calculation else 'imported_value',
        spatial_support=spatial,queryable=queryable,availability='missing_input' if missing else 'available' if queryable else 'not_implemented',
        temporal_state=state,variable=p.variable,unit='1' if d16 else p.unit,event_definition=event,scientific_threshold=threshold,
        reference_period='1991–2020' if d16 else None,trend_treatment='retained' if d16 else None,
        method=p.calculation.formula if p.calculation else p.method_version,adapter_version=ADAPTER_VERSION,provider_version=p.product_version,
        identity_basis=IDENTITY_BASIS,initialized_at=p.initialized_at,issued_at=p.issued_at,retrieved_at=p.retrieved_at,
        processed_at=p.ingested_at,first_seen_at=p.ingested_at,first_seen_basis=FIRST_SEEN_BASIS,valid_from=p.valid_from,valid_to=p.valid_to,
        temporal_semantics=semantics,coverage=p.coverage,resolution=p.grid.resolution if p.grid else None,quality_mask=p.grid.quality_mask if p.grid else None,
        original_url=p.original_url,original_sha256=p.checksum_sha256,original_download=f'/v1/forecasts/fields/{key}/original' if queryable else f'/v1/products/{p.id}/original',
        metadata_download=f'/v1/forecasts/fields/{key}' if queryable else f'/v1/products/{p.id}',
        reference_url='https://psl.noaa.gov/marine-heatwaves/' if d16 else p.license_url,
        limitation=('Experimental de investigación. No predice el evento diario de cinco días, daño coralino, mortalidad ni temperatura del aire. ' if d16 else '')+p.limitation,
        experimental=d16 or p.source_id in {'D09','D16'},update=job,update_pending=(now-(job.last_success_at if job and job.last_success_at else p.retrieved_at)).total_seconds()>p.cadence_seconds)


def forecast_catalog(now=None, root=None, operations=None):
    moment=now or clock();ops=operations if operations is not None else _operations()
    versions=retained(root)
    entries=[descriptor(p,moment,ops,version=k,root=root) for k,p in versions.items()]
    # Other existing products stay discoverable with their actual temporal state;
    # kind=forecast alone does not imply future or a query adapter.
    for p in all_products(root or products_root()):
        if p.kind=='forecast' and not _adapted(p):entries.append(descriptor(p,moment,ops,root=root))
    entries.sort(key=lambda f:(f.source_id,f.valid_from or f.retrieved_at,f.variable,f.first_seen_at,f.id))
    monthly=[e for e in entries if e.source_id=='D16' and e.availability=='available']
    future=[e for e in monthly if e.temporal_state=='future']
    # First complete future month; latest retained cycle for that month. If no
    # future remains, show the latest available archive/current month explicitly.
    chosen=min(future,key=lambda e:(e.valid_from,-(e.initialized_at or e.first_seen_at).timestamp(),-e.first_seen_at.timestamp())) if future else max(monthly,key=lambda e:(e.valid_from,e.first_seen_at),default=None)
    fields=[e for e in entries if e.queryable and e.availability=='available']
    return ForecastCatalog(as_of=moment,forecasts=entries,default_d16_id=chosen.id if chosen else None,
        future_fields=sum(e.temporal_state=='future' for e in fields),current_fields=sum(e.temporal_state=='in_progress' for e in fields),archived_fields=sum(e.temporal_state=='expired' for e in fields),
        own_experiments=1 if ((root or products_root()).parent/'d15/monthly_series.json').is_file() else 0,
        note='Son productos/campos retenidos, no eventos detectados. Probabilidades/valores del proveedor; Earth Echo integra y permite consultar. Experimento SST retrospectivo separado, sin habilidad adicional demostrada.')


def forecast_field(key, now=None, root=None, operations=None):
    p=retained(root).get(key)
    if p is None:
        other=next((p for p in all_products(root or products_root()) if p.kind=='forecast' and not _adapted(p) and identity(p)==key),None)
        if other is not None:return ForecastField(status='not_implemented',reason='Producto existente, consulta geográfica aún no adaptada.',forecast=descriptor(other,now or clock(),root=root))
        return ForecastField(status='missing_input',reason='Versión no retenida o entrada ausente; no se sustituyó por otra corrida ni DEMO.')
    meta=descriptor(p,now or clock(),operations if operations is not None else _operations(),version=key,root=root)
    if meta.availability=='missing_input':return ForecastField(status='missing_input',reason='Original científico no disponible.',forecast=meta)
    return ForecastField(status='expired' if meta.temporal_state=='expired' else 'available',forecast=meta,grid=p.grid)


def point_from_field(field, longitude, latitude):
    lon=normalize_longitude(longitude)
    base=dict(forecast=field.forecast,requested_longitude=lon,requested_latitude=latitude,selection_rule=CELL_RULE,unit=field.forecast.unit if field.forecast else None)
    if field.grid is None:return ForecastPoint(status=field.status,reason=field.reason,**base)
    address=locate(field.grid,lon,latitude)
    if address is None:return ForecastPoint(status='no_coverage',reason='Sin cobertura en esta posición: fuera del soporte de la malla.',**base)
    r,c=address;cell=cell_at(field.grid,r,c);v=field.grid.values[r*field.grid.width+c]
    if v is None:return ForecastPoint(status='no_coverage',reason='Sin cobertura en esta posición: máscara nativa (tierra/hielo/sin salida). No se buscó otra celda.',cell=cell,**base)
    probabilistic=field.forecast.result_type=='imported_probability'
    return ForecastPoint(status=field.status,cell=cell,probability=v if probabilistic else None,value=None if probabilistic else v,**base)


def forecast_point(key, longitude, latitude, now=None, root=None, operations=None):
    return point_from_field(forecast_field(key,now,root,operations),longitude,latitude)


def forecast_highlights(key, threshold=.7, limit=20, now=None, root=None, operations=None):
    field=forecast_field(key,now,root,operations)
    base=dict(forecast_id=key,probability_filter=threshold,rule=HIGHLIGHT_RULE,limit=limit)
    if field.grid is None:return ForecastHighlights(status=field.status,reason=field.reason,matching_cells=0,total_areas=0,returned_areas=0,areas=[],**base)
    if field.forecast.result_type!='imported_probability':return ForecastHighlights(status='not_implemented',reason='Este producto contiene valores, no probabilidades definidas.',matching_cells=0,total_areas=0,returned_areas=0,areas=[],**base)
    if all(v is None for v in field.grid.values):return ForecastHighlights(status='no_coverage',reason='Sin datos válidos: el campo está completamente enmascarado.',matching_cells=0,total_areas=0,returned_areas=0,areas=[],**base)
    matching,groups=components(field.grid,threshold)
    areas=[]
    for rep,count,low,high in groups[:limit]:
        r,c=divmod(rep,field.grid.width)
        result=point_from_field(field,field.grid.longitudes[c],field.grid.latitudes[r])
        areas.append(ForecastHighlight(id=f'{key}:r{r}-c{c}',cell_count=count,probability_min=low,probability_max=high,representative=result))
    return ForecastHighlights(status=field.status,reason='Sin áreas que cumplan este filtro.' if not groups else None,matching_cells=matching,total_areas=len(groups),returned_areas=len(areas),areas=areas,**base)


def point_csv(result):
    stream=io.StringIO();writer=csv.writer(stream)
    writer.writerow(['forecast_id','product_id','source_id','phenomenon_id','valid_from','valid_to','temporal_semantics','initialized_at','issued_at','retrieved_at','processed_at','first_seen_at','status','cell_id','longitude','latitude','probability','value','unit','event_definition','scientific_threshold','reference_period','trend_treatment','original_sha256','adapter_version'])
    f=result.forecast;c=result.cell
    writer.writerow([f.id if f else None,f.product_id if f else None,f.source_id if f else None,f.phenomenon_id if f else None,
        f.valid_from.isoformat() if f and f.valid_from else None,f.valid_to.isoformat() if f and f.valid_to else None,f.temporal_semantics if f else None,
        *[getattr(f,k).isoformat() if f and getattr(f,k) else None for k in ['initialized_at','issued_at','retrieved_at','processed_at','first_seen_at']],
        result.status,c.id if c else None,c.longitude if c else result.requested_longitude,c.latitude if c else result.requested_latitude,
        result.probability,result.value,result.unit,f.event_definition if f else None,f.scientific_threshold if f else None,f.reference_period if f else None,f.trend_treatment if f else None,f.original_sha256 if f else None,f.adapter_version if f else None])
    return stream.getvalue()


def planetary_forecast(now=None, operations=None):
    from earth_echo.queries.forecasts import forecast_dir
    moment=now or clock();path=forecast_dir()/'d28-kp-forecast.json'
    note='Sólo filas originales predicted; ventanas [inicio,fin) de tres horas, incluidas las ya iniciadas mientras no terminen. Índice planetario; sin ubicación, probabilidad local de aurora o habilidad evaluada.'
    if not path.is_file():return PlanetaryForecast(status='missing_input',reason='No hay entrada Kp retenida.',windows=[],note=note)
    data=json.loads(path.read_bytes());retrieved=parse_utc(data['retrieved_at']);steps=data.get('steps',[])
    # Recover the provider's still-running predicted window from the retained raw
    # JSON even for snapshots made by the former start>=retrieval parser.
    from earth_echo.ingest.feeds import feeds_dir
    from earth_echo.connectors.swpc_forecast import parse_predicted_kp
    raw_path=feeds_dir()/data.get('raw_file','missing')
    if raw_path.is_file():steps=parse_predicted_kp(json.loads(raw_path.read_bytes()),retrieved)
    windows=[PlanetaryWindow(valid_from=s['valid_start'],valid_to=s['valid_end'],value=s['kp'],temporal_state=temporal_state(parse_utc(s['valid_start']),parse_utc(s['valid_end']),moment)) for s in steps]
    windows.sort(key=lambda w:w.valid_from)
    ops=operations if operations is not None else _operations();job=ops.jobs.get('d28-kp-forecast')
    version=data.get('checksum_sha256') or hashlib.sha256(path.read_bytes()).hexdigest()
    meta=ForecastDescriptor(id=version,product_id='d28-kp',source_id='D28',phenomenon_id='F29',title='Kp previsto · índice planetario',provider='NOAA SWPC',result_type='imported_value',spatial_support='planetary',queryable=False,availability='available',
        temporal_state='future' if any(w.temporal_state=='future' for w in windows) else 'in_progress' if any(w.temporal_state=='in_progress' for w in windows) else 'expired',
        variable='Kp',unit='Kp',event_definition='Índice Kp planetario previsto; no probabilidad de auroras locales.',method='Filas predicted originales SWPC',adapter_version=ADAPTER_VERSION,provider_version=data.get('product_version','unknown'),identity_basis='SHA256 del JSON original SWPC retenido; identidad local, no emisión.',
        initialized_at=data.get('initialized_at'),issued_at=data.get('issued_at'),retrieved_at=retrieved,processed_at=data.get('archived_at',retrieved),first_seen_at=data.get('first_seen_at',data.get('archived_at',retrieved)),first_seen_basis='Captura local retenida, no publicación SWPC.',
        valid_from=windows[0].valid_from if windows else None,valid_to=windows[-1].valid_to if windows else None,temporal_semantics='three_hour_windows',coverage='Planetario; sin geometría local.',
        original_url='https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json',original_sha256=version,original_download=f'/v1/forecasts/planetary/d28-kp/original?version={version}',metadata_download=f'/v1/forecasts/planetary/d28-kp?version={version}',reference_url='https://www.swpc.noaa.gov/products/planetary-k-index',limitation=note,experimental=False,update=job,update_pending=(moment-(job.last_success_at if job and job.last_success_at else retrieved)).total_seconds()>10800)
    return PlanetaryForecast(status='expired' if meta.temporal_state=='expired' else 'available',forecast=meta,windows=windows,note=note)
