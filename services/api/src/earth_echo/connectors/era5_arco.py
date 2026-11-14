"""One stable ERA5 hourly surface field from the public, attributed ARCO copy."""
import hashlib
import io
import json
import math
import re
import struct
import zipfile
from datetime import datetime,timedelta,timezone
from decimal import Decimal
import blosc2
import numpy as np
from numcodecs import Blosc
from earth_echo.connectors.http import download
from earth_echo.contracts.products import ScientificProduct,ScientificGrid,Verification
from earth_echo.science.units import kelvin_to_celsius
from earth_echo.storage.products import publish

STORE='ar/full_37-1h-0p25deg-chunk-1.zarr-v3'
BASE='https://storage.googleapis.com/gcp-public-data-arco-era5/'+STORE
DOC='https://github.com/google-research/arco-era5'
CDS='https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview'
VARIABLE='2m_temperature'


def utc_boundary(value):
    parsed=datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):raise ValueError('ERA5 boundary lacks timezone')
        # ARCO explicitly documents its date boundaries in UTC.
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def decode_chunk(raw,metadata):
    if metadata.get('zarr_format')!=2 or metadata.get('order')!='C' or metadata.get('filters') is not None:
        raise ValueError('Unsupported ARCO chunk layout')
    if metadata.get('compressor')!={'blocksize':0,'clevel':5,'cname':'lz4','id':'blosc','shuffle':1}:
        raise ValueError('ARCO compression changed; review required')
    dtype=np.dtype(metadata['dtype'])
    size=math.prod(metadata['chunks'])*dtype.itemsize
    if dtype.str not in ('<f4','<i8') or not 0<size<=4_200_000 or len(raw)<16:
        raise ValueError('Unexpected ARCO dtype or decompression budget')
    _,_,_,typesize,nbytes,blocksize,cbytes=struct.unpack('<BBBBIII',raw[:16])
    if nbytes!=size or cbytes!=len(raw) or typesize!=dtype.itemsize or not 0<blocksize<=size:
        raise ValueError('ARCO compressed buffer size disagrees with metadata')
    first=Blosc().decode(raw)
    second=blosc2.decompress(raw)
    if len(first)!=size or first!=second:
        raise ValueError('Independent C-Blosc1/C-Blosc2 decoding disagrees')
    return np.frombuffer(first,dtype=dtype).reshape(metadata['chunks'])


def archive_assets(files,manifest):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_STORED) as z:
        for name,raw in sorted({**files,'manifest.json':json.dumps(manifest,ensure_ascii=False,sort_keys=True).encode()}.items()):
            # Deterministic container; provider response bytes remain exact.
            z.writestr(zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0)),raw)
    return out.getvalue()


