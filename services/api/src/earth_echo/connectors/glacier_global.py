"""RGI7 native representative points/areas, with all original attributes retained."""
import csv
import hashlib
import io
import math
import zipfile
from collections import Counter,defaultdict
from datetime import datetime
from decimal import Decimal
from earth_echo.connectors.http import download
from earth_echo.connectors.glacier_inventory import BASE,G_URL
from earth_echo.connectors.scientific_archive import pack_files
from earth_echo.contracts.products import ScientificProduct,ProductSample,Verification
from earth_echo.science.paths import path_extent
from earth_echo.storage.products import publish

KEY='d26-rgi7-global-large-glaciers'
G_NAME='RGI2000-v7.0-G-global-attributes.csv'
COMPARISON='https://rgidata.org/user_guide/_downloads/2b96e230cfac68c479a609f64e01cbc6/RGI2000-v7.0-G-comparison-rgi6.csv'
DOC='https://rgidata.org/user_guide/regions/overview.html'
MIN_AREA=Decimal('50')
REGION_IDS=frozenset(f'{i:02}' for i in range(1,20))


def csv_rows(raw):
    return csv.DictReader(io.TextIOWrapper(io.BytesIO(raw),encoding='utf-8-sig',newline=''),strict=True)


def decode_global(raw,reference):
    reader=csv_rows(raw)
    if not {'rgi_id','o1region','cenlon','cenlat','area_km2','src_date'}<=set(reader.fieldnames or []) or not raw.endswith(b'\n'):
        raise ValueError('Incomplete/unexpected RGI7 global CSV')
    identifiers=set();counts=Counter();areas=defaultdict(Decimal);selected_counts=Counter();samples=[]
    for row in reader:
        if None in row or any(v is None for v in row.values()):raise ValueError('Incomplete RGI7 CSV record')
        sid,region=row['rgi_id'],row['o1region']
        if region not in REGION_IDS or not sid.startswith('RGI2000-v7.0-G-'+region+'-') or sid in identifiers:
            raise ValueError('Duplicate ID or unexpected RGI7 edition/region')
        identifiers.add(sid);counts[region]+=1
        area=Decimal(row['area_km2'])
        lon,lat=float(row['cenlon']),float(row['cenlat'])
        if not area.is_finite() or area<0 or not(math.isfinite(lon) and math.isfinite(lat) and -180<=lon<=180 and -90<=lat<=90):
            raise ValueError('Missing/invalid RGI7 area or native representative point; no zero fill')
        areas[region]+=area
        if area<MIN_AREA:continue
        selected_counts[region]+=1
        samples.append(ProductSample(id=sid,longitude=lon,latitude=lat,value=float(area),
            quality='Contexto estático RGI7. Punto representativo dentro del glaciar definido por el proveedor, no centroide, celda de ráster ni observación actual. Área km² nativa; sin probabilidad.',
            attributes={'nombre':row.get('glac_name') or sid,**row,
                'src_date_definicion':'Fecha/época de la imagen fuente conservada literalmente; sin zona UTC acreditada, no recuperación ni fecha de desastre.',
                'geometria':'cenlon/cenlat nativos, no centroide. Huella RGI7 no descargada.',
                'seleccion':'Área nativa ≥50 km² para una vista mundial acotada. Los glaciares menores siguen en el CSV original completo; no son datos ausentes ni se selecciona por peligro.',
                'otros_atributos':'Conservados como texto nativo; no se interpretan códigos como probabilidades o estado saludable.'}))
    published={row['Region']:row for row in csv_rows(reference)}
    if set(published)!={*(f'{i:02}' for i in range(1,21)),'Global'}:
        raise ValueError('Unexpected official RGI comparison table')
    # Independent published aggregates, not inferred from our selected display.
    for region in published:
        count=sum(counts.values()) if region=='Global' else counts[region]
        area=sum(areas.values()) if region=='Global' else areas[region]
        if count!=int(published[region]['Count RGI 7.0']) or abs(area-Decimal(published[region]['Area RGI 7.0']))>Decimal('.5'):
            raise ValueError('RGI7 native count/area disagrees with independent published region')
    if sum(counts.values())!=274531 or not 1<=len(samples)<=3000:
        raise ValueError('Unexpected RGI7 global edition or display budget')
    return samples,{'native_records':sum(counts.values()),'native_area_km2':str(sum(areas.values())),
        'region_counts':dict(sorted(counts.items())),'selected_region_counts':dict(sorted(selected_counts.items()))}


