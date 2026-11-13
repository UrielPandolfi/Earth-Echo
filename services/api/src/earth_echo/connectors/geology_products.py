"""GVP inventory and authorized tsunami messages, each kept within its scientific scope."""
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from earth_echo.connectors.http import download
from earth_echo.contracts.products import ScientificProduct, ProductSample, Verification
from earth_echo.storage.products import publish

GVP = 'https://webservices.volcano.si.edu/geoserver/GVP-VOTW/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=GVP-VOTW:Smithsonian_VOTW_Holocene_Volcanoes'

def parse_gvp(payload):
    if payload.get('type')!='FeatureCollection' or len(payload['features']) != payload['totalFeatures']:
        raise ValueError('Incomplete GVP inventory')
    samples = []
    for feature in payload['features']:
        prop,geo = feature['properties'],feature['geometry']
        if geo['type']!='Point': raise ValueError('Expected native volcano locations')
        lon,lat = geo['coordinates'][:2]
        if abs(lon-float(prop['Longitude']))>1e-6 or abs(lat-float(prop['Latitude']))>1e-6:
            raise ValueError('GVP geographic fields disagree')
        samples.append(ProductSample(id=str(prop['Volcano_Number']),longitude=lon,latitude=lat,value=prop.get('Elevation'),
            quality='Ubicación de inventario Holoceno; no actividad actual',attributes={'nombre':prop['Volcano_Name'],'país':prop['Country'],
            'tipo':prop['Primary_Volcano_Type'],'última_erupción_año':str(prop.get('Last_Eruption_Year','')),'época':prop['Geologic_Epoch']}))
    return samples

def fetch_gvp(now: datetime) -> str:
    url = GVP+'&outputFormat=application/json&maxFeatures=2000'
    raw,_ = download(url,max_bytes=3_000_000)
    payload = json.loads(raw)
    samples = parse_gvp(payload)
    hit_url = GVP.replace('version=1.0.0','version=2.0.0')+'&resultType=hits'
    hit_raw,_ = download(hit_url,max_bytes=20_000)
    hits = ET.fromstring(hit_raw)
    count = int(hits.attrib.get('numberMatched',hits.attrib.get('numberOfFeatures','-1')))
    if count != len(samples): raise ValueError('WFS hits disagree with inventory')
    sha = hashlib.sha256(raw).hexdigest()
    p = ScientificProduct(id='d23-holocene-inventory',source_id='D23',title='Volcanes · inventario Holoceno',collection_id='Smithsonian_VOTW_Holocene_Volcanoes',
        product_version='WFS Holocene snapshot; edición no informada en respuesta',variable='volcano_elevation',unit='m (elevación de inventario)',native_unit='m',kind='static_context',representation='points',
        retrieved_at=now,ingested_at=now,original_url=url,license_url='https://volcano.si.edu/database/webservices.cfm',attribution='Smithsonian Global Volcanism Program / Venzke · VOTW',
        checksum_sha256=sha,byte_size=len(raw),raw_file=f'd23-holocene-inventory/assets/{sha}.json',coverage='Inventario mundial de volcanes conocidos del Holoceno.',cadence_seconds=604800,
        method_version='gvp-wfs-v1',limitation='Contexto estático, no una red de sensores ni un pronóstico de erupción. Elevación y año de última erupción conservan la definición del inventario.',samples=samples,
        verification=Verification(method='Conteo contra WFS 2.0 resultType=hits y coordenadas GeoJSON contra atributos Latitude/Longitude',original_url=hit_url,checked_at=now,expected=str(count),actual=str(len(samples)),passed=True))
    return publish(p,raw,'.json')

ATOM = '{http://www.w3.org/2005/Atom}'
CAP = '{urn:oasis:names:tc:emergency:cap:1.2}'

