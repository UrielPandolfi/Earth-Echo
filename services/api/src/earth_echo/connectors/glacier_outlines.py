"""Versioned historical RGI6 outlines, separate from RGI7 attributes or GLOF."""
import csv
import hashlib
import io
import math
import struct
import zipfile
from datetime import datetime
from decimal import Decimal
import shapefile
from pyproj import CRS
from shapely.geometry import shape,mapping
from earth_echo.connectors.http import download
from earth_echo.contracts.geometry import GeoMultiPolygon,GeographicExtent
from earth_echo.contracts.products import ScientificProduct,ProductSample,ProductRegion,Verification
from earth_echo.science.static_geometry import prepare_static_polygon
from earth_echo.storage.products import publish

LISTING='https://cluster.klima.uni-bremen.de/~oggm/rgi/www.glims.org/RGI/rgi60_files/'
NAME='17_rgi60_SouthernAndes'
URL=LISTING+NAME+'.zip'
DOC='https://nsidc.org/sites/default/files/rgi_tech_report_v60.pdf'
KEY='d26-rgi60-patagonia-outlines'
# A reproducible cartographic selection, not a danger/size threshold detector.
WEST,SOUTH,EAST,NORTH,MIN_AREA=-74.5,-51,-72,-48,50


def check_native_shape(shp,shx,index,original):
    """Independent ESRI binary offsets, record number, bbox, parts and coordinates."""
    offset,length=struct.unpack_from('>2I',shx,100+index*8)
    offset*=2;length*=2
    number,nwords=struct.unpack_from('>2I',shp,offset)
    if number!=index+1 or nwords*2!=length or struct.unpack_from('<I',shp,offset+8)[0]!=5:
        raise ValueError('Independent RGI SHP/SHX record differs')
    bbox=struct.unpack_from('<4d',shp,offset+12)
    parts,points=struct.unpack_from('<2I',shp,offset+44)
    if length!=44+4*parts+16*points or points!=len(original.points) or parts!=len(original.parts) or tuple(original.bbox)!=bbox:
        raise ValueError('Independent RGI shape dimensions/bounds differ')
    if tuple(original.parts)!=struct.unpack_from('<'+str(parts)+'I',shp,offset+52):
        raise ValueError('Independent RGI ring offsets differ')
    coordinates=struct.unpack_from('<'+str(2*points)+'d',shp,offset+52+4*parts)
    if any((x,y)!=(coordinates[2*i],coordinates[2*i+1]) for i,(x,y) in enumerate(original.points)):
        raise ValueError('Independent RGI native coordinates differ')
    if not all(math.isfinite(v) for v in coordinates) or any(not(-180<=x<=180 and -90<=y<=90) for x,y in original.points):
        raise ValueError('Invalid RGI WGS84 coordinates')


