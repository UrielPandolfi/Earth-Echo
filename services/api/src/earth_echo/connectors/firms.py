"""Public NOAA-20 VIIRS C2 thermal-anomaly detections, not ignition forecasts."""
import base64
import csv
import hashlib
import io
import json
import math
from datetime import datetime, timezone
from decimal import Decimal
from zipfile import ZipFile
import shapefile
from pyproj import CRS
from earth_echo.connectors.http import download
from earth_echo.contracts.products import ScientificProduct, ProductSample, Verification
from earth_echo.science.paths import path_extent
from earth_echo.storage.products import publish

HOST = 'https://firms.modaps.eosdis.nasa.gov'
INDEX = HOST+'/api/active_fire_files/all?format=json'
DOC = HOST+'/content/descriptions/FIRMS_VIIRS_Firehotspots.html'


def decode_csv(raw):
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    required = {'latitude','longitude','frp','acq_date','acq_time','confidence','satellite','version','bright_ti4','bright_ti5','scan','track','daynight'}
    if not required <= set(reader.fieldnames or []):
        raise ValueError('Expected FIRMS scientific CSV, not login/error HTML')
    samples = {}; rows = []
    for row in reader:
        if len(rows)>=25_000 or None in row or any(v is None for v in row.values()):
            raise ValueError('FIRMS exceeds 25,000 records or contains a truncated row')
        if row['satellite']!='N20' or row['confidence'] not in {'low','nominal','high','l','n','h'} or not row['version'].startswith('2.0'):
            raise ValueError('Unexpected VIIRS satellite, collection or native quality')
        longitude, latitude = float(row['longitude']),float(row['latitude'])
        stamp = datetime.strptime(row['acq_date']+row['acq_time'].zfill(4),'%Y-%m-%d%H%M').replace(tzinfo=timezone.utc)
        if not (-180<=longitude<=180 and -90<=latitude<=90):
            raise ValueError('Invalid native VIIRS coordinate')
        value = None if row['frp'].strip() in {'','-999','-999.0'} else float(Decimal(row['frp']))
        if value is not None and (not math.isfinite(value) or value<0):
            raise ValueError('Invalid FRP; no silent clipping')
        identity = '|'.join([row['satellite'],stamp.isoformat(),str(Decimal(row['longitude']).normalize()),str(Decimal(row['latitude']).normalize())])
        sid = 'n20-'+hashlib.sha256(identity.encode()).hexdigest()[:20]
        eligible = row['confidence'] not in {'low','l'} and value is not None
        sample = ProductSample(id=sid,time=stamp,longitude=longitude,latitude=latitude,value=value,map_eligible=eligible,
            quality=f"VIIRS confidence={row['confidence']}; nominal/high se dibujan, low o FRP ausente quedan en tabla. Confidence es clase nativa, no probabilidad. Anomalía térmica, no incidente confirmado.",
            attributes={'nombre':f"VIIRS NOAA-20 · {row['acq_date']} {row['acq_time'].zfill(4)} UTC", **row,
                'FRP_unidad':'MW, potencia radiativa integrada del píxel', 'bright_ti4_ti5_unidad':'K, temperatura de brillo I4/I5; no temperatura del aire',
                'scan_track_unidad':'km, tamaño del píxel según escaneo; centro nominal 375 m', 'mascara_visual':'nominal/high y FRP presente; no rellenar low como cero'})
        if sid in samples and samples[sid]!=sample:
            raise ValueError('Conflicting native detections at the same pixel/time')
        samples[sid]=sample; rows.append(row)
    return list(samples.values()), rows


def verify_shape(raw, rows):
    with ZipFile(io.BytesIO(raw)) as z:
        if sum(i.file_size for i in z.infolist())>15_000_000:
            raise ValueError('FIRMS expanded shapefile exceeds 15 MB')
        stem=next(n[:-4] for n in z.namelist() if n.endswith('.shp'))
        if not CRS.from_wkt(z.read(stem+'.prj').decode()).equals(CRS.from_epsg(4326),ignore_axis_order=True):
            raise ValueError('VIIRS reference geometry is not WGS84')
        reader=shapefile.Reader(shp=io.BytesIO(z.read(stem+'.shp')),shx=io.BytesIO(z.read(stem+'.shx')),dbf=io.BytesIO(z.read(stem+'.dbf')))
        native={}
        for sr in reader.iterShapeRecords():
            row=sr.record.as_dict()
            key=(row['ACQ_DATE'].isoformat(),row['ACQ_TIME'],row['LATITUDE'],row['LONGITUDE'])
            if sr.shape.points[0]!=(row['LONGITUDE'],row['LATITUDE']):
                raise ValueError('Shapefile geometry and native coordinates disagree')
            native[key]=row
        for row in rows:
            key=(row['acq_date'],row['acq_time'].zfill(4),float(row['latitude']),float(row['longitude']))
            other=native.get(key)
            if other is None or any(Decimal(str(other[k.upper()]))!=Decimal(row[k]) for k in ('frp','bright_ti4','bright_ti5','scan','track')) or any(other[k.upper()]!=row[k] for k in ('confidence','satellite','version','daynight')):
                raise ValueError('CSV/shapefile scientific values or revision disagree; previous retained')
        if len(native)!=len({(r['acq_date'],r['acq_time'].zfill(4),float(r['latitude']),float(r['longitude'])) for r in rows}):
            raise ValueError('FIRMS formats have different coverage/revisions')
        return len(rows)


