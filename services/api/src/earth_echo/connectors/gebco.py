"""Small numeric OPeNDAP subset plus independent native HDF5 value checks."""
import hashlib
import json
import re
import struct
from datetime import datetime
from urllib.parse import quote
import h5py
from earth_echo.connectors.http import download
from earth_echo.connectors.ranges import RangeSource
from earth_echo.connectors.netcdf_classic import ClassicNetCdf
from earth_echo.contracts.products import ScientificProduct,ScientificGrid,Verification
from earth_echo.storage.products import publish

PATH='bodc/gebco/global/gebco_2026/'
FILES={'elevation':PATH+'ice_surface_elevation/netcdf/GEBCO_2026.nc','tid':PATH+'type_identifier_grid/netcdf/gebco_2026_tid.nc'}
DOC='https://www.gebco.net/data-products-gridded-bathymetry-data/gebco2026-grid'
TID={'0':'Tierra','10':'Ecosonda monohaz','11':'Ecosonda multihaz','12':'Sísmica','13':'Sondeo aislado','14':'Sondeo ENC','15':'Lidar batimétrico','16':'Sensor óptico','17':'Mediciones directas combinadas',
    '40':'Predicción guiada por gravedad satelital','41':'Interpolación algorítmica','42':'Contornos batimétricos de cartas','43':'Contornos ENC','44':'Fuentes medidas/derivadas con interpolación guiada por gravedad',
    '45':'Gravedad aérea','46':'Calado estimado de iceberg','47':'Flotador Argo encallado','48':'Registrador en animal','70':'Malla preexistente de fuentes mixtas','71':'Fuente desconocida','72':'Puntos de control en baja cobertura'}

def decode_ascii(raw: bytes,variable: str):
    text=raw.decode();body=text.split('---------------------------------------------\n',1)[1]
    match=re.match(rf'{variable}\.{variable}\[(\d+)\]\[(\d+)\]\n',body)
    if not match: raise ValueError('Unknown OPeNDAP grid encoding')
    height,width=map(int,match.groups());matrix=[]
    for row in range(height):
        found=re.search(rf'^\[{row}\], (.+)$',body,re.M)
        if not found: raise ValueError('Missing DAP row')
        cells=[int(v.strip()) for v in found[1].split(',')]
        if len(cells)!=width: raise ValueError('Wrong DAP width')
        matrix.append(cells)
    def axis(name,count):
        a=re.search(rf'{variable}\.{name}\[{count}\]\n([^\n]+)',body)
        if not a: raise ValueError('Missing DAP coordinates')
        values=[float(v) for v in a[1].split(',')]
        if len(values)!=count: raise ValueError('Wrong DAP axis length')
        return values
    return matrix,axis('lat',height),axis('lon',width)