def decode_outlines(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        expected={NAME+'.'+ext for ext in ('shp','shx','dbf','prj')}|{NAME+'_hypso.csv'}
        if set(archive.namelist())!=expected or len(archive.infolist())!=5 or sum(i.file_size for i in archive.infolist())>60_000_000 or any(i.flag_bits&1 for i in archive.infolist()):
            raise ValueError('Unexpected RGI6 region/archive budget')
        members={name:archive.read(name) for name in archive.namelist()}  # CRC32 checked.
    if not CRS.from_wkt(members[NAME+'.prj'].decode()).equals(CRS.from_epsg(4326),ignore_axis_order=True):
        raise ValueError('RGI6 outlines are not WGS84')
    hypso={}
    for row in csv.DictReader(io.StringIO(members[NAME+'_hypso.csv'].decode(),newline=None)):
        row={k.strip():v.strip() for k,v in row.items()}
        if row['RGIId'] in hypso:raise ValueError('Duplicate RGI hypsometry identifier')
        hypso[row['RGIId']]=(row['GLIMSId'],Decimal(row['Area']))
    # Published technical report table 6: independent regional metadata check.
    if len(hypso)!=15908 or sum(v[1] for v in hypso.values())!=Decimal('29429.080'):
        raise ValueError('RGI6 region differs from published count/area')
    reader=shapefile.Reader(shp=io.BytesIO(members[NAME+'.shp']),shx=io.BytesIO(members[NAME+'.shx']),dbf=io.BytesIO(members[NAME+'.dbf']))
    if len(reader)!=15908:raise ValueError('RGI6 SHP count differs from published inventory')
    samples=[];regions=[];vertices=normalized=0
    for index,record in enumerate(reader.iterRecords()):
        row=record.as_dict();area=row['Area']
        if not row['RGIId'].startswith('RGI60-17.') or row['O1Region']!='17':
            raise ValueError('Unexpected RGI edition/region; no silent replacement')
        independent=hypso.get(row['RGIId'])
        if independent!=(row['GLIMSId'],Decimal(str(area))):raise ValueError('Independent RGI CSV/DBF area or ID disagrees')
        if not (area>=MIN_AREA and WEST<=row['CenLon']<=EAST and SOUTH<=row['CenLat']<=NORTH and row['Status']==0):
            continue
        if not math.isfinite(area):raise ValueError('Invalid native RGI area')
        original=reader.shape(index)
        check_native_shape(members[NAME+'.shp'],members[NAME+'.shx'],index,original)
        geometry=shape(original.__geo_interface__)
        if not all(math.isclose(a,b,rel_tol=0,abs_tol=1e-10) for a,b in zip(geometry.bounds,original.bbox)):
            raise ValueError('RGI native bbox differs from coordinates')
        if (row['BgnDate'],row['EndDate'])!=('20009999','20030531'):
            raise ValueError('RGI selected image epochs changed; review metadata')
        # Southern Andes selection cannot cross the antimeridian.
        if any(abs(a[0]-b[0])>180 for a,b in zip(original.points,original.points[1:])):
            raise ValueError('Unexpected antimeridian-crossing glacier; split before publishing')
        geometry,valid,quality=prepare_static_polygon(geometry)
        normalized+=int(quality.startswith('Topología normalizada'))
        vertices+=len(original.points)
        sid=row['RGIId'];name=row['Name'] or sid
        extent=GeographicExtent(west=original.bbox[0],south=original.bbox[1],east=original.bbox[2],north=original.bbox[3],crosses_antimeridian=False)
        samples.append(ProductSample(id=sid,value=area,map_eligible=valid,
            quality='Contexto estático RGI 6.0; área km² nativa, no valor de peligro. '+quality,
            attributes={'nombre':name,**{k:str(v) for k,v in row.items()},
                'Area_definicion':'km², área del inventario sobre proyección cilíndrica equivalente de esfera autálica WGS84; no recalculada desde el dibujo',
                'fechas_definicion':'BgnDate/EndDate son fechas o rangos de imágenes fuente. 9999 = mes/día desconocidos; se conserva el año sin inventar instante UTC.',
                'seleccion':'Punto representativo CenLon/CenLat en [-74.5,-72] × [-51,-48], Area≥50 km², Status=0. Contorno completo, sin recortar a esa caja.',
                'geometria_visual':quality+'; sin simplificación. RGI 6.0, no reinterpretado como RGI 7.0.',
                'otros_atributos':'Códigos nativos conservados; no equivalen a probabilidad o estado actual.'}))
        if valid:
            data=mapping(geometry)
            coords=[data['coordinates']] if data['type']=='Polygon' else data['coordinates']
            regions.append(ProductRegion(id=sid,name=name,sample_id=sid,geometry=GeoMultiPolygon(type='MultiPolygon',coordinates=coords),extent=extent,quality=quality+'; contorno histórico sin simplificación, no zona afectada.'))
    if not 1<=len(samples)<=100 or not regions:raise ValueError('RGI display selection outside bounded scope')
    return samples,regions,vertices,normalized


def fetch_glacier_outlines(now:datetime):
    listing,_=download(LISTING,max_bytes=100_000)
    if NAME+'.zip' not in listing.decode(errors='replace'):raise ValueError('Published RGI6 regional link missing')
    raw,_=download(URL,max_bytes=30_000_000)
    samples,regions,vertices,normalized=decode_outlines(raw)
    sha=hashlib.sha256(raw).hexdigest()
    extent=GeographicExtent(west=min(r.extent.west for r in regions),south=min(r.extent.south for r in regions),east=max(r.extent.east for r in regions),north=max(r.extent.north for r in regions),crosses_antimeridian=False)
    return publish(ScientificProduct(id=KEY,source_id='D26',title='Contornos glaciares históricos · RGI 6.0 · Patagonia',
        collection_id='RGI 6.0 / 17_rgi60_SouthernAndes / selección Patagonia austral Area≥50 km²',product_version='RGI 6.0 (2017); espejo académico OGGM de GLIMS',
        variable='glacier_area',unit='km²',native_unit='km²',kind='static_context',representation='regions',
        issued_at=None,issue_time_basis='Inventario histórico: BgnDate=20009999 (año 2000, mes/día desconocidos), EndDate=20030531 en la selección. Época de imágenes, no fecha UTC de observación actual o forecast.',
        retrieved_at=now,ingested_at=now,original_url=URL,license_url='https://nsidc.org/data/nsidc-0770/versions/6',
        attribution='RGI Consortium (2017), Randolph Glacier Inventory Version 6.0, doi:10.7265/4m1f-gd79; contornos distribuidos por OGGM / Universität Bremen desde GLIMS. Citar subconjunto Patagonia austral.',
        checksum_sha256=sha,byte_size=len(raw),raw_file=f'd26-rgi60-patagonia-outlines/assets/{sha}.zip',
        coverage=f'{len(samples)} glaciares de Status=0 y Area≥50 km² con punto representativo en lon [-74,5,-72], lat [-51,-48]; {len(regions)} contornos completos dibujados. Selección, no toda Patagonia. ZIP nativo contiene la región Andes del Sur completa.',extent=extent,
        cadence_seconds=2592000,method_version='rgi60-patagonia-native-outlines-v1',samples=samples,regions=regions,
        limitation='Contornos históricos de RGI 6.0 (2017), versión anterior identificada explícitamente y separada de los atributos RGI 7.0 de Alaska. Época de imágenes 2000–2003, con mes/día iniciales desconocidos. No representan área actual, retroceso medido, lagunas, estabilidad de diques, vaciamientos ni pronóstico GLOF. Selección cartográfica por punto representativo/área, no umbral de peligro; no incluye todos los glaciares del área. Se conservan límites completos, anillos interiores y áreas nativas, sin simplificar ni recortar. '+f'{normalized} contornos con contactos de anillo normalizados sólo para dibujar, conservando área planar relativa a 1e-10 y bbox a 1e-10°; originales intactos. {len(samples)-len(regions)} geometrías no calificadas quedan sin dibujo. La descarga de esta edición fija no cambia su época. RGI 7.0 sigue siendo la versión recomendada y sus huellas oficiales siguen pendientes de Earthdata.',
        verification=Verification(method='CRC32 de los cinco miembros; áreas/IDs de todos los registros comparados DBF/CSV de hipsometría. Conteo y suma regional frente a tabla 6 del informe RGI6. Cada contorno mostrado cotejado con SHP/SHX binarios independientes: bbox, índice, anillos, dimensiones y todas sus coordenadas. PRJ WGS84 comprobado.',
            original_url=DOC,checked_at=now,expected='15908 glaciares y 29429.080 km² publicados para Andes del Sur; todas las áreas/IDs y coordenadas seleccionadas coincidentes',
            actual=f'15908 glaciares y 29429.080 km² cotejados; {len(samples)} áreas/contornos seleccionados, {vertices} vértices nativos, {normalized} topologías normalizadas para dibujo',passed=True)),raw,'.zip')
