"""Native MOL sea level and components, with explicit datum and closure check."""
from datetime import datetime,timedelta,timezone
from decimal import Decimal,localcontext
import hashlib
import io
import json
import zipfile
import h5py
import netCDF4
import numpy as np
from earth_echo.connectors.hdf_native import native_window
from earth_echo.connectors.marine_currents import ROOT,DOC,LICENSE,UsedRanges,attr
from earth_echo.connectors.ranges import RangeSource,ArchivedRangeSource
from earth_echo.connectors.scientific_archive import pack_files
from earth_echo.contracts.products import ScientificProduct,ScientificGrid,Verification
from earth_echo.storage.products import publish,read_product,products_root

COLLECTION='cmems_mod_glo_phy_anfc_merged-sl_PT1H-i_202411'
METHOD='cmems-mol-native-northwest-1deg-v1'
VARIABLES={
    'total_sea_level':('total','Altura total del mar · geoide','sea_surface_height_above_geoid'),
    'invert_barometer':('inverse-barometer','Aporte barómetro inverso · nivel del mar','change_in_sea_surface_height_due_to_change_in_air_pressure'),
    'sea_surface_height':('dynamic','Nivel dinámico sin marea ni presión · MOL','ocean_dynamic_sea_level'),
    'ocean_tide':('tide','Elevación por marea oceánica · MOL','sea_surface_height_above_geoid_due_to_ocean_tide'),
}
OFFSETS={'global_mean_steric_variation':'global_average_steric_sea_level_change',
    'global_mean_mass_volume_variation':'global_average_sea_level_change_due_to_water_mass_budget'}
TOTAL_DEFINITION='Total elevation = ocean_tide + invert_barometer + sea_surface_height + global_mean_steric_variation + global_mean_mass_volume_variation'


def scientific_url(day):
    valid=day+timedelta(days=1)
    return ROOT+COLLECTION+f'/{valid:%Y/%m}/MOL_{valid:%Y%m%d}_R{day:%Y%m%d}.nc'


def closure(fields):
    total=fields['total_sea_level'].astype('f8')
    components=[fields[k].astype('f8') for k in (*list(VARIABLES)[1:],*OFFSETS)]
    mask=np.logical_and.reduce([np.isfinite(a)&(a!=-9999) for a in (total,*components)])
    if not np.any(mask):raise ValueError('MOL no joint valid support for native sum check')
    residual=abs(total-sum(components))
    # Four quantities quantized to2^-10m, two offsets to2^-34m, and
    # conservative Float32 arithmetic allowance based on actual magnitudes.
    bound=4/(2*1024)+2/(2*2**34)+8*np.finfo('f4').eps*(abs(total)+sum(abs(a) for a in components))
    if np.any(residual[mask]>bound[mask]):raise ValueError('MOL native total/component closure exceeds quantization budget')
    index=tuple(np.argwhere(mask)[0])
    with localcontext() as context:
        context.prec=50
        delta=abs(Decimal.from_float(float(total[index]))-sum(Decimal.from_float(float(a[index])) for a in components))
    if abs(float(delta)-float(residual[index]))>1e-14:raise ValueError('MOL Decimal/NumPy closure disagree')
    return {'joint_centers_checked':int(mask.sum()),'maximum_absolute_residual_m':float(residual[mask].max()),
        'rounding_bound':'4/(2*1024)+2/(2*2^34)+8*eps_float32*(abs(total)+sum(abs(components))) m',
        'decimal_sample_absolute_residual_m':str(delta),'method':'native-five-component-quantized-closure-v1'}


