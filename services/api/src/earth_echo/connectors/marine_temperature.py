"""Qualified native CMEMS potential temperature at a model depth, not skin SST."""
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import zipfile
import h5py
import netCDF4
import numpy as np
from earth_echo.connectors.hdf_native import native_window
from earth_echo.connectors.marine_currents import ROOT, DOC, LICENSE, UsedRanges, attr
from earth_echo.connectors.ranges import RangeSource, ArchivedRangeSource
from earth_echo.connectors.scientific_archive import pack_files
from earth_echo.contracts.products import ScientificProduct, ScientificGrid, Verification
from earth_echo.storage.products import publish, read_product, products_root

COLLECTION = 'cmems_mod_glo_phy-thetao_anfc_0.083deg_PT6H-i_202406'
METHOD = 'cmems-native-thetao-caribbean-atlantic-1deg-v1'
ID = 'd14-thetao-surface'


def scientific_url(day):
    valid = day + timedelta(days=1)
    return ROOT + COLLECTION + f'/{valid:%Y/%m}/glo12_rg_6h-i_{valid:%Y%m%d}-00h_3D-thetao_fcst_R{day:%Y%m%d}.nc'


def decode(source, day):
    if source.url != scientific_url(day) or not source.etag or source.etag.startswith('W/'):
        raise ValueError('Marine temperature native URL/strong object version missing')
    with source.open() as reader, h5py.File(reader, 'r') as ds:
        if attr(ds.attrs.get('Conventions')) != 'CF-1.6' or attr(ds.attrs.get('source')) != 'MERCATOR GLO12' or attr(ds.attrs.get('product')) != 'GLOBAL_ANALYSISFORECAST_PHY_001_024' or attr(ds.attrs.get('title')) != 'Instantaneous fields for product GLOBAL_ANALYSISFORECAST_PHY_001_024':
            raise ValueError('Marine temperature native collection/time meaning changed')
        lon, lat, depth, time = [ds[k][...] for k in ('longitude', 'latitude', 'depth', 'time')]
        if lon.shape != (4320,) or lat.shape != (2041,) or attr(ds['longitude'].attrs.get('units')) != 'degrees_east' or attr(ds['latitude'].attrs.get('units')) != 'degrees_north' or np.max(abs(lon-(-180+np.arange(4320)/12))) > 2.1e-5 or np.max(abs(lat-(-80+np.arange(2041)/12))) > 1.1e-5:
            raise ValueError('Marine temperature independent native CF axes changed')
        if depth.shape != (50,) or attr(ds['depth'].attrs.get('units')) != 'm' or attr(ds['depth'].attrs.get('positive')) != 'down' or depth[0] != np.float32(.494025) or not np.all(np.diff(depth)>0):
            raise ValueError('Marine temperature native depth changed')
        units = attr(ds['time'].attrs.get('units'))
        if time.shape != (1,) or units != 'hours since 1950-01-01' or attr(ds['time'].attrs.get('calendar')) != 'gregorian':
            raise ValueError('Marine temperature CF time encoding changed')
        stamp = datetime(1950,1,1,tzinfo=timezone.utc)+timedelta(hours=float(time[0]))
        independent = netCDF4.num2date(time[0], units, calendar='gregorian', only_use_cftime_datetimes=False, only_use_python_datetimes=True).replace(tzinfo=timezone.utc)
        if stamp != independent or stamp != day+timedelta(days=1):
            raise ValueError('Marine temperature native time and file identity disagree')
        v = ds['thetao']
        if v.shape != (1,50,2041,4320) or v.dtype != np.dtype('<f4') or v.chunks != (1,6,256,540) or attr(v.attrs.get('standard_name')) != 'sea_water_potential_temperature' or attr(v.attrs.get('units')) != 'degrees_C' or attr(v.attrs.get('cell_methods')) != 'area: mean' or float(v.attrs.get('scale_factor',1)) != 1 or float(v.attrs.get('add_offset',0)) != 0:
            raise ValueError('Marine potential temperature units/layout/meaning changed')
        low, high, fill = [float(np.asarray(v.attrs[k]).item()) for k in ('valid_min','valid_max','_FillValue')]
        if (low,high) != (-10,40) or not np.isfinite(fill) or low <= fill <= high:
            raise ValueError('Marine temperature native quality metadata changed')
        # One compressed chunk includes six depths. Qualify every retained value
        # but publish only depth0; the exact six native layers remain replayable.
        surface = None
        for z in range(6):
            manual = native_window(v,(0,z),1024,1280,1080,1620)
            library = v[0,z,1024:1280,1080:1620]
            if not np.array_equal(manual.view('u4'),library.view('u4')):
                raise ValueError('Marine temperature raw DEFLATE and HDF5 disagree bitwise')
            if z == 0:surface = manual
        rows = np.array([int(np.argmin(abs(lat-y))) for y in np.arange(26.5,5.4,-1)])
        cols = np.array([int(np.argmin(abs(lon-x))) for x in np.arange(-89.5,-45,1)])
        field = surface[np.ix_(rows-1024,cols-1080)]
        values = [None if not np.isfinite(x) or x == fill or x < low or x > high else float(x) for x in field.ravel()]
        metadata = {'collection':COLLECTION,'CF':'1.6','native_depths_m':depth[:6].tolist(),'published_depth_m':float(depth[0]),'native_values_bitwise_checked':829440,
            'native_fill':fill,'native_valid_range_C':[low,high],'time_units':units,'calendar':'gregorian','time_coordinate':stamp.isoformat(),'temporal_statistic':'instantaneous',
            'production_day_from_filename':day.date().isoformat(),'initialized_at':None,'issued_at':None,'native_axis_rounding_tolerance_degrees':{'lon':2.1e-5,'lat':1.1e-5},
            'sampling':'One exact native1/12-degree center every12steps; 45x22view, Caribbean/tropical northwest Atlantic only. No spatial average or interpolation. Native Float32 coordinates retained.', 'method':METHOD}
        return values, lon[cols].tolist(), lat[rows].tolist(), stamp, metadata