def decode_archive(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if len(z.infolist())>20 or sum(i.file_size for i in z.infolist())>8_000_000:
            raise ValueError('ARCO archive exceeds bounded scientific asset')
        files={name:z.read(name) for name in z.namelist()}
    manifest=json.loads(files.pop('manifest.json'))
    if manifest.get('store')!=STORE or manifest.get('schema_version')!='1':raise ValueError('Unexpected ARCO edition/manifest')
    if set(files)!=set(manifest['assets']):raise ValueError('ARCO manifest coverage differs')
    for name,item in manifest['assets'].items():
        if hashlib.sha256(files[name]).hexdigest()!=item['sha256'] or len(files[name])!=item['bytes']:
            raise ValueError('ARCO original asset checksum differs')
    attrs=json.loads(files['.zattrs'])
    target=datetime.fromisoformat(manifest['selected_time'])
    if target.tzinfo is None or target.utcoffset()!=timedelta(0):raise ValueError('ERA5 reference must be UTC')
    lower=utc_boundary(attrs['valid_time_start'])
    upper=utc_boundary(attrs['valid_time_stop'])
    if not lower<=target<=upper:raise ValueError('Selected time is outside stable ERA5; no silent ERA5T substitution')
    metadata={axis:json.loads(files[axis+'/.zarray']) for axis in ['time','latitude','longitude',VARIABLE]}
    variable_attrs=json.loads(files[VARIABLE+'/.zattrs'])
    if variable_attrs.get('units')!='K' or variable_attrs.get('short_name')!='t2m' or variable_attrs.get('_ARRAY_DIMENSIONS')!=['time','latitude','longitude']:
        raise ValueError('ERA5 surface air temperature units/dimensions changed')
    if metadata[VARIABLE]['chunks']!=[1,721,1440] or metadata[VARIABLE].get('fill_value')!='NaN':
        raise ValueError('Unexpected ERA5 surface shape/fill')
    time_attrs=json.loads(files['time/.zattrs'])
    if time_attrs.get('units')!='hours since 1900-01-01 00:00:00' or time_attrs.get('calendar')!='proleptic_gregorian':
        raise ValueError('Unexpected ERA5 CF time units/calendar')
    epoch=datetime(1900,1,1,tzinfo=timezone.utc)
    origin=int(decode_chunk(files['time/0'],metadata['time'])[0])
    index=manifest['time_index'];chunk=index//metadata['time']['chunks'][0]
    values=decode_chunk(files['time/'+str(chunk)],metadata['time'])
    actual=epoch+timedelta(hours=int(values[index%len(values)]))
    if actual!=target or index!=(target-(epoch+timedelta(hours=origin))).total_seconds()/3600:
        raise ValueError('ERA5 native CF coordinate and selected hour disagree')
    lat=decode_chunk(files['latitude/0'],metadata['latitude'])
    lon=decode_chunk(files['longitude/0'],metadata['longitude'])
    if not np.array_equal(lat,np.linspace(90,-90,721,dtype='f4')) or not np.array_equal(lon,np.arange(1440,dtype='f4')/4):
        raise ValueError('ERA5 geographic coordinates changed')
    for axis,unit in [('latitude','degrees_north'),('longitude','degrees_east')]:
        if json.loads(files[axis+'/.zattrs']).get('units')!=unit:raise ValueError('Unexpected coordinate units')
    native=decode_chunk(files[f'{VARIABLE}/{index}.0.0'],metadata[VARIABLE])[0]
    rows=list(range(2,721,4))
    cols=sorted(range(2,1440,4),key=lambda c:(float(lon[c])+180)%360-180)
    displayed=[kelvin_to_celsius(float(native[r,c])) if np.isfinite(native[r,c]) else None for r in rows for c in cols]
    present=[v for v in displayed if v is not None]
    if not present:raise ValueError('Stable ERA5 chunk entirely absent; previous retained')
    grid=ScientificGrid(width=360,height=180,west=-180,east=180,south=-90,north=90,
        longitudes=[(float(lon[c])+180)%360-180 for c in cols],latitudes=[float(lat[r]) for r in rows],values=displayed,
        minimum=min(present),maximum=max(present),missing_cells=displayed.count(None),
        resolution='Activo ARCO 0,25°; visualización 1°. ERA5 es reanálisis, no observación de sensor.',
        sampling='Stride 4 de centros ARCO: latitudes 89,5…−89,5° y longitudes normalizadas/ordenadas −179,5…179,5°. Sin promedio ni interpolación adicional. El bloque ARCO completo 721×1440 permanece en el ZIP; la remalla a 0,25° pertenece al proveedor.',
        quality_mask='Fill NaN/no finito permanece null. Sin flags o ensemble de incertidumbre descargados; cobertura de reanálisis modelado no equivale a observación directa ni a precisión uniforme.')
    # Native byte/value and conversion check at a displayed WGS84 centre.
    r,c=502,1194 # -35.5°, 298.5° == -61.5°
    native_k=float(native[r,c]);expected=float(Decimal(str(native_k))-Decimal('273.15'))
    actual_c=grid.values[rows.index(r)*360+cols.index(c)]
    if not math.isclose(expected,actual_c,abs_tol=1e-12,rel_tol=0):raise ValueError('Independent Kelvin conversion disagrees')
    # The complete selected chunks/metadata define science; global publication time
    # and the coverage of *other* preliminary ERA5T data cannot create a new stable field.
    scientific={'files':{name:hashlib.sha256(data).hexdigest() for name,data in files.items() if name!='.zattrs'},
        'global_attributes':{k:v for k,v in attrs.items() if k not in {'last_updated','valid_time_stop_era5t'}},
        'selected_time':target.isoformat(),'generation':manifest['assets'][f'{VARIABLE}/{index}.0.0']['generation']}
    science_sha=hashlib.sha256(json.dumps(scientific,sort_keys=True).encode()).hexdigest()
    return grid,target,manifest,science_sha,expected,actual_c


def fetch_era5(now:datetime):
    files={};assets={}
    def get(name,limit=100_000):
        raw,headers=download(BASE+'/'+name,max_bytes=limit)
        files[name]=raw
        normalized={k.lower():v for k,v in headers.items()}
        assets[name]={'url':BASE+'/'+name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'generation':normalized.get('x-goog-generation')}
        return raw
    attrs=json.loads(get('.zattrs'))
    target=utc_boundary(attrs['valid_time_stop'])
    if target>now:raise ValueError('ERA5 stable boundary is in the future')
    meta={}
    for axis in ['time','latitude','longitude',VARIABLE]:
        meta[axis]=json.loads(get(axis+'/.zarray'));get(axis+'/.zattrs')
    origin=int(decode_chunk(get('time/0',1_000_000),meta['time'])[0])
    start=datetime(1900,1,1,tzinfo=timezone.utc)+timedelta(hours=origin)
    index=int((target-start).total_seconds()/3600)
    if not 0<=index<meta['time']['shape'][0]:raise ValueError('Stable ERA5 index outside allocated data')
    time_name='time/'+str(index//meta['time']['chunks'][0])
    if time_name not in files:get(time_name,1_000_000)
    get('latitude/0');get('longitude/0');get(f'{VARIABLE}/{index}.0.0',5_000_000)
    manifest={'schema_version':'1','store':STORE,'selected_time':target.isoformat(),'time_index':index,'assets':assets}
    raw=archive_assets(files,manifest)
    grid,target,manifest,science_sha,expected,actual=decode_archive(raw)
    sha=hashlib.sha256(raw).hexdigest();generation=assets[f'{VARIABLE}/{index}.0.0']['generation']
    return publish(ScientificProduct(id='d08-era5-air-temperature',source_id='D08',title='ERA5 · temperatura del aire a 2 m · archivo estable',
        collection_id=STORE,product_version=f'ARCO store v3 (Zarr format 2), stable ERA5; chunk generation={generation}',
        variable=VARIABLE,unit='°C',native_unit='K',kind='historical',representation='field',observed_at=target,
        issued_at=None,issue_time_basis='Hora de referencia CF del reanálisis en UTC, no observación directa ni emisión de pronóstico. last_updated corresponde al archivo ARCO completo, no a esta hora. Se excluye ERA5T.',
        retrieved_at=now,ingested_at=now,original_url=BASE+'/'+f'{VARIABLE}/{index}.0.0',license_url=CDS,
        attribution='Copernicus C3S / ECMWF ERA5 (Hersbach et al., doi:10.24381/cds.adbb2d47); ARCO redistribuido por Google Research (Carver y Merose, 2023). Contains modified Copernicus Climate Change Service information (2026).',
        checksum_sha256=sha,scientific_checksum_sha256=science_sha,byte_size=len(raw),raw_file=f'd08-era5-air-temperature/assets/{sha}.zip',
        coverage=f'Campo mundial de una hora estable ERA5: {target.isoformat()}. No se descargó una serie temporal ni el archivo de petabytes.',cadence_seconds=604800,
        method_version='era5-arco-stable-hour-stride4-v1',grid=grid,
        limitation='Temperatura del aire a 2 m de reanálisis ERA5, combinación de modelo y observaciones; no SST, LST de satélite ni observación meteorológica directa. Sólo una hora estable: no tendencia, climatología ni detector de ola de calor/frío. ARCO redistribuye/remalla a 0,25°; se conserva el bloque completo y vista stride 4 a 1°, sin agregar interpolación. Epoch CF real 1900: valid_time_start=1940 limita datos calificados pero no es el inicio del eje reservado. No se usa ERA5T ni se supone que toda la forma Zarr esté poblada. Sin incertidumbre/ensemble ni QA por celda descargados. No se leyó el GRIB original de ECMWF; el original conservado es el conjunto exacto de bloques/metadatos ARCO. last_updated no es emisión del campo. Las rutas CDS y otras variables/horas siguen pendientes de ampliar con sus propios accesos/verificaciones.',
        verification=Verification(method='Todos los bytes de los bloques cotejados entre C-Blosc1 (numcodecs) y C-Blosc2, ejes WGS84 completos y hora CF cotejados con calendario UTC. Conversión K→°C en centro −35,5°,−61,5° comprobada con Decimal independiente. No evalúa incertidumbre o habilidad climática.',original_url=DOC,checked_at=now,
            expected=f'{expected:.15g} °C, centro −35,5°,−61,5°; todos los bloques coinciden',actual=f'{actual:.15g} °C; CF {target.isoformat()}',passed=True)),raw,'.zip')