def decode(source,day):
    if source.url!=scientific_url(day) or not source.etag or source.etag.startswith('W/'):raise ValueError('MOL native URL/strong object identity missing')
    with source.open() as reader,h5py.File(reader,'r') as ds:
        if attr(ds.attrs.get('Conventions'))!='CF-1.6' or attr(ds.attrs.get('source'))!='MERCATOR GLO12,FES2014' or attr(ds.attrs.get('title'))!='hourly mean merged sea levels':raise ValueError('MOL source/temporal statistic changed')
        lon,lat=ds['longitude'][...],ds['latitude'][...]
        for name,axis,expected in [('longitude',lon,-180+np.arange(4320)/12),('latitude',lat,-80+np.arange(2041)/12)]:
            # Producer quantized coordinates too (least_significant_digit3).
            quantized=np.round(expected.astype('f4')*1024)/1024
            if axis.shape!=expected.shape or not np.array_equal(axis.view('u4'),quantized.view('u4')) or int(np.asarray(ds[name].attrs.get('least_significant_digit')).item())!=3 or attr(ds[name].attrs.get('units'))!=('degrees_east' if name=='longitude' else 'degrees_north'):
                raise ValueError('MOL native quantized CF axes changed')
        depth=ds['depth'][...]
        if depth.shape!=(1,) or depth[0]!=np.float32(.494140625) or attr(ds['depth'].attrs.get('units'))!='m' or attr(ds['depth'].attrs.get('positive'))!='Down':raise ValueError('MOL native auxiliary depth changed')
        time=ds['time'][...];units=attr(ds['time'].attrs.get('units'))
        if time.shape!=(24,) or units!='hours since 1950-01-01 00:00:00' or attr(ds['time'].attrs.get('calendar'))!='gregorian':raise ValueError('MOL CF hourly time changed')
        stamps=[datetime(1950,1,1,tzinfo=timezone.utc)+timedelta(hours=float(t)) for t in time]
        independent=netCDF4.num2date(time,units,calendar='gregorian',only_use_cftime_datetimes=False,only_use_python_datetimes=True)
        if stamps!=[t.replace(tzinfo=timezone.utc) for t in independent] or stamps!=[day+timedelta(days=1,minutes=30,hours=i) for i in range(24)]:raise ValueError('MOL native dates/filename disagree')
        if attr(ds['total_sea_level'].attrs.get('long_name'))!=TOTAL_DEFINITION:raise ValueError('MOL total datum/components definition changed')
        fields={};definitions={}
        for name in (*VARIABLES,*OFFSETS):
            v=ds[name];standard=VARIABLES[name][2] if name in VARIABLES else OFFSETS[name]
            digits=3 if name in VARIABLES else 10
            if v.shape!=(24,1,2041,4320) or v.dtype!=np.dtype('<f4') or v.chunks!=(1,1,1021,2160) or attr(v.attrs.get('units'))!='m' or attr(v.attrs.get('standard_name'))!=standard or int(np.asarray(v.attrs.get('least_significant_digit')).item())!=digits or float(v.attrs.get('scale_factor',1))!=1 or float(v.attrs.get('add_offset',0))!=0 or float(np.asarray(v.attrs.get('_FillValue')).item())!=-9999:
                raise ValueError('MOL native units/precision/mask/meaning changed')
            manual=native_window(v,(0,0),1021,2041,0,2160);library=v[0,0,1021:2041,0:2160]
            if not np.array_equal(manual.view('u4'),library.view('u4')):raise ValueError('MOL independent HDF5 raw numeric chunk decode disagrees bitwise')
            fields[name]=manual;definitions[name]=attr(v.attrs.get('long_name'))
        checked=closure(fields)
        rows=np.array([int(np.argmin(abs(lat-y))) for y in np.arange(89.5,5.4,-1)])
        cols=np.array([int(np.argmin(abs(lon-x))) for x in np.arange(-179.5,0,1)])
        values={name:[None if not np.isfinite(v) or v==-9999 else float(v) for v in a[np.ix_(rows-1021,cols)].ravel()] for name,a in fields.items() if name in VARIABLES}
        offsets={}
        for name in OFFSETS:
            valid=fields[name][np.isfinite(fields[name])&(fields[name]!=-9999)]
            if len(valid)==0 or not np.all(valid==valid[0]):raise ValueError('MOL global offset is not constant on qualified support')
            offsets[name]={'value_m':float(valid[0]),'native_definition':definitions[name]}
        metadata={'collection':COLLECTION,'CF':'1.6','native_source':'MERCATOR GLO12,FES2014','native_values_bitwise_checked':13_219_200,
            'native_definitions':definitions,'native_auxiliary_depth_m':float(depth[0]),'native_coordinate_quantization':'least_significant_digit3; binary step1/1024degree',
            'longitude_valid_max_attribute':float(np.asarray(ds['longitude'].attrs['valid_max']).item()),'actual_last_longitude':float(lon[-1]),
            'global_offsets_at_this_time':offsets,'component_closure':checked,'time_coordinate':stamps[0].isoformat(),'time_units':units,'calendar':'gregorian',
            'temporal_statistic':'hourly mean; no time_bounds, endpoints not invented','production_day_from_filename':day.date().isoformat(),'initialized_at':None,'issued_at':None,
            'sampling':'Exact native centers every12steps (1degree view), northwest quadrant only; no spatial averaging/interpolation or preservation of unsampled extremes.','method':METHOD}
        return values,lon[cols].tolist(),lat[rows].tolist(),stamps[0],metadata


