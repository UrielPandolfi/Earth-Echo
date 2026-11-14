"""Bounded GDACS cyclone CAP areas, explicitly including past/cancelled notices."""
import hashlib
import json
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
from xml.etree import ElementTree as E
from earth_echo.connectors.http import download
from earth_echo.contracts.products import ScientificProduct,ProductSample,ProductRegion,Verification
from earth_echo.science.paths import split_polygon,path_extent
from earth_echo.storage.products import publish

URL='https://www.gdacs.org/xml/rss.xml'
G='{http://www.gdacs.org}'
C='{urn:oasis:names:tc:emergency:cap:1.2}'

def decode_cap(raw: bytes,item):
    root=E.fromstring(raw)
    if root.tag!=C+'alert': raise ValueError('Expected CAP 1.2, not login HTML')
    info=root.find(C+'info')
    if info is None: raise ValueError('CAP has no information')
    parameters={p.findtext(C+'valueName'):p.findtext(C+'value') for p in info.findall(C+'parameter')}
    for key in ('eventid','version','alertlevel','datemodified'):
        if parameters.get(key)!=item.findtext(G+key): raise ValueError(f'CAP/RSS revision disagrees: {key}')
    sent=datetime.fromisoformat(root.findtext(C+'sent'))
    expires=info.findtext(C+'expires')
    sid='TC'+parameters['eventid']+'-v'+parameters['version']
    value=item.findtext(G+'alertscore')
    sample=ProductSample(id=sid,time=sent,valid_to=datetime.fromisoformat(expires) if expires else None,value=float(value) if value else None,
        quality=f"status={root.findtext(C+'status')}; msgType={root.findtext(C+'msgType')}; urgency={info.findtext(C+'urgency')}; certainty={info.findtext(C+'certainty')}",
        attributes={'nombre':root.findtext(C+'incidents'),'eventid':parameters['eventid'],'version':parameters['version'],'alertlevel':parameters['alertlevel'],
            'sent':sent.isoformat(),'expires':expires,'urgency':info.findtext(C+'urgency'),'severity':info.findtext(C+'severity'),'status':root.findtext(C+'status'),'msgType':root.findtext(C+'msgType'),
            'fromdate':parsedate_to_datetime(parameters['fromdate']).isoformat(),'todate':parsedate_to_datetime(parameters['todate']).isoformat(),
            'modified':parsedate_to_datetime(parameters['datemodified']).isoformat(),'headline':info.findtext(C+'headline'),'description':info.findtext(C+'description'),
            'references':root.findtext(C+'references'),'sender':root.findtext(C+'sender'),'CAP':item.findtext(G+'cap')})
    regions=[]
    for area in info.findall(C+'area'):
        for polygon in area.findall(C+'polygon'):
            ring=[[float(lon),float(lat)] for pair in polygon.text.split() for lat,lon in [pair.split(',')]]
            geometry=split_polygon(ring)
            regions.append(ProductRegion(id=f'{sid}-{len(regions)}',name=f"{root.findtext(C+'incidents')} · {parameters['alertlevel']} · {info.findtext(C+'urgency')}",sample_id=sid,
                geometry=geometry,extent=path_extent(ring),quality='Área CAP del proveedor; no es profundidad medida, ni toda el área está afectada. No se sustituye por epicentro, bbox o buffer local.'))
    if not regions: raise ValueError('Selected cyclone CAP has no polygon; cannot publish an invented area')
    return sample,regions

def fetch_gdacs(now: datetime):
    feed,_=download(URL,max_bytes=2_000_000)
    root=E.fromstring(feed)
    items=[i for i in root.findall('channel/item') if i.findtext(G+'eventtype')=='TC']
    items.sort(key=lambda i:parsedate_to_datetime(i.findtext(G+'datemodified')),reverse=True)
    samples=[];regions=[];caps=[]
    for item in items[:3]:
        url=item.findtext(G+'cap')
        if not url or urlparse(url).scheme!='https' or urlparse(url).hostname!='www.gdacs.org': raise ValueError('Untrusted CAP origin')
        raw,_=download(url,max_bytes=500_000)
        sample,areas=decode_cap(raw,item)
        samples.append(sample);regions.extend(areas);caps.append({'url':url,'body':raw.decode('utf-8-sig')})
    if not samples: raise ValueError('No cyclone CAP available in bounded RSS; previous retained, no demo')
    raw=json.dumps({'rss_url':URL,'rss':feed.decode('utf-8-sig'),'caps':caps},ensure_ascii=False,separators=(',',':')).encode()
    sha=hashlib.sha256(raw).hexdigest()
    return publish(ScientificProduct(id='d35-cyclone-cap-areas',source_id='D35',title='GDACS · áreas CAP de ciclones',collection_id='GDACS RSS + CAP cyclone resources',product_version='; '.join(s.id for s in samples),
        variable='gdacs_alertscore',unit='puntaje GDACS (no probabilidad)',native_unit='puntaje GDACS publicado',kind='indicator',representation='regions',issued_at=max(s.time for s in samples),
        issue_time_basis='CAP sent por mensaje; fecha del evento, modificación y expiración se conservan por registro. todate no equivale a expires.',retrieved_at=now,ingested_at=now,
        original_url=URL,license_url='https://www.gdacs.org/About/termofuse.aspx',attribution='Global Disaster Alert and Coordination System (GDACS), EC-JRC / Naciones Unidas',
        checksum_sha256=sha,byte_size=len(raw),raw_file=f'd35-cyclone-cap-areas/assets/{sha}.json',coverage=f'{len(samples)} CAP de ciclón en el RSS consultado, máximo tres. No cubre todos los avisos ni otros tipos de amenaza.',
        cadence_seconds=21600,method_version='gdacs-cyclone-cap-v1',limitation='Avisos/áreas publicados, incluidos mensajes pasados, actualizaciones y cancelaciones. Un nivel Green no declara seguridad; el puntaje no es probabilidad. Se conserva urgency/status/msgType y el área original. No es un pronóstico propio ni profundidad de inundación. La API SEARCH respondió vacía; un CAP de inundación devolvió HTML y esa capacidad queda pendiente.',
        samples=samples,regions=regions,verification=Verification(method='eventid, version, alertlevel y datemodified cotejados independientemente entre RSS y cada CAP; orden lat/lon de CAP convertido explícitamente a GeoJSON lon/lat',original_url=URL,checked_at=now,expected=str(len(samples))+' versiones RSS',actual=str(len(samples))+' coincidencias CAP',passed=True)),raw,'.json')