def product_from_ranges(range_bytes, day, retrieved_at, now):
    source = UsedRanges(range_bytes)
    values,lons,lats,stamp,metadata = decode(source,day)
    source.cache = {k:source.cache[k] for k in sorted(source.used)}
    native = source.archive(metadata)
    raw = pack_files({'thetao.ranges.json':native},{'schema_version':'1','method':METHOD,'native_metadata':metadata,'assets':{'thetao.ranges.json':{
        'url':source.url,'etag':source.etag,'last_modified':source.modified,'original_object_bytes':source.size,
        'retained_range_bytes':sum(map(len,source.cache.values())),'range_blocks':len(source.cache),'sha256':hashlib.sha256(native).hexdigest()}}},compression=zipfile.ZIP_DEFLATED)
    sha = hashlib.sha256(raw).hexdigest(); present = [v for v in values if v is not None]
    product = ScientificProduct(id=ID,source_id='D14',title='Temperatura potencial marina · 0,494025m · Caribe/Atlántico',
        collection_id='GLOBAL_ANALYSISFORECAST_PHY_001_024 / '+COLLECTION,product_version=f'edition202406 / filename R{day:%Y%m%d} / ETag{source.etag} / CF1.6',
        variable='thetao / sea_water_potential_temperature',unit='°C',native_unit='degrees_C; Float32 sin escala/offset',kind='forecast',representation='field',
        initialized_at=None,issued_at=None,observed_at=None,valid_from=stamp,valid_to=None,retrieved_at=retrieved_at,ingested_at=now,
        issue_time_basis='Campo instantáneo según título nativo. Coordenada CF horas desde1950-01-01/gregorian, UTC predeterminado; nombre de archivo y decodificación independiente coinciden. R identifica día de producción, sin hora de inicialización/emisión acreditada: null. Last-Modified es modificación de distribución, no emisión.',
        original_url=DOC,license_url=LICENSE,attribution='E.U. Copernicus Marine Service Information (CMEMS), Mercator Ocean; MERCATOR GLO12. Selección de centros y subconjunto por Earth Echo; rangos originales conservados.',
        checksum_sha256=sha,byte_size=len(raw),raw_file=f'shared/{sha}.zip',scientific_checksum_sha256=hashlib.sha256(json.dumps({'etag':source.etag,'url':source.url,'values':values,'metadata':metadata},sort_keys=True).encode()).hexdigest(),
        coverage='Caribe y Atlántico tropical noroccidental, límites de vista5–27°N/90–45°O,45×22centros. Un instante previsto y capa modelo a0,494025m. No cobertura mundial o perfil vertical publicado.',
        cadence_seconds=86400,method_version=METHOD,
        grid=ScientificGrid(width=45,height=22,west=-90,east=-45,south=5,north=27,longitudes=lons,latitudes=lats,values=values,
            minimum=min(present) if present else None,maximum=max(present) if present else None,missing_cells=values.count(None),resolution='Nativo1/12°; vista1° (45×22centros)',sampling=metadata['sampling'],
            quality_mask='Relleno nativo/no finito/fuera de valid_min−10…valid_max40°C→missing transparente. Valores negativos válidos dentro de rango; sin flags adicionales. Vista no conserva extremos entre centros.'),
        verification=Verification(method='829.440Float32 de un chunk/seis profundidades cotejados bit a bit: HDF5/h5py frente a decodificación cruda independiente zlib. Ejes regulares independientes con tolerancia de redondeo Float32≤2,1e−5°; tiempo CF con timedelta/netCDF4. Sólo primera profundidad publicada.',original_url=source.url,checked_at=now,
            expected='6×256×540Float32 bitwise; thetao en°C, profundidad0,494025m, CF1950/gregorian',actual=f'829440Float32 coincidentes; {len(present)} centros visibles válidos/{len(values)}; {stamp.isoformat()}',passed=True),
        limitation='Pronóstico físico de temperatura potencial del agua en capa modelo0,494025m; no SST de piel radiométrica, temperatura del aire ni medición observada. Campo instantáneo con promedio espacial nativo area:mean; vista por selección de centros, sin promedio regional ni conservación de extremos. No se combina directamente con climatologías de otros productos para anomalías/MHW. No salinidad/oxígeno, HAB/toxicidad, Vibrio o mortalidad inferidos. Un chunk conserva seis profundidades para reproducir valores; sólo superficie modelada se publica. Sin hora de inicialización/emisión acreditada, no se usa R/Last-Modified como sustituto; ETag multipart identifica versión, sin SHA del objeto3D completo.')
    return product,raw


def fetch_marine_temperature(now):
    if now.tzinfo is None:raise ValueError('Marine temperature requires aware UTC timestamp')
    now=now.astimezone(timezone.utc)
    day=now.replace(hour=0,minute=0,second=0,microsecond=0)-(timedelta(days=1) if now.hour<12 else timedelta())
    source=RangeSource(scientific_url(day),max_bytes=8_388_608,max_requests=64,deadline_seconds=120)
    current=read_product(ID,products_root());retrieved_at=now
    if current:
        raw=(products_root()/current.raw_file).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=current.checksum_sha256:raise ValueError('Marine temperature archive checksum changed')
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:previous=ArchivedRangeSource(archive.read('thetao.ranges.json'))
        if (previous.url,previous.size,previous.etag)==(source.url,source.size,source.etag):
            source.cache.update(previous.cache);retrieved_at=current.retrieved_at
    decode(source,day)
    product,raw=product_from_ranges(source.archive({}),day,retrieved_at,now)
    return publish(product,raw,'.zip')