def products_from_ranges(range_bytes,day,retrieved_at,now):
    source=UsedRanges(range_bytes)
    values,lons,lats,stamp,metadata=decode(source,day)
    source.cache={k:source.cache[k] for k in sorted(source.used)}
    native=source.archive(metadata)
    raw=pack_files({'mol.ranges.json':native},{'schema_version':'1','method':METHOD,'native_metadata':metadata,'assets':{'mol.ranges.json':{
        'url':source.url,'etag':source.etag,'last_modified':source.modified,'original_object_bytes':source.size,'retained_range_bytes':sum(map(len,source.cache.values())),
        'range_blocks':len(source.cache),'sha256':hashlib.sha256(native).hexdigest()}}},compression=zipfile.ZIP_DEFLATED)
    sha=hashlib.sha256(raw).hexdigest();products=[]
    for name,(suffix,title,standard) in VARIABLES.items():
        field=values[name];present=[v for v in field if v is not None]
        definition=metadata['native_definitions'][name]
        products.append(ScientificProduct(id='d14-mol-'+suffix,source_id='D14',title=title+' · norte occidental',collection_id='GLOBAL_ANALYSISFORECAST_PHY_001_024 / '+COLLECTION,
            product_version=f'edition202411 / filename R{day:%Y%m%d} / ETag{source.etag} / CF1.6',variable=name+' / '+standard,unit='m',native_unit='m; Float32, least_significant_digit3, sin escala/offset',
            kind='forecast',representation='field',observed_at=None,initialized_at=None,issued_at=None,valid_from=stamp,valid_to=None,retrieved_at=retrieved_at,ingested_at=now,
            issue_time_basis='Coordenada CF de media horaria,00:30UTC, sin time_bounds: no se inventan extremos del promedio. CF horas desde1950/gregorian cotejadas con timedelta/netCDF4. R identifica día de producción, no hora de inicialización/emisión: null. Last-Modified del objeto no es emisión científica.',
            original_url=DOC,license_url=LICENSE,attribution='E.U. Copernicus Marine Service Information (CMEMS), Mercator Ocean; MERCATOR GLO12/FES2014. Subconjunto por rangos y selección de centros por Earth Echo.',
            checksum_sha256=sha,byte_size=len(raw),raw_file=f'shared/{sha}.zip',scientific_checksum_sha256=hashlib.sha256(json.dumps({'etag':source.etag,'url':source.url,'variable':name,'values':field,'metadata':metadata},sort_keys=True).encode()).hexdigest(),
            coverage='Subconjunto norte occidental5–90°N/180–0°O de modelo global, una media horaria; vista180×85centros1° desde malla1/12°. No cobertura mundial descargada ni puntos de costa/inundación locales.',cadence_seconds=86400,method_version=METHOD,
            grid=ScientificGrid(width=180,height=85,west=-180,east=0,south=5,north=90,longitudes=lons,latitudes=lats,values=field,minimum=min(present) if present else None,maximum=max(present) if present else None,missing_cells=field.count(None),
                resolution='Nativo1/12°; vista1° (180×85centros)',sampling=metadata['sampling']+' Ejes nativos cuantizados1/1024° conservados; centros elegidos lon−179,5…−0,5/lat89,5…5,5.',quality_mask='_FillValue−9999 o no finito→missing transparente; cero/negativos válidos. Sin flags adicionales o validación costera local.'),
            verification=Verification(method='13.219.200Float32 de seis componentes cotejados bit a bit HDF5 frente a chunks crudos zlib/deshacer shuffle. Ejes por fórmula regular más cuantización binaria nativa. Total cotejado con suma de cinco componentes y cota de cuantización/Float32, muestra Decimal50 independiente.',original_url=source.url,checked_at=now,
                expected='6×1020×2160Float32 bitwise; total=tide+inverse_barometer+dynamic+steric+mass dentro de precisión publicada',actual=f'13219200Float32 coincidentes; {metadata["component_closure"]["joint_centers_checked"]} sumas comprobadas; residual máximo{metadata["component_closure"]["maximum_absolute_residual_m"]}m; {len(present)}/{len(field)} centros visibles válidos.',passed=True),
            limitation='Pronóstico externo físico MOL. Definición nativa: '+definition+'. Altura total referida sobre geoide según CF, no datum local de marea, LAT/MSL local, profundidad de inundación o incremento de nivel respecto de hoy. Componentes conservadas separadas: dinámica sin marea/presión, aporte barométrico inverso y marea oceánica. Variaciones medias estérica/masa referidas al estado inicial20161005 permanecen en manifiesto/original como componentes, no tendencia observada o inicialización del pronóstico. Coordenada depth auxiliar0,494140625m cuantizada nativa, no altura de un sensor. Un plazo/sector, sin cobertura mundial descargada, extremos costeros, tormenta detectada o probabilidad. No es GTSM D41, tsunami, aviso o modelo Earth Echo validado. Sin emisión/inicialización acreditadas; ETag multipart no es SHA del objeto completo.'))
    return products,raw


def fetch_marine_level(now):
    if now.tzinfo is None:raise ValueError('MOL requires aware UTC timestamp')
    now=now.astimezone(timezone.utc)
    day=now.replace(hour=0,minute=0,second=0,microsecond=0)-(timedelta(days=1) if now.hour<12 else timedelta())
    source=RangeSource(scientific_url(day),max_bytes=12_582_912,max_requests=96,deadline_seconds=240)
    current=read_product('d14-mol-total',products_root());retrieved_at=now
    if current:
        raw=(products_root()/current.raw_file).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=current.checksum_sha256:raise ValueError('MOL retained archive checksum changed')
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:previous=ArchivedRangeSource(archive.read('mol.ranges.json'))
        if (previous.url,previous.size,previous.etag)==(source.url,source.size,source.etag):source.cache.update(previous.cache);retrieved_at=current.retrieved_at
    decode(source,day)
    products,raw=products_from_ranges(source.archive({}),day,retrieved_at,now)
    results=[publish(p,raw,'.zip') for p in products]
    return 'unchanged' if all(r=='unchanged' for r in results) else 'stored'
