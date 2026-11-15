"""Published USGS OAF, not probabilities inferred from the earthquake feed."""
import base64
import hashlib
import json
from datetime import datetime,timedelta,timezone
from urllib.parse import urlencode
from earth_echo.connectors.http import download
from earth_echo.contracts.products import ScientificProduct,ProductSample,Verification
from earth_echo.storage.products import publish

def _epoch(milliseconds):
    return datetime.fromtimestamp(milliseconds/1000,timezone.utc)

def describe_oaf(payload: dict, event_id: str, now: datetime) -> dict:
    """Read the published forecast. Do not redraw the model circle: its radius has no unit in the file."""
    if not isinstance(payload.get('forecast'), list) or not payload['forecast']:
        raise ValueError('OAF forecast missing')
    parameters=payload.get('model',{}).get('parameters',{})
    windows=[]
    for window in payload['forecast']:
        start,end=_epoch(window['timeStart']),_epoch(window['timeEnd'])
        if end<=start: raise ValueError('Invalid OAF window')
        bins=[]
        for item in window['bins']:
            probability=float(item['probability'])
            if not 0<=probability<=1: raise ValueError('OAF probability outside 0–1')
            bins.append({'magnitude':float(item['magnitude']),'probability':probability,'median_count':float(item['median']) if 'median' in item else None,
                'p95_minimum':float(item['p95minimum']) if 'p95minimum' in item else None,'p95_maximum':float(item['p95maximum']) if 'p95maximum' in item else None})
        state='in_progress' if start<=now<end else 'future' if start>now else 'expired'
        windows.append({'label':str(window['label']),'valid_from':start,'valid_to':end,'temporal_state':state,'bins':bins})
    windows.sort(key=lambda item: item['valid_from'])
    latitude=parameters.get('regionCenterLat'); longitude=parameters.get('regionCenterLon')
    if latitude is not None and not -90<=float(latitude)<=90: raise ValueError('OAF latitude out of range')
    if longitude is not None and not -180<=float(longitude)<=180: raise ValueError('OAF longitude out of range')
    return {'event_id':event_id,'magnitude':None if parameters.get('magMain') is None else float(parameters['magMain']),
        'latitude':None if latitude is None else float(latitude),'longitude':None if longitude is None else float(longitude),
        'model_name':str(payload.get('model',{}).get('name') or 'USGS OAF'),'region_type':parameters.get('regionType'),
        'region_radius':None if parameters.get('regionRadius') is None else float(parameters['regionRadius']),'windows':windows}


def parse_oaf(payload: dict,event_id: str) -> list[ProductSample]:
    result=[]
    for window in payload['forecast']:
        start,end=_epoch(window['timeStart']),_epoch(window['timeEnd'])
        if end<=start: raise ValueError('Invalid OAF window')
        for bin in window['bins']:
            definition=f"USGS: probabilidad de al menos una réplica de magnitud ≥{bin['magnitude']} en {window['label']}, desde {start.isoformat()} hasta {end.isoformat()}, condicionada al evento {event_id} y a la región del modelo."
            result.append(ProductSample(id=f'{event_id}-{window["timeStart"]}-m{bin["magnitude"]}',time=start,valid_to=end,
                value=float(bin['probability']),probability=float(bin['probability']),probability_definition=definition,quality='Pronóstico externo USGS OAF',
                attributes={'evento':event_id,'umbral_magnitud':str(bin['magnitude']),'ventana':window['label'],
                    'conteo_p95_mínimo':str(bin['p95minimum']),'conteo_p95_máximo':str(bin['p95maximum']),
                    'región_modelo':json.dumps({k:v for k,v in payload['model']['parameters'].items() if k.startswith('region')})}))
    return result

def fetch_oaf(now: datetime) -> str:
    query='https://earthquake.usgs.gov/fdsnws/event/1/query?'+urlencode({'format':'geojson','producttype':'oaf','starttime':(now-timedelta(days=30)).strftime('%Y-%m-%d'),'limit':1,'orderby':'time'})
    discovery,_=download(query,max_bytes=100_000)
    events=json.loads(discovery)['features']
    if not events: raise ValueError('No OAF in bounded 30 day search; previous retained')
    event=events[0]
    detail_url=event['properties']['detail']
    if not detail_url.startswith('https://earthquake.usgs.gov/'): raise ValueError('Unexpected USGS detail host')
    detail_raw,_=download(detail_url,max_bytes=2_000_000)
    details=json.loads(detail_raw)
    products=[p for p in details['properties']['products']['oaf'] if p.get('status')!='DELETE']
    product=max(products,key=lambda p:(p.get('preferredWeight',0),p['updateTime']))
    content=product['contents']['forecast.json']
    url=content['url']
    if not url.startswith('https://earthquake.usgs.gov/product/oaf/'): raise ValueError('Unexpected OAF origin')
    raw,_=download(url,max_bytes=200_000)
    digest=hashlib.sha256(raw).digest()
    if len(raw)!=int(content['length']) or base64.b64encode(digest).decode()!=content['sha256']:
        raise ValueError('OAF length/checksum disagree with independent event product manifest')
    payload=json.loads(raw)
    samples=parse_oaf(payload,event['id'])
    issued=_epoch(payload['creationTime'])
    if issued>now: raise ValueError('OAF emission in future')
    sha=digest.hex()
    p=ScientificProduct(id='d22-oaf-recent',source_id='D22',title=f'Réplicas USGS · {event["id"]}',collection_id='USGS Operational Aftershock Forecast',product_version=str(product['updateTime']),
        variable='aftershock_exceedance_probability',unit='1 (probabilidad definida)',native_unit='1',kind='forecast',representation='table',issued_at=issued,
        issue_time_basis='forecast.json creationTime; versión de producto updateTime; no se inventa inicialización',valid_from=min(s.time for s in samples),valid_to=max(s.valid_to for s in samples),
        retrieved_at=now,ingested_at=now,original_url=url,license_url='https://earthquake.usgs.gov/data/oaf/overview.php',attribution='USGS Earthquake Hazards Program',
        checksum_sha256=sha,byte_size=len(raw),raw_file=f'd22-oaf-recent/assets/{sha}.json',coverage=f'Evento {event["id"]}: región {json.dumps({k:v for k,v in payload["model"]["parameters"].items() if k.startswith("region")})}; no cobertura mundial.',
        cadence_seconds=3600,method_version='usgs-oaf-published-v1',limitation=f'Probabilidades importadas, no hora/lugar garantizados de la próxima réplica. Un solo evento reciente publicado; el producto no existe para todos los sismos. Modelo del proveedor: {payload["model"]["name"]}.',samples=samples,
        verification=Verification(method='SHA-256 y longitud del forecast contra manifiesto independiente de productos del evento USGS',original_url=detail_url,checked_at=now,expected=content['sha256'],actual=base64.b64encode(digest).decode(),passed=True))
    return publish(p,raw,'.json')
