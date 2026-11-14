"""Published global GRACE/CLSM wetness percentiles, not measurements of wells."""
import hashlib
import io
import json
import zipfile
from datetime import datetime,timedelta,timezone
import h5py
import numpy as np
import rasterio
from netCDF4 import num2date
from earth_echo.connectors.http import download
from earth_echo.contracts.products import ScientificProduct,ScientificGrid,Verification
from earth_echo.storage.products import publish
from earth_echo.connectors.scientific_archive import pack_files as pack

PAGE='https://nasagrace.unl.edu/GlobalData.aspx?p=current'
BASE='https://nasagrace.unl.edu/globaldata/current/'
DOC='https://www.drought.gov/data-maps-tools/groundwater-and-soil-moisture-conditions-grace-data-assimilation'
NC='GRACEDADM_CLSM025_GL_7D.nc4'
VARIABLES={
    'gws_inst':('gws_perc_025deg_GL.tif','d33-grace-groundwater','Agua subterránea somera · percentil GRACE/CLSM','ground_water_storage_percentile'),
    'rtzsm_inst':('rtzsm_perc_025deg_GL.tif','d33-grace-root-zone','Zona radicular · percentil GRACE/CLSM','root_zone_soil_moisture_percentile'),
    'sfsm_inst':('sfsm_perc_025deg_GL.tif','d33-grace-surface-soil','Humedad superficial · percentil GRACE/CLSM','surface_soil_moisture_percentile'),
}


def text(value):
    return value.decode() if isinstance(value,bytes) else str(value)


def scalar(value):
    return np.asarray(value).reshape(-1).item(0)