def fetch_firms(now: datetime):
    index_raw,_=download(INDEX,max_bytes=1_000_000)
    index=json.loads(index_raw)
    csv_path=index['csv']['noaa20']['South America'][0]
    shp_path=index['shp']['noaa20']['South America'][0]
    for path in (csv_path,shp_path):
        if not path.startswith('/data/active_fire/noaa-20-viirs-c2/') or 'South_America_24h' not in path or '..' in path:
            raise ValueError('Official FIRMS index no longer describes selected bounded product')
    csv_raw,_=download(HOST+csv_path,max_bytes=4_000_000)
    shp_raw,_=download(HOST+shp_path,max_bytes=4_000_000)
    samples,rows=decode_csv(csv_raw)
    count=verify_shape(shp_raw,rows)
    raw=json.dumps({'csv_url':HOST+csv_path,'shapefile_url':HOST+shp_path,'csv':csv_raw.decode('utf-8-sig'),'shapefile_zip_base64':base64.b64encode(shp_raw).decode()},sort_keys=True,separators=(',',':')).encode()
    sha=hashlib.sha256(raw).hexdigest()
    return publish(ScientificProduct(id='d06-viirs-noaa20-sa',source_id='D06',title='FIRMS · anomalías térmicas NOAA-20 · Sudamérica',
        collection_id='VIIRS NOAA-20 Collection 2 · FIRMS public South_America_24h CSV/SHP',product_version='; '.join(sorted({r['version'] for r in rows})),
        variable='fire_radiative_power',unit='MW',native_unit='MW',kind='observation',representation='points',observed_at=min((s.time for s in samples),default=None),observation_end=max((s.time for s in samples),default=None),
        retrieved_at=now,ingested_at=now,original_url=HOST+csv_path,license_url='https://www.earthdata.nasa.gov/engage/open-data-services-and-software/data-and-information-policy',
        attribution='NASA LANCE FIRMS / NOAA-20 VIIRS, Collection 2 NRT',checksum_sha256=sha,byte_size=len(raw),raw_file=f'd06-viirs-noaa20-sa/assets/{sha}.json',
        coverage=f'{len(samples)} detecciones únicas del archivo regional Sudamérica 24h publicado; {sum(s.map_eligible for s in samples)} cumplen máscara visual. El intervalo real se conserva aunque el archivo publicado tenga demora. Cero registros significa archivo vacío comprobado, no ausencia regional de fuego.',extent=path_extent([[s.longitude,s.latitude] for s in samples]) if samples else None,
        cadence_seconds=10800,method_version='firms-noaa20-sa-frp-v1',
        limitation='Anomalías térmicas observadas: pueden incluir incendios, volcanes y antorchas de gas. Un píxel nominal 375 m no es perímetro quemado, incendio único, área quemada ni probabilidad de ignición. FRP integrada del píxel en MW; brillo I4/I5 en K, scan/track km. Tiempos de adquisición UTC a resolución de minuto; publicación/emisión exacta desconocida. Calidad nativa low/nominal/high: low y FRP ausente no se dibujan, conservando coordenadas y valores en tabla/original. Consulta regional de un sensor, no cobertura global ni ausencia garantizada entre pasadas. Archivo 24h puede estar atrasado: se muestran las fechas reales. No requiere MAP_KEY para esta descarga pública; API por área/fecha es otro acceso.',
        samples=samples,verification=Verification(method='Todos los píxeles CSV cotejados contra SHP/DBF publicados independientemente: coordenadas de geometría/atributo, UTC, FRP MW por Decimal, I4/I5, tamaño, satélite, clase de calidad y versión; PRJ WGS84',
            original_url=HOST+shp_path,checked_at=now,expected=f'{count} registros nativos CSV',actual=f'{count} coincidencias científicas SHP/DBF',passed=True)),raw,'.json')