def fetch_gebco(now: datetime):
    # 1° Caribbean window, native 15 arc-second cells (first measured at stride 8).
    row0,row1,col0,col1=25680,25919,22800,23039
    archive={};arrays={};probes=[]
    for variable,path in FILES.items():
        base='https://dap.ceda.ac.uk/thredds/dodsC/'+path
        url=base+'.ascii?'+quote(f'{variable}[{row0}:1:{row1}][{col0}:1:{col1}]',safe='')
        raw,_=download(url,max_bytes=800_000);das,_=download(base+'.das',max_bytes=100_000)
        if variable=='elevation' and ('height_above_mean_sea_level' not in das.decode() or 'GEBCO_2026' not in das.decode()): raise ValueError('Unknown GEBCO datum/version')
        matrix,lats,lons=decode_ascii(raw,variable);arrays[variable]=(matrix,lats,lons)
        source=RangeSource('https://dap.ceda.ac.uk/'+path,max_requests=16,max_bytes=2_000_000)
        if source.read_at(0,4)==b'CDF\x01':
            ds=ClassicNetCdf(source.read_at(0,65536))
            def scalar(name,indices):
                var=ds.variables[name];index=0
                for dimension,position in zip(var['dimensions'],indices): index=index*ds.dimensions[dimension]+position
                code,size={1:('b',1),6:('d',8)}[var['type']]
                return struct.unpack('>'+code,source.read_at(var['offset']+index*size,size))[0]
            native=int(scalar(variable,[row0,col0]));lat=scalar('lat',[row0]);lon=scalar('lon',[col0])
        else:
            with source.open() as stream,h5py.File(stream,'r') as ds:
                native=int(ds[variable][row0,col0])
                lat=float(ds['lat'][row0]);lon=float(ds['lon'][col0])
                if variable=='elevation' and bytes(ds[variable].attrs['units']).decode()!='m': raise ValueError('Unknown height unit')
        if native!=matrix[0][0] or abs(lat-lats[0])>1e-8 or abs(lon-lons[0])>1e-8: raise ValueError('Native binary scalar/coordinates disagree with DAP')
        probes.append((variable,native))
        archive[variable]={'url':url,'ascii':raw.decode(),'metadata_url':base+'.das','metadata':das.decode(),'native_check':json.loads(source.archive({'row':row0,'column':col0,'value':native}))}
    matrix,lats,lons=arrays['elevation'];quality,qlats,qlons=arrays['tid']
    if qlats!=lats or qlons!=lons or len(matrix)!=240 or len(matrix[0])!=240: raise ValueError('TID grid is not aligned with elevation')
    values=[float(v) for row in reversed(matrix) for v in row];q=[v for row in reversed(quality) for v in row]
    if any(str(v) not in TID for v in q): raise ValueError('New TID class requires a documented interpretation')
    grid=ScientificGrid(width=240,height=240,west=-85,east=-84,south=17,north=18,longitudes=lons,latitudes=list(reversed(lats)),values=values,minimum=min(values),maximum=max(values),missing_cells=0,
        resolution='Nativa 15 segundos de arco, 240×240 centros en 1°',sampling='Recorte nativo OPeNDAP sin reducción ni promedio; filas reordenadas norte→sur. La prueba inicial a stride 8 se amplió después de medir 7.854 bytes.',
        quality_mask='TID por celda conserva tipo de fuente, no exactitud ni confianza. GEBCO no declara nodata en este recorte; cero es elevación válida. Resolución no implica medición directa.',quality_values=q,quality_legend={str(v):TID[str(v)] for v in sorted(set(q))})
    raw=json.dumps(archive,ensure_ascii=False,separators=(',',':')).encode();sha=hashlib.sha256(raw).hexdigest()
    return publish(ScientificProduct(id='d31-gebco-caribe',source_id='D31',title='Batimetría y TID GEBCO · Caribe',collection_id='GEBCO_2026 ice surface elevation + TID',product_version='2026; DOI 10.5285/4f68d5c7-45eb-f999-e063-7086abc036fa',variable='height_above_mean_sea_level',unit='m sobre nivel medio del mar',native_unit='m, positivo hacia arriba',kind='static_context',representation='field',
        retrieved_at=now,ingested_at=now,original_url=archive['elevation']['url'],license_url=DOC,attribution='GEBCO Bathymetric Compilation Group 2026 / BODC / Nippon Foundation-GEBCO Seabed 2030',checksum_sha256=sha,byte_size=len(raw),raw_file=f'd31-gebco-caribe/assets/{sha}.json',
        coverage='Recorte del Caribe 85–84° O, 17–18° N; original nominal mundial no descargado completo.',cadence_seconds=2592000,method_version='gebco-native-dap-tid-v1',
        limitation='Contexto estático, no medición actual ni profundidad de inundación. Altura negativa indica fondo marino bajo nivel medio del mar; no se invierte el signo sin conversión. WGS84 horizontal; datum vertical nominal EPSG:5831/MSL, con heterogeneidad conocida de fuentes someras según GEBCO. No apto para navegación o seguridad marítima. Se conservan ASCII numérico nativo, metadatos y bloques HDF5 de comprobación, sin descargar los 7,5 GB.',grid=grid,
        verification=Verification(method='Elevación, TID y coordenadas ASCII cotejados con lectura binaria HDF5 (elevación) y struct/NetCDF clásico (TID) de archivos mundiales mediante rangos limitados',original_url='https://dap.ceda.ac.uk/'+FILES['elevation'],checked_at=now,expected=str(probes),actual=str([(k,arrays[k][0][0][0]) for k in FILES]),passed=True)),raw,'.json')
