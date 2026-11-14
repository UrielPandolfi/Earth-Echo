"""BasinATLAS v1 level-03 South American context, from actual HydroATLAS members."""
import hashlib
import io
import json
import struct
import math
from decimal import Decimal
from datetime import datetime
import shapefile
from pyproj import CRS
from shapely.geometry import shape, mapping
from earth_echo.science.static_geometry import prepare_static_polygon
from earth_echo.connectors.http import download
from earth_echo.connectors.zip_subset import FigshareZipSubset, ArchivedZipSubset
from earth_echo.contracts.geometry import GeoMultiPolygon, GeographicExtent
from earth_echo.contracts.products import ScientificProduct, ProductSample, ProductRegion, Verification
from earth_echo.storage.products import publish
from earth_echo.paths import repo_root

API = 'https://api.figshare.com/v2/articles/9890531'
DOC = 'https://data.hydrosheds.org/file/technical-documentation/HydroATLAS_TechDoc_v10_1.pdf'
BASE = 'BasinATLAS_v10_shp/BasinATLAS_v10_lev03'
MEMBERS = [BASE + '.' + ext for ext in ('shp', 'shx', 'dbf', 'prj')]
FIELDS = ('HYBAS_ID', 'NEXT_DOWN', 'NEXT_SINK', 'MAIN_BAS', 'SUB_AREA', 'UP_AREA', 'PFAF_ID', 'ENDO', 'COAST')


def native_dbf_area(dbf, index):
    """Independent dBASE header/field-offset decode; no shapefile library."""
    count, header_length, record_length = struct.unpack_from('<IHH', dbf, 4)
    if index >= count or len(dbf) < header_length + count * record_length:
        raise ValueError('Truncated native DBF')
    offset = 1
    for pos in range(32, header_length-1, 32):
        field = dbf[pos:pos+32]
        name = field[:11].split(b'\0')[0].decode('ascii')
        size = field[16]
        if name == 'SUB_AREA':
            start = header_length + index*record_length + offset
            return Decimal(dbf[start:start+size].decode('ascii').strip())
        offset += size
    raise ValueError('Native SUB_AREA field absent')


def decode_basins(members):
    if not CRS.from_wkt(members[BASE+'.prj'].decode()).equals(CRS.from_epsg(4326), ignore_axis_order=True):
        raise ValueError('BasinATLAS geometry is not WGS84')
    reader = shapefile.Reader(shp=io.BytesIO(members[BASE+'.shp']), shx=io.BytesIO(members[BASE+'.shx']), dbf=io.BytesIO(members[BASE+'.dbf']))
    samples = []; regions = []; native_vertices = display_vertices = 0
    for index, record in enumerate(reader.iterRecords()):
        row = record.as_dict()
        if not str(row['HYBAS_ID']).startswith('603'):
            continue
        area = native_dbf_area(members[BASE+'.dbf'], index)
        if Decimal(str(row['SUB_AREA'])) != area or area <= 0:
            raise ValueError('Independent native DBF area disagrees')
        original = reader.shape(index)
        geometry = shape(original.__geo_interface__)
        geometry,valid,quality = prepare_static_polygon(geometry)
        native_vertices += len(original.points)
        sid = str(row['HYBAS_ID'])
        extent = GeographicExtent(west=original.bbox[0], south=original.bbox[1], east=original.bbox[2], north=original.bbox[3], crosses_antimeridian=False)
        # Cross-check native SHX offset and SHP bbox, using binary headers directly.
        shx = members[BASE+'.shx']; shp = members[BASE+'.shp']
        offset = struct.unpack_from('>I', shx, 100+index*8)[0]*2
        if tuple(struct.unpack_from('<4d', shp, offset+12)) != tuple(original.bbox):
            raise ValueError('Independent SHP/SHX georeferencing disagrees')
        points_bbox = (min(p[0] for p in original.points), min(p[1] for p in original.points), max(p[0] for p in original.points), max(p[1] for p in original.points))
        if not all(math.isclose(a,b,abs_tol=1e-10,rel_tol=0) for a,b in zip(points_bbox,original.bbox)):
            raise ValueError('Independent SHP/SHX bbox disagrees with native coordinates')
        samples.append(ProductSample(id=sid, value=float(area), quality='Contexto estático; SUB_AREA nativo km², sin probabilidad ni fecha de observación por polígono. '+quality,
            attributes={**{k:str(row[k]) for k in FIELDS}, 'COAST_definicion':'1: agrupación de cuencas costeras, no una sola cuenca',
                'ENDO_definicion':'2: sumidero endorreico; NEXT_DOWN puede ser enlace virtual',
                'UP_AREA_unidad':'km²; área conectada aguas arriba, sin conexiones virtuales endorreicas',
                'resolucion':'Base HydroSHEDS 15 segundos de arco; jerarquía Pfafstetter nivel 03',
                'geometria_visual':quality+'; simplificación topológica 0.01°; SUB_AREA original inalterada; original disponible'}))
        if not valid:
            continue
        reduced = geometry.simplify(.01, preserve_topology=True)
        data = mapping(reduced)
        coords = [data['coordinates']] if data['type'] == 'Polygon' else data['coordinates']
        display = GeoMultiPolygon(type='MultiPolygon', coordinates=coords)
        display_vertices += sum(len(ring) for poly in display.coordinates for ring in poly)
        regions.append(ProductRegion(id=sid, name=f'Cuenca {sid}', sample_id=sid, geometry=display, extent=extent,
            quality=quality+'; delimitación estática, simplificada 0.01°. No es región inundada.'))
    if not samples:
        raise ValueError('No South American level-03 basin in actual archive')
    return samples, regions, native_vertices, display_vertices


