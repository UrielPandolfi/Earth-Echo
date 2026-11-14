"""Versioned historical NASA Aqua chlorophyll through NOAA's public archive."""
import csv,hashlib,io,json,math,re
from datetime import datetime,timezone
import netCDF4
import numpy as np
from earth_echo.connectors.http import download
from earth_echo.connectors.netcdf_classic import ClassicNetCdf
from earth_echo.connectors.ocean_fields import decode_grid
from earth_echo.connectors.scientific_archive import pack_files
from earth_echo.contracts.products import ScientificProduct,Verification
from earth_echo.storage.products import publish

BASE='https://oceanwatch.pifsc.noaa.gov/erddap'
DATASET='aqua_chla_1d_2018_0'
KEY='d17-aqua-chlorophyll-archive'
INFO=BASE+'/info/'+DATASET+'/index.json'


def decode_chlorophyll(raw):
    ds=ClassicNetCdf(raw);attrs=ds.attributes;var=ds.variables['chlor_a']['attributes']
    if attrs.get('institution')!='NASA/GSFC OBPG' or attrs.get('platform')!='Aqua' or attrs.get('instrument')!='MODIS' or attrs.get('processing_level')!='L3 Mapped' or attrs.get('processing_version')!='2018.1QLP':
        raise ValueError('NASA Aqua archive identity/processing version changed; review required')
    if attrs.get('identifier_product_doi')!='10.5067/AQUA/MODIS/L3M/CHL/2018' or var.get('long_name')!='Chlorophyll Concentration, OCI Algorithm':
        raise ValueError('Unexpected NASA OceanColor algorithm/DOI')
    for name,unit in [('latitude','degrees_north'),('longitude','degrees_east')]:
        if ds.variables[name]['attributes'].get('units')!=unit:raise ValueError('Unexpected NASA axis units')
    grid,stamp=decode_grid(raw,'chlor_a','mg m-3',wrap_longitude=True)
    if stamp.strftime('A%Y%j') not in attrs.get('product_name','') or not attrs['product_name'].endswith('.L3m_DAY_CHL_chlor_a_4km.nc'):
        raise ValueError('Native daily NASA filename and time coordinate disagree')
    # All native subset values, including NaNs and axes, independently decoded.
    with netCDF4.Dataset('memory.nc',memory=raw) as check:
        check.set_auto_maskandscale(False)
        for name in ('time','latitude','longitude','chlor_a'):
            values=np.array(ds.values(name));other=np.asarray(check.variables[name][:]).flatten()
            if values.shape!=other.shape or not np.array_equal(values,other,equal_nan=True):raise ValueError('Independent NetCDF4 scientific decoding disagrees')
    if grid.minimum is None or grid.minimum<=0:raise ValueError('No positive qualified NASA chlorophyll; log view cannot silently mask zero')
    grid.color_scale='log10'
    grid.resolution='L3 nativo 1/24° (~4,64 km); vista cada 24 centros (~1°), no media de 1°.'
    grid.sampling='Centros nativos índices12:24:last. Longitudes 0…360 normalizadas a −180…180 y columnas reordenadas con los valores, filas norte→sur. Sin promedio adicional, interpolar huecos o conectar bordes a través del antimeridiano. El NetCDF retenido contiene exactamente los valores científicos nativos muestreados; resolución completa accesible por consulta al proveedor.'
    grid.quality_mask='NaN/_FillValue y rango válido nativo 0,001…100 mg/m³. No se recorta al colorBar 0,03…30. L3 ya procesado por NASA; l2_flag_names enumera flags usados aguas arriba pero no es una máscara numérica por celda. No se inventa QA/confianza adicional o causa de cada hueco. Archivo histórico QLP.'
    science=dict(attrs);science['history']='\n'.join(s for s in science.get('history','').splitlines() if not re.match(r'^\d{4}-\d{2}-\d{2}T[^ ]+ (?:\(local files\)|https://oceanwatch\.pifsc\.noaa\.gov/erddap/griddap/)',s))
    digest=hashlib.sha256(json.dumps({'attributes':science,'dimensions':ds.dimensions,'variables':{k:{'attributes':v['attributes'],'values':ds.values(k)} for k,v in ds.variables.items()}},sort_keys=True,default=str).encode()).hexdigest()
    return grid,stamp,ds,digest


def verify_point(raw,stamp,lat,native_lon,expected):
    rows=list(csv.reader(io.StringIO(raw.decode())))
    if len(rows)!=3 or rows[0]!=['time','latitude','longitude','chlor_a'] or rows[1]!=['UTC','degrees_north','degrees_east','mg m-3']:
        raise ValueError('Independent NASA CSV columns/units disagree')
    r=rows[2]
    # ERDDAP emits shortest-roundtrip decimals for native Float32 axes/values.
    # Compare that exact precision instead of accepting a different pixel via
    # an arbitrary geographic tolerance or rejecting harmless decimal formatting.
    if len(r)!=4 or r[0]!=stamp or np.float32(float(r[1]))!=np.float32(lat) or np.float32(float(r[2]))!=np.float32(native_lon):raise ValueError('Independent NASA CSV time/coordinates disagree')
    actual=float(r[3])
    if expected is None:
        if math.isfinite(actual):raise ValueError('Independent NASA CSV missing mask disagrees')
    elif not math.isfinite(actual) or np.float32(actual)!=np.float32(expected):raise ValueError('Independent NASA CSV value disagrees')


