"""FAO RAMSES public survey reports, including reported absence of desert locust."""
import hashlib
import json
import math
from datetime import datetime,timedelta,timezone
from urllib.parse import urlencode
from earth_echo.connectors.http import download
from earth_echo.contracts.products import ScientificProduct,ProductSample,Verification
from earth_echo.storage.products import publish
from earth_echo.science.paths import path_extent

BASE='https://services5.arcgis.com/sjP4Ugu5s0dZWLjd/arcgis/rest/services/Ramses_Observations_Dashboard_View/FeatureServer/0'
ITEM='https://hqfao.maps.arcgis.com/sharing/rest/content/items/ed8228a11a2547178cdf4ab002464efb?f=json'
FIELDS='OBJECTID,GlobalID,Obs_Date,Observation_Time,Country,RAMSES_Locust_Type,Locust_Presence,Locust_Phase,Density_Description,Density_Unit,Observation_Confirmation,Observation_Reliability,Latitude,Longitude,Data_Collection_Method'

def load_json(url):
    raw,_=download(url,max_bytes=1_000_000);data=json.loads(raw)
    if 'error' in data: raise ValueError('RAMSES query rejected')
    return data

def decode_reports(data):
    if data.get('type')!='FeatureCollection': raise ValueError('Expected survey GeoJSON')
    reports=[]
    for feature in data['features']:
        a=feature['properties'];g=feature.get('geometry')
        if g is None: lon=lat=None
        elif g.get('type')=='Point':
            lon,lat=g['coordinates'][:2]
            if not (-180<=lon<=180 and -90<=lat<=90) or not all(math.isfinite(v) for v in (lon,lat)):
                lon=lat=None
            elif a.get('Longitude') is None or a.get('Latitude') is None or not math.isclose(lon,a['Longitude'],abs_tol=1e-6) or not math.isclose(lat,a['Latitude'],abs_tol=1e-6):
                raise ValueError('GeoJSON coordinates disagree with native longitude/latitude')
        else: raise ValueError('Unexpected survey geometry')
        time=datetime.fromtimestamp(a['Obs_Date']/1000,timezone.utc) if a.get('Obs_Date') is not None else None
        category=a.get('RAMSES_Locust_Type')
        if category not in {'ADULT','HOPPER','BAND','SWARM','NO LOCUST',None}: raise ValueError('New RAMSES category needs interpretation')
        attributes={k:None if v is None else str(v) for k,v in a.items()}
        attributes.update(nombre=f'{category or "No informado"} · {a.get("Country") or "No informado"}',species='Schistocerca gregaria (ámbito del Locust Hub FAO)',
            temporal_definition='Obs_Date del proveedor, campos declarados UTC; Observation_Time se conserva como texto sin combinarlo como hora UTC no verificada.')
        reports.append(ProductSample(id=f'ramses-{a["OBJECTID"]}',time=time,longitude=lon,latitude=lat,value=None,category=category,
            quality=f'Confirmación: {a.get("Observation_Confirmation")}; fiabilidad: {a.get("Observation_Reliability")}. Son etiquetas del proveedor, no probabilidad. '+('Coordenadas inválidas/ausentes: sin pin.' if lon is None else ''),attributes=attributes))
    if len({s.id for s in reports})!=len(reports): raise ValueError('Duplicate survey id')
    return reports