def fetch_hydroatlas(now: datetime):
    meta_raw, _ = download(API, max_bytes=100_000)
    meta = json.loads(meta_raw)
    file = next(f for f in meta['files'] if f['id'] == 20087237 and f['name'] == 'BasinATLAS_Data_v10_shp.zip')
    cache = repo_root()/'.cache/hydroatlas-native.zipranges.json'
    raw = cache.read_bytes() if cache.exists() else None
    if raw and json.loads(raw)['file'] != file:
        raw = None
    if raw is None:
        subset = FigshareZipSubset(file)
        members = subset.members(MEMBERS)
        raw = subset.archive({'article_id':meta['id'], 'article_version':meta['version'], 'doi':meta['doi'], 'members':MEMBERS})
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(raw)
    samples, regions, native, display = decode_basins(ArchivedZipSubset(raw).members(MEMBERS))
    # Verify persisted subset independently replays the compressed ZIP (CRC32).
    replay = ArchivedZipSubset(raw).members(MEMBERS)
    if len(replay) != 4:
        raise ValueError('Retained HydroATLAS ZIP subset cannot reproduce original members')
    sha = hashlib.sha256(raw).hexdigest()
    extent = GeographicExtent(west=min(r.extent.west for r in regions), east=max(r.extent.east for r in regions), south=min(r.extent.south for r in regions), north=max(r.extent.north for r in regions), crosses_antimeridian=False)
    return publish(ScientificProduct(id='d32-basins-south-america', source_id='D32', title='HydroATLAS · cuencas de Sudamérica',
        collection_id='BasinATLAS v10 lev03 · Figshare 9890531/file 20087237', product_version=f'BasinATLAS 1.0; artículo v{meta["version"]}',
        variable='SUB_AREA', unit='km²', native_unit='km²', kind='static_context', representation='regions',
        retrieved_at=now, ingested_at=now, original_url=file['download_url'], license_url='https://creativecommons.org/licenses/by/4.0/',
        attribution='Linke et al. (2019), HydroATLAS / HydroSHEDS; doi:10.1038/s41597-019-0300-6',
        checksum_sha256=sha, byte_size=len(raw), raw_file=f'd32-basins-south-america/assets/{sha}.json', extent=extent,
        coverage=f'{len(samples)} unidades de nivel 03 con HYBAS_ID que comienza 603, Sudamérica; {len(regions)} geometrías válidas dibujadas. SUB_AREA/UP_AREA/topología nativos; no todos los atributos interpretados.',
        cadence_seconds=2592000, method_version='basinatlas-v10-level03-sa-v2',
        limitation=f'Contexto estático: no caudal, almacenamiento de agua ni inundación. COAST=1 agrupa cuencas costeras y ENDO conserva conexiones virtuales. Época específica del polígono no declarada: fecha nula. Base 15 arcsec, nivel 03; simplificación topológica 0.01° de {native} vértices nativos a {display} dibujados; áreas km² originales. Anillos nativos que se tocan se normalizan sólo para visualizar mediante GEOS make_valid(structure), con diferencia relativa de área planar <=1e-10 y bbox <=1e-10°; calidad por cuenca lo declara. {len(samples)-len(regions)} geometrías fuera de ese criterio permanecen sin dibujo. Se retienen cuatro miembros nativos del ZIP ({sum(len(v) for v in ArchivedZipSubset(raw).ranges.values())} bytes de rangos), no la colección de {file["size"]} bytes. Los restantes atributos DBF quedan en el original sin asignarles unidades o interpretación. CRC32 de miembros verificado; MD5 de la colección completa no comprobado porque no se descargó completa.',
        samples=samples, regions=regions,
        verification=Verification(method='SUB_AREA de todos los registros publicados leído también con offsets dBASE/Decimal; bbox de cada SHP cotejada contra SHX binario; PRJ WGS84 comprobado, CRC32 y reproducción offline de los cuatro miembros ZIP',
            original_url=DOC, checked_at=now, expected=f'{len(samples)} áreas/bbox nativas coincidentes y 4 miembros reproducibles', actual=f'{len(samples)} áreas/bbox nativas coincidentes y 4 miembros reproducibles', passed=True)), raw, '.json')