def product_from_originals(raw,reference,now):
    samples,statistics=decode_global(raw,reference)
    files={G_NAME:raw,'RGI2000-v7.0-G-comparison-rgi6.csv':reference}
    assets={name:{'url':G_URL if name==G_NAME else COMPARISON,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for name,b in files.items()}
    archive=pack_files(files,{'schema_version':'1','assets':assets,'statistics':statistics},compression=zipfile.ZIP_DEFLATED)
    sha=hashlib.sha256(archive).hexdigest()
    product=ScientificProduct(id=KEY,source_id='D26',title='RGI 7 · glaciares ≥50 km² · contexto mundial',
        collection_id='RGI2000-v7.0-G global attributes / OGGM mirror / Area≥50 km²',product_version='RGI 7.0 (2023), producto G',
        variable='glacier_area',unit='km²',native_unit='km²',kind='static_context',representation='points',
        observed_at=None,issued_at=None,issue_time_basis='Inventario con época objetivo alrededor de 2000; src_date nativo por glaciar conservado como texto. Fechas sin zona no se convierten en instantes UTC.',
        retrieved_at=now,ingested_at=now,original_url=G_URL,license_url='https://rgidata.org/user_guide/01_introduction.html',
        attribution='RGI 7.0 Consortium (2023), Randolph Glacier Inventory, doi:10.5067/F6JMOVY5NAVZ, CC BY 4.0; distribución académica OGGM / Universität Bremen. Subconjunto cartográfico global de glaciares ≥50 km².',
        checksum_sha256=sha,byte_size=len(archive),raw_file=f'shared/{sha}.zip',extent=path_extent([[s.longitude,s.latitude] for s in samples]),
        coverage=f'{len(samples)} puntos representativos nativos de glaciares ≥50 km² en {len(statistics["selected_region_counts"])} regiones de inventario. CSV completo conserva 274531 glaciares de 19 regiones; excluye capas de hielo de Groenlandia/Antártida continental. Selección, no todos los glaciares dibujados.',
        cadence_seconds=2592000,method_version='rgi7-global-large-glaciers-native-points-v1',samples=samples,
        limitation='Contexto mundial de áreas y puntos representativos RGI7, no huellas poligonales, eventos ni observaciones de hoy. El umbral ≥50 km² limita la vista, no mide peligro; glaciares menores quedan en el original completo, no se convierten en cero o ausentes. Hay 19 regiones en el original y 16 con glaciares que cumplen la selección. Las grandes capas de hielo y Antártida continental están excluidas. Épocas fuente variables alrededor de 2000; no se inventa UTC desde fechas sin zona. Los puntos son nativos del proveedor, no centroides calculados ni celdas rasterizadas. No indica retroceso medido, lagunas, diques, GLOF o predicción. La muestra RGI7 de Alaska y los contornos RGI6 de Patagonia permanecen separados; no se suman entre versiones para inferir cambio. Los 274.531 registros y todos sus atributos originales siguen descargables en ZIP sin pérdida; no se descargaron geometrías mundiales. Huellas RGI7 oficiales aún requieren el acceso correspondiente.',
        verification=Verification(method='Conteos exactos y áreas sumadas con Decimal por cada región y a escala global, cotejados con CSV de estadísticas independiente publicado por RGI. Las áreas publicadas se redondean a km² enteros: tolerancia 0,5 km². IDs únicos, edición, coordenadas WGS84 y dominio de áreas verificados en todos los registros. Selección no altera puntos/áreas originales; SHA y CRC32 del activo completo conservados.',
            original_url=COMPARISON,checked_at=now,expected='274531 registros de 19 regiones; áreas publicadas de cada región y 706744 km² globales, redondeados',
            actual=f'{statistics["native_records"]} registros; {statistics["native_area_km2"]} km² nativos globales; {len(samples)} puntos en la selección; todos los cotejos regionales pasaron',passed=True))
    return product,archive


def fetch_glacier_global(now:datetime):
    listing,_=download(BASE,max_bytes=100_000)
    if G_NAME not in listing.decode(errors='replace'):raise ValueError('RGI7 public attribute link missing')
    raw,_=download(G_URL,max_bytes=80_000_000)
    reference,_=download(COMPARISON,max_bytes=50_000)
    product,archive=product_from_originals(raw,reference,now)
    return publish(product,archive,'.zip')