def fetch_locusts(now: datetime):
    metadata=load_json(BASE+'?f=json');item=load_json(ITEM)
    if metadata.get('serviceItemId')!='ed8228a11a2547178cdf4ab002464efb' or metadata.get('dateFieldsTimeReference',{}).get('timeZone')!='UTC' or item.get('owner')!='faodlis_hqfao':
        raise ValueError('RAMSES identity or time zone changed')
    params={'where':f"Obs_Date >= TIMESTAMP '{(now-timedelta(days=7)):%Y-%m-%d %H:%M:%S}' AND Obs_Date <= TIMESTAMP '{now:%Y-%m-%d %H:%M:%S}'",'outFields':FIELDS,'returnGeometry':'true','outSR':4326,
        'orderByFields':'Obs_Date DESC,OBJECTID DESC','resultRecordCount':200,'f':'geojson'}
    url=BASE+'/query?'+urlencode(params);data=load_json(url);samples=decode_reports(data)
    # A separate Esri JSON query verifies id, native date, category and geometry.
    if samples:
        oid=samples[0].attributes['OBJECTID'];check_url=BASE+'/query?'+urlencode({'objectIds':oid,'outFields':FIELDS,'returnGeometry':'true','outSR':4326,'f':'json'})
        check=load_json(check_url);reference=check['features'][0]
        if reference['attributes']!=data['features'][0]['properties']: raise ValueError('Independent native attributes differ from GeoJSON')
        coords=data['features'][0]['geometry']['coordinates']
        if not math.isclose(reference['geometry']['x'],coords[0],abs_tol=1e-6) or not math.isclose(reference['geometry']['y'],coords[1],abs_tol=1e-6): raise ValueError('Independent native geometry differs')
    else:
        oid='0';check_url=BASE+'/query?'+urlencode({'where':params['where'],'returnCountOnly':'true','f':'json'})
        check=load_json(check_url)
        if check.get('count')!=0: raise ValueError('Empty GeoJSON disagrees with independent count')
    raw=json.dumps({'source_metadata':metadata,'item_metadata':item,'query_url':url,'geojson':data,'independent_check':check},ensure_ascii=False,separators=(',',':')).encode();sha=hashlib.sha256(raw).hexdigest()
    # Query end changes per retrieval; fingerprint all returned reports + stable product identity.
    science_sha=hashlib.sha256(json.dumps({'geojson':data,'item':item['id'],'fields':FIELDS},sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return publish(ScientificProduct(id='d19-desert-locust-surveys',source_id='D19',title='Langosta del desierto · reportes RAMSES',collection_id='Ramses_Observations_Dashboard_View/0',product_version='Item '+item['id']+'; modified='+str(item.get('modified')),variable='reported_desert_locust_category',unit='categoría reportada',native_unit='RAMSES_Locust_Type',
        kind='observation',representation='points',observed_at=min((s.time for s in samples if s.time),default=None),observation_end=max((s.time for s in samples if s.time),default=None),retrieved_at=now,ingested_at=now,
        original_url=BASE+'/query',license_url='https://www.fao.org/contact-us/terms/db-terms-of-use/en',attribution='FAO · DLIS/RAMSES Locust Hub y servicios nacionales originales. Fecha de acceso en retrieved_at. Condiciones FAO; ítem sin licencia específica publicada.',
        checksum_sha256=sha,scientific_checksum_sha256=science_sha,byte_size=len(raw),raw_file=f'd19-desert-locust-surveys/assets/{sha}.json',coverage=f'Consulta de siete días, máximo 200 reportes. Muestra actual: {len(samples)} registros en '+', '.join(sorted({s.attributes['Country'] or 'No informado' for s in samples}))+'. Ámbito de langosta del desierto; no traslada el riesgo a Sudamérica.',
        extent=path_extent([[s.longitude,s.latitude] for s in samples if s.longitude is not None and s.latitude is not None]) if any(s.longitude is not None and s.latitude is not None for s in samples) else None,
        cadence_seconds=86400,method_version='fao-ramses-surveys-v1',limitation='Reportes de campo de Schistocerca gregaria, incluidos NO LOCUST/ABSENT. Cada punto es un reporte y no un enjambre detectado; no se cuenta número de individuos ni se infiere riesgo fuera del muestreo. Categorías y calidad son originales. Sin trayectoria migratoria futura, probabilidad ni reproducción inferida. Fecha reportada UTC; la hora textual no se convierte sin definición adicional. El servicio público no publica licencia específica en el ítem: se conserva esa limitación y atribución FAO.',samples=samples,
        verification=Verification(method='Primer reporte cotejado entre GeoJSON y Esri JSON por OBJECTID/atributos/geometría; si la consulta no tiene reportes, se coteja count=0 por separado. Cero reportes no acredita ausencia de la especie.',original_url=check_url,checked_at=now,expected=oid,actual=samples[0].attributes['OBJECTID'] if samples else '0',passed=True)),raw,'.json')