def decode_grace(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if len(z.infolist())!=5 or sum(i.file_size for i in z.infolist())>8_000_000:raise ValueError('Unexpected GRACE archive budget')
        files={name:z.read(name) for name in z.namelist()}
    manifest=json.loads(files.pop('manifest.json'))
    if manifest.get('schema_version')!='1':raise ValueError('Unexpected GRACE manifest version')
    if set(files)!={NC,*[v[0] for v in VARIABLES.values()]} or set(manifest['assets'])!=set(files):raise ValueError('GRACE scientific files differ')
    for name,data in files.items():
        if hashlib.sha256(data).hexdigest()!=manifest['assets'][name]['sha256'] or len(data)!=manifest['assets'][name]['bytes']:raise ValueError('Original GRACE checksum differs')
    products={}
    with h5py.File(io.BytesIO(files[NC]),'r') as nc:
        if text(nc.attrs['title'])!='GRACE Data Assimilation Global Drought Indicator' or text(nc.attrs['version'])!='030' or text(nc.attrs['source'])!='Catchment':
            raise ValueError('GRACE edition/model changed; scientific review required')
        lat=nc['lat'][:];lon=nc['lon'][:]
        if not np.array_equal(lat,np.arange(600,dtype='f4')*.25-59.875) or not np.array_equal(lon,np.arange(1440,dtype='f4')*.25-179.875):raise ValueError('Unexpected GRACE global WGS84 axes')
        for axis,unit in [('lat','degrees_north'),('lon','degrees_east')]:
            if text(nc[axis].attrs['units'])!=unit:raise ValueError('Unexpected GRACE coordinate units')
        time=nc['time'];units=text(time.attrs['units']).strip()
        calendar=text(time.attrs.get('calendar','standard'))
        if calendar not in {'standard','gregorian'}:raise ValueError('Unexpected GRACE calendar')
        if time.shape!=(1,) or units!='days since 2003-02-02 00:00:00' or text(time.attrs['time_increment'])!='7':raise ValueError('Unexpected GRACE native calendar/cadence')
        stamp=datetime(2003,2,2,tzinfo=timezone.utc)+timedelta(days=float(time[0]))
        independent=num2date(float(time[0]),units,calendar=calendar)
        if (independent.year,independent.month,independent.day)!=(stamp.year,stamp.month,stamp.day) or stamp.strftime('%Y%m%d')!=text(time.attrs['begin_date']) or text(time.attrs['begin_time'])!='000000':
            raise ValueError('GRACE CF time and native begin date disagree')
        if stamp.hour or stamp.minute or stamp.second:raise ValueError('Unexpected GRACE reference time')
        native_metadata={k:text(nc.attrs[k]) for k in ['version','input','history','institution','source','references']}
        for variable,(tif,key,title,standard_name) in VARIABLES.items():
            data=nc[variable]
            if data.shape!=(1,600,1440) or text(data.attrs['units'])!='%' or text(data.attrs['standard_name'])!=standard_name or text(data.attrs['cell_methods'])!='time: point':
                raise ValueError('Unexpected GRACE percentile units/shape/temporal support')
            if scalar(data.attrs['scale_factor'])!=1 or scalar(data.attrs['add_offset'])!=0 or scalar(data.attrs['_FillValue'])!=-999 or scalar(data.attrs['missing_value'])!=-999:
                raise ValueError('Unexpected GRACE packing or missing mask')
            native=data[0]
            with rasterio.open(io.BytesIO(files[tif])) as ds:
                if ds.count!=1 or ds.dtypes!=('float32',) or ds.crs.to_epsg()!=4326 or tuple(ds.transform)[:6]!=(.25,0,-180,0,-.25,90) or ds.nodata!=-999:
                    raise ValueError('Independent GRACE TIFF georeferencing/quality differs')
                reference=ds.read(1)
                if not np.array_equal(reference,native[::-1],equal_nan=True):raise ValueError('Independent GRACE TIFF values/missing mask disagree')
            valid=native[(native!=-999)&np.isfinite(native)]
            if not len(valid) or np.min(valid)<0 or np.max(valid)>100:raise ValueError('Invalid GRACE percentile domain')
            # Nearest target centres; exact ties choose south/west, explicitly.
            rows=list(range(597,-1,-4));cols=list(range(1,1440,4))
            values=[float(native[r,c]) if native[r,c]!=-999 and np.isfinite(native[r,c]) else None for r in rows for c in cols]
            present=[v for v in values if v is not None]
            grid=ScientificGrid(width=360,height=150,west=-180,east=180,south=-60,north=90,
                longitudes=[-179.5+c for c in range(360)],latitudes=[89.5-r for r in range(150)],values=values,
                minimum=min(present) if present else None,maximum=max(present) if present else None,missing_cells=values.count(None),reverse_colors=True,
                resolution='Malla del producto 0,25°; vista 1°. No es resolución de observación de GRACE.',
                sampling='Vecino más cercano de centros 0,25° a centros 1°; empate exacto elige sur/oeste (desplazamiento nativo −0,125° en ambas coordenadas). Sin promediar percentiles, rellenar ni extrapolar. Los 864.000 nodos de cada variable permanecen en NetCDF/TIFF conservados.',
                quality_mask='Fill −999/no finito ausente; océano/Antártida y máscara de Groenlandia del proveedor. Cero percentil válido se conserva. No hay flags o ensemble de incertidumbre por celda. Rojo=bajo percentil, azul=alto, sin declaración de daño/inundación/salud.')
            products[variable]=(grid,int((native==-999).sum()))
    return products,stamp,native_metadata,manifest


def fetch_grace(now:datetime):
    listing,_=download(PAGE,max_bytes=200_000)
    for name in [NC,*[v[0] for v in VARIABLES.values()]]:
        if '/globaldata/current/'+name not in listing.decode(errors='replace'):raise ValueError('Published GRACE scientific link missing')
    files={};assets={}
    for name in [NC,*[v[0] for v in VARIABLES.values()]]:
        data,headers=download(BASE+name,max_bytes=3_000_000 if name==NC else 1_500_000)
        files[name]=data;normalized={k.lower():v for k,v in headers.items()}
        assets[name]={'url':BASE+name,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'last_modified_http':normalized.get('last-modified')}
    raw=pack(files,{'schema_version':'1','assets':assets})
    decoded,stamp,metadata,manifest=decode_grace(raw)
    if stamp>now:raise ValueError('GRACE indicator reference is in the future')
    sha=hashlib.sha256(raw).hexdigest();results=[]
    for variable,(tif,key,title,_) in VARIABLES.items():
        grid,native_missing=decoded[variable]
        results.append(publish(ScientificProduct(id=key,source_id='D33',title=title,collection_id='GRACEDADM_CLSM025_GL_7D / NASA GSFC HSL / NDMC',
            product_version='030; input='+metadata['input'],variable=variable,unit='% (percentil)',native_unit='%',kind='indicator',representation='field',observed_at=stamp,
            issued_at=None,issue_time_basis='Hora CF de referencia del modelo, cell_methods=time: point; cadencia 7 días no implica media semanal. CF sin offset usa UTC. Creación literal sin zona: '+metadata['history']+'. HTTP Last-Modified no se usa como emisión.',
            retrieved_at=now,ingested_at=now,original_url=BASE+NC,license_url=DOC,
            attribution='NASA GSFC HSL / GRACE-FO / Catchment / NDMC, University of Nebraska–Lincoln. Li et al. (2019), doi:10.1029/2018WR024618. Datos disponibles en nasagrace.unl.edu mediante colaboración con NDMC.',
            checksum_sha256=sha,byte_size=len(raw),raw_file=f'shared/{sha}.zip',coverage='Producto global terrestre −60…90° de latitud, Groenlandia enmascarada y océano ausente. Una fecha semanal del modelo; no todo lugar tiene valor ni es una lectura de cada pozo.',
            cadence_seconds=86400,method_version='grace-clsm030-global-nearest-v1',grid=grid,
            limitation='Percentil de humedad/almacenamiento derivado de asimilación GRACE-FO en Catchment; no humedad volumétrica, altura/nivel de agua ni medición directa de cada pozo. Referencia global 1948–2012 por localización/época del año según Drought.gov; el NetCDF no repite esa climatología y no se recalculó. Valor alto/bajo no es probabilidad de inundación/sequía futura ni daño confirmado. Rejilla 0,25° no equivale a resolución observacional del satélite. Celda visual 1° toma un vecino nativo según regla explícita; no promedia rangos. Indicador global, no los forecasts CONUS de 30/60/90 días. El atributo input conserva una cadena terminada en 2019-08: no acredita la última observación GRACE asimilada, aunque la referencia del campo sea reciente; no se inventa actualización del satélite. Creación sin zona permanece literal, emisión UTC null. No incertidumbre o habilidad predictiva propia validada.',
            verification=Verification(method='Los 864.000 nodos por variable y su máscara cotejados entre NetCDF/h5py y GeoTIFF/rasterio independientes, tras invertir el eje latitudinal nativo ascendente. CRS, transform, relleno, unidades, escala y referencia CF/begin_date cotejados. No valida modelo o probabilidad.',
                original_url=BASE+tif,checked_at=now,expected=f'864000 nodos TIFF, nodata −999, EPSG:4326; SHA {assets[tif]["sha256"]}',actual=f'864000 nodos NetCDF coincidentes; {native_missing} faltantes nativos; CF {stamp.isoformat()}',passed=True)),raw,'.zip'))
    return 'unchanged' if all(r=='unchanged' for r in results) else 'stored'