def fetch_nasa_chlorophyll(now:datetime):
    info,_=download(INFO,max_bytes=150_000);attrs={(r[1],r[2]):r[4] for r in json.loads(info)['table']['rows'] if r[0]=='attribute'}
    latest=datetime.fromtimestamp(float(str(attrs[('time','actual_range')]).split(',')[-1]),timezone.utc)
    if latest>now:raise ValueError('Future NASA archive time')
    if latest!=datetime(2022,5,31,12,tzinfo=timezone.utc):raise ValueError('Qualified historical NASA edition changed; review date/version before extending archive')
    stamp=latest.strftime('%Y-%m-%dT%H:%M:%SZ');url=BASE+'/griddap/'+DATASET+'.nc?chlor_a[('+stamp+')][12:24:last][12:24:last]'
    raw,_=download(url,max_bytes=1_500_000);grid,decoded,ds,science_sha=decode_chlorophyll(raw)
    if decoded!=latest:raise ValueError('NASA discovery and actual field date disagree')
    present_index=max((i for i,v in enumerate(grid.values) if v is not None),key=lambda i:grid.values[i])
    missing_index=next((i for i,v in enumerate(grid.values) if v is None),None)
    if missing_index is None:raise ValueError('Unexpected complete daily ocean field; mask review required')
    files={'subset.nc':raw,'discovery.json':info,'request-url.txt':url.encode()}
    for name,index in [('finite',present_index),('missing',missing_index)]:
        lat,lon=grid.latitudes[index//grid.width],grid.longitudes[index%grid.width]
        native_lon=lon%360
        csv_url=BASE+'/griddap/'+DATASET+f'.csv?chlor_a[({stamp})][({lat})][({native_lon})]'
        check,_=download(csv_url,max_bytes=10_000);verify_point(check,stamp,lat,native_lon,grid.values[index]);files[name+'.csv']=check
    archive=pack_files(files,{'schema_version':'1','assets':{n:{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for n,b in files.items()},'discovery_url':INFO})
    sha=hashlib.sha256(archive).hexdigest()
    p=ScientificProduct(id=KEY,source_id='D17',title='Clorofila NASA Aqua · archivo 2022 · OCI',collection_id=DATASET,product_version=ds.attributes['processing_version']+' / '+ds.attributes['product_name']+' / DOI '+ds.attributes['identifier_product_doi'],variable='chlor_a',unit='mg/m³',native_unit='mg m-3',kind='historical',representation='field',observed_at=latest,issued_at=None,issue_time_basis='time=12UTC es referencia del agregado L3 diario, no una pasada individual ni emisión. Último campo disponible en esta distribución:2022. date_created de colección no lo rejuvenece.',retrieved_at=now,ingested_at=now,original_url=url,license_url=ds.attributes['license'],attribution='NASA/GSFC Ocean Biology Processing Group, Aqua MODIS, OCI L3M, DOI 10.5067/AQUA/MODIS/L3M/CHL/2018. Redistribución y cambio de dominio de longitudes por NOAA/PIFSC OceanWatch.',checksum_sha256=sha,scientific_checksum_sha256=science_sha,byte_size=len(archive),raw_file=f'shared/{sha}.zip',coverage='Campo L3 diario de ámbito oceánico mundial, referencia 31/05/2022, con huecos de nubes/tierra/no recuperación sin clasificar por causa. Vista 1°; no es clorofila mundial actual ni cobertura efectiva completa.',cadence_seconds=2592000,method_version='nasa-aqua-oci-archive-stride24-wrap-longitude-v1',grid=grid,
        limitation='Archivo histórico NASA OceanColor de 31/05/2022; versión nativa 2018.1QLP prevalece sobre título comercial v2018.0. QLP/quicklook, no edición Science Quality R2022 actual. La distribución pública termina en 2022: no satisface clorofila NASA reciente, cuya ruta Earthdata sigue pendiente. Concentración de clorofila, no especie, toxicidad, HAB confirmado, hipoxia o enfermedad. Agregado L3 diario, máscara NaN/rango nativo, sin flags L2 por celda descargados. Colorbar no es máscara. Submuestreo de 4,64km a ~1° por centros; las áreas entre centros no son una nueva medición promediada. Longitudes normalizadas sin crear celdas/pines. Los valores científicos del subconjunto y dos CSV independientes están retenidos; no se descargó la colección nativa mundial o su historia completa. Sin tendencia, detector o validación predictiva.',
        verification=Verification(method='Todos los valores y ejes del subconjunto cotejados ClassicNetCdf/struct frente a netCDF4 independiente, incluidos NaN. Máximo válido y celda ausente solicitados de nuevo como CSV: columnas/unidades/UTC/latitud/longitud0…360 y valor/máscara cotejados. Identidad NASA/Aqua/MODIS/DOI/OCI/versión, archivo diario y fecha verificados.',original_url=INFO,checked_at=now,expected=f'Máximo {grid.values[present_index]} mg/m³ y celda ausente, fecha {stamp}',actual='Ambos CSV coinciden; ejes/valores completos coinciden con netCDF4; máscara y reordenación WGS84 conservadas',passed=True))
    return publish(p,archive,'.zip')
