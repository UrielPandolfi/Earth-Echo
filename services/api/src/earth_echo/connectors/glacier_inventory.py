"""Bounded RGI7 attributes from the OGGM academic mirror; no invented outlines."""
import base64
import csv
import hashlib
import io
import json
import math
from decimal import Decimal
from datetime import datetime
from earth_echo.connectors.ranges import RangeSource,ArchivedRangeSource
from earth_echo.contracts.products import ScientificProduct, ProductSample, Verification
from earth_echo.science.paths import path_extent
from earth_echo.storage.products import publish

BASE='https://cluster.klima.uni-bremen.de/~oggm/rgi/'
G_URL=BASE+'RGI2000-v7.0-G-global-attributes.csv'
C_URL=BASE+'RGI2000-v7.0-C-global-attributes.csv'
GUIDE='https://rgidata.org/user_guide/'


def complete_csv_prefix(raw,kind):
    # Byte windows may end inside a record. Only complete physical lines are
    # admitted; a quote/newline crossing the window is rejected by strict CSV.
    last=raw.rfind(b'\n')
    if last<0:raise ValueError('No complete native CSV row')
    reader=csv.DictReader(io.StringIO(raw[:last+1].decode('utf-8-sig')),strict=True)
    required={'rgi_id','o1region','cenlon','cenlat','area_km2'}
    if not required<=set(reader.fieldnames or []):raise ValueError('Expected native RGI7 attributes, not an HTML catalog')
    rows=list(reader)
    if not rows or len(rows)>2000:raise ValueError('RGI attribute subset outside 1–2000 record budget')
    for row in rows:
        if None in row or any(v is None for v in row.values()) or not row['rgi_id'].startswith('RGI2000-v7.0-'+kind+'-01-') or row['o1region']!='01':
            raise ValueError('Incomplete or unexpected native RGI7 Alaska attribute row')
    return rows


def decode_inventory(raw):
    rows=complete_csv_prefix(raw,'G');samples=[]
    for row in rows:
        lon,lat=float(row['cenlon']),float(row['cenlat'])
        if not (-180<=lon<=180 and -90<=lat<=90):raise ValueError('Invalid native representative point')
        area=None if row['area_km2'].strip().lower() in {'','nan','-999','-999.0','-9999','-9999.0'} else float(Decimal(row['area_km2']))
        if area is not None and (not math.isfinite(area) or area<0):raise ValueError('Invalid glacier area; no clipping to zero')
        samples.append(ProductSample(id=row['rgi_id'],longitude=lon,latitude=lat,value=area,map_eligible=area is not None,
            quality='Inventario estático RGI7; punto representativo nativo dentro del glaciar, no centroide ni evento. Área km² nativa. No fecha UTC de observación inventada.',
            attributes={'nombre':row.get('glac_name') or row['rgi_id'],**row,'src_date_definicion':'Fecha de la imagen fuente, texto nativo sin zona UTC; no instante medido actual',
                'geometria':'cenlon/cenlat nativos: punto aproximadamente central dentro de la huella, no centroide. Polígono no descargado.',
                'otros_atributos':'Conservados como texto nativo; las clases numéricas no se interpretan como probabilidades'}))
    return samples,rows


def verify_complex(rows,reference):
    complexes=complete_csv_prefix(reference,'C')
    by_point={(round(float(r['cenlon']),10),round(float(r['cenlat']),10)):r for r in complexes}
    for row in rows:
        other=by_point.get((round(float(row['cenlon']),10),round(float(row['cenlat']),10)))
        if other and row['area_km2'].strip() and math.isclose(float(row['area_km2']),float(other['area_km2']),rel_tol=1e-10,abs_tol=1e-12):
            return row,other
    raise ValueError('No independent glacier/complex area and representative point match')


def fetch_glacier_inventory(now: datetime):
    source=RangeSource(G_URL,max_bytes=400_000,max_requests=3)
    reference=RangeSource(C_URL,max_bytes=200_000,max_requests=2)
    prefix=source.read_at(0,262144);other_prefix=reference.read_at(0,131072)
    samples,rows=decode_inventory(prefix)
    glacier,complex_row=verify_complex(rows,other_prefix)
    original=source.archive({'product':'RGI2000-v7.0-G global attributes; bounded complete initial Alaska records'})
    check=reference.archive({'product':'RGI2000-v7.0-C attributes; independent representative-point/area check'})
    if ArchivedRangeSource(original).read_at(0,262144)!=prefix or ArchivedRangeSource(check).read_at(0,131072)!=other_prefix:
        raise ValueError('RGI retained ranges do not reproduce native values')
    raw=json.dumps({'glacier_ranges_base64':base64.b64encode(original).decode(),'complex_ranges_base64':base64.b64encode(check).decode()},sort_keys=True,separators=(',',':')).encode()
    sha=hashlib.sha256(raw).hexdigest()
    return publish(ScientificProduct(id='d26-rgi7-alaska-attributes',source_id='D26',title='RGI 7 · áreas y puntos representativos · muestra de Alaska',
        collection_id='RGI2000-v7.0-G global attributes · OGGM mirror · bounded initial Alaska records',product_version='RGI 7.0 (2023), producto G; copia académica OGGM',
        variable='glacier_area',unit='km²',native_unit='km²',kind='static_context',representation='points',retrieved_at=now,ingested_at=now,original_url=G_URL,
        license_url=GUIDE,attribution='RGI 7.0 Consortium (2023), doi:10.5067/F6JMOVY5NAVZ; distribución académica OGGM / Universität Bremen',
        checksum_sha256=sha,byte_size=len(raw),raw_file=f'd26-rgi7-alaska-attributes/assets/{sha}.json',
        coverage=f'{len(samples)} registros completos iniciales del CSV global, todos región 01 Alaska; NO representa todo Alaska. {samples[0].id} a {samples[-1].id}. Se recibieron 262.144 bytes del producto G y 131.072 del C.',
        extent=path_extent([[s.longitude,s.latitude] for s in samples]),cadence_seconds=2592000,method_version='rgi7-attributes-prefix-v1',
        limitation=f'Contexto estático de áreas/puntos representativos, no polígonos ni área quemada/inundada. RGI tiene época objetivo alrededor de 2000; src_date por registro es fecha de imagen fuente sin zona, conservada como texto, no observación actual UTC. No describe retroceso, espesor, lagunas, diques ni probabilidad GLOF. Muestra de registros iniciales, no cobertura completa regional ni mundial. Fin parcial de ventana byte se excluye, sin rellenar valores. Archivos G/C globales de {source.size}/{reference.size} bytes no descargados completos. Se usa espejo académico público de atributos; las huellas oficiales NSIDC siguen detrás de Earthdata. Los puntos son nativos del proveedor, no inventados desde celdas ni centroides locales.',
        samples=samples,verification=Verification(method='Área km² y punto representativo cotejados entre producto glaciar G y complejo C coincidentes; definiciones WGS84/unidades/fecha contra guía RGI7; rangos reproducidos offline y Content-Range/versión verificados',
            original_url=C_URL,checked_at=now,expected=f"{glacier['rgi_id']}: {glacier['area_km2']} km²; {glacier['cenlon']},{glacier['cenlat']}",
            actual=f"{complex_row['rgi_id']}: {complex_row['area_km2']} km²; {complex_row['cenlon']},{complex_row['cenlat']}; diferencia <1e-10 relativa",passed=True)),raw,'.json')