def parse_cap(raw: bytes) -> tuple[list[ProductSample],dict]:
    root = ET.fromstring(raw)
    if root.tag != CAP+'alert': raise ValueError('Unsupported CAP namespace')
    text = lambda key:root.findtext(CAP+key)
    sent, status, msg_type = text('sent'),text('status'),text('msgType')
    if not sent or not status or not msg_type: raise ValueError('CAP missing time/status/type')
    samples=[]
    for index,info in enumerate(root.findall(CAP+'info')):
        get=lambda key:info.findtext(CAP+key)
        attributes={'emisor':text('sender'),'status':status,'msgType':msg_type,'references':text('references'),
            'evento':get('event'),'titular':get('headline'),'severidad':get('severity'),'certeza':get('certainty'),
            'vigencia_desde':get('effective'),'expira':get('expires'),'área':'; '.join(a.findtext(CAP+'areaDesc','') for a in info.findall(CAP+'area')),
            'descripción':get('description'),'time_role':'emisión del mensaje, no hora del terremoto'}
        # Keep original areas; without a valid polygon, do NOT use the earthquake epicentre as alert area.
        attributes['geometría_original_CAP'] = json.dumps([{c.tag.split('}')[-1]:c.text for c in a if c.tag in {CAP+'polygon',CAP+'circle'}} for a in info.findall(CAP+'area')])
        samples.append(ProductSample(id=f'{text("identifier")}:{index}',time=sent,valid_to=get('expires'),value=None,quality='Aviso oficial importado; puede ser informativo, prueba o cancelación, ver status/msgType',attributes=attributes))
    return samples, {'sent':sent,'status':status,'msgType':msg_type}

def fetch_tsunami(now: datetime) -> str:
    bundle=[]; samples=[]; latest=None
    for centre in ['PAAQ','PHEB']:
        url=f'https://www.tsunami.gov/events/xml/{centre}Atom.xml'
        atom_raw,_=download(url,max_bytes=200_000)
        atom=ET.fromstring(atom_raw)
        entries=atom.findall(ATOM+'entry')[-5:]
        caps=[]
        for entry in entries:
            link=next((e.attrib['href'] for e in entry.findall(ATOM+'link') if e.attrib.get('type')=='application/cap+xml'),None)
            if not link: continue
            if not link.startswith('https://www.tsunami.gov/events/'): raise ValueError('Unexpected CAP origin')
            cap_raw,_=download(link,max_bytes=200_000)
            parsed,meta=parse_cap(cap_raw)
            if datetime.fromisoformat(meta['sent'].replace('Z','+00:00')) > now: raise ValueError('CAP emission in future')
            # Independent Atom emission and CAP sent must refer to same message.
            atom_time=entry.findtext(ATOM+'updated')
            if datetime.fromisoformat(atom_time.replace('Z','+00:00')) != datetime.fromisoformat(meta['sent'].replace('Z','+00:00')):
                raise ValueError('Atom and CAP disagree on issue time')
            samples.extend(parsed); latest=max(latest or meta['sent'],meta['sent'])
            caps.append({'url':link,'xml':cap_raw.decode()})
        bundle.append({'url':url,'atom':atom_raw.decode(),'cap':caps})
    if not samples: raise ValueError('No CAP messages available; previous archive retained')
    # Deduplicate by authoritative CAP identifier across centres/updates.
    samples=list({s.id:s for s in samples}.values())
    raw=json.dumps(bundle,ensure_ascii=False).encode(); sha=hashlib.sha256(raw).hexdigest()
    p=ScientificProduct(id='d27-tsunami-messages',source_id='D27',title='Tsunami · mensajes NTWC/PTWC',collection_id='NTWC/PTWC Atom + CAP 1.2',product_version='CAP 1.2',
        variable='authorized_tsunami_message',unit='mensaje',native_unit='CAP',kind='observation',representation='table',issued_at=latest,issue_time_basis='CAP sent, cotejado con Atom updated',
        retrieved_at=now,ingested_at=now,original_url='https://www.tsunami.gov/?page=productRetrieval',license_url='https://www.tsunami.gov/',attribution='NOAA/NWS NTWC y PTWC',
        checksum_sha256=sha,byte_size=len(raw),raw_file=f'd27-tsunami-messages/assets/{sha}.json',coverage='Ámbitos de responsabilidad de NTWC/PTWC, no cobertura mundial de todas las costas.',cadence_seconds=900,
        method_version='atom-cap-v1',limitation='Mensajes oficiales con emisor, estado, actualización/cancelación y expiración. Un mensaje informativo no confirma tsunami. No se infiere llegada ni área afectada desde el epicentro. Geometrías CAP originales preservadas en cada mensaje.',samples=samples,
        verification=Verification(method='Hora de emisión cotejada entre Atom y documento CAP independiente enlazado',original_url=bundle[0]['url'],checked_at=now,expected=str(latest),actual=str(latest),passed=True))
    return publish(p,raw,'.json')
