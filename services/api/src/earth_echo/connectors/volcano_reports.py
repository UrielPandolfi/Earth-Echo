"""Published preliminary GVP activity reports; inventory is never eruption prediction."""
import base64
import hashlib
import json
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as E
from earth_echo.connectors.http import download
from earth_echo.contracts.products import ScientificProduct, ProductSample, Verification
from earth_echo.storage.products import publish

RSS='https://volcano.si.edu/news/WeeklyVolcanoRSS.xml'
CAP='https://volcano.si.edu/news/WeeklyVolcanoCAP.xml'
C='{urn:oasis:names:tc:emergency:cap:1.1}'


def decode_reports(rss,cap):
    channel=E.fromstring(rss).find('channel')
    alert=E.fromstring(cap)
    if channel is None or alert.tag!=C+'alert':raise ValueError('Expected actual RSS and CAP 1.1, not HTML')
    sent=datetime.fromisoformat(alert.findtext(C+'sent'))
    channel_date=parsedate_to_datetime(channel.findtext('pubDate'))
    infos={i.findtext(C+'headline'):i for i in alert.findall(C+'info')}
    samples=[];periods=set()
    for item in channel.findall('item'):
        title=item.findtext('title') or ''
        match=re.fullmatch(r'(.+) \(([^()]+)\) - Report for (.+) - (.+)',title)
        if not match:raise ValueError('Unrecognized native GVP report title; no category invented')
        name,country,period,category=match.groups()
        info=infos.get(f'Volcanic activity report for {name} ({country}), {period}')
        if info is None:raise ValueError('RSS/CAP report period or volcano name disagrees')
        item_date=parsedate_to_datetime(item.findtext('pubDate'))
        if item_date!=sent:raise ValueError('RSS item/CAP issue times disagree')
        lat,lon=map(float,item.findtext('{http://www.georss.org/georss}point').split())
        area=info.find(C+'area');circle=area.findtext(C+'circle').split()
        cap_lat,cap_lon=map(float,circle[0].split(','))
        if (lat,lon)!=(cap_lat,cap_lon) or float(circle[1])!=0 or area.findtext(C+'areaDesc')!=country:
            raise ValueError('CAP point/location disagrees; never turn circle radius 0 into affected area')
        codes={e.findtext(C+'valueName'):e.findtext(C+'value') for e in info.findall(C+'eventCode')}
        if codes.get('Volcano Name')!=name or codes.get('New Activity')!=('Yes' if category.startswith('New ') else 'No'):
            raise ValueError('Native RSS category/CAP classification disagrees')
        guid=item.findtext('guid') or ''
        number=re.search(r'#vn_(\d{6})$',guid)
        if not number:raise ValueError('Native GVP volcano number absent')
        samples.append(ProductSample(id=number[1]+'-'+sent.strftime('%Y%m%d'),time=item_date,longitude=lon,latitude=lat,value=None,category=category,
            quality='Reporte preliminar publicado, no sensor continuo ni probabilidad. time es emisión del reporte, no hora de actividad. CAP certeza/urgencia se conservan como etiquetas.',
            attributes={'nombre':name,'pais':country,'periodo_reportado_local':period,'categoria_RSS':category,'GVP_volcano_number':number[1],
                'fecha_registro':'Emisión RSS por ítem, cotejada con CAP sent; no fecha de erupción',
                'RSS_pubDate':item.findtext('pubDate'),'RSS_channel_pubDate':channel.findtext('pubDate'),'CAP_sent':alert.findtext(C+'sent'),
                'CAP_identifier':alert.findtext(C+'identifier'),'CAP_status':alert.findtext(C+'status'),'CAP_msgType':alert.findtext(C+'msgType'),
                'CAP_urgency':info.findtext(C+'urgency'),'CAP_severity':info.findtext(C+'severity'),'CAP_certainty':info.findtext(C+'certainty'),
                'fuentes_primarias':info.findtext(C+'contact'),'reporte':guid,'geometria':'Ubicación del volcán, no área afectada; CAP circle tiene radio 0'}))
        periods.add(period)
    if not samples or len(samples)!=len(infos):raise ValueError('GVP RSS/CAP coverage differs or reports absent')
    return samples,sent,channel_date,sorted(periods),alert.findtext(C+'identifier')


def fetch_volcano_reports(now: datetime):
    rss,_=download(RSS,max_bytes=1_000_000)
    cap,_=download(CAP,max_bytes=1_000_000)
    samples,sent,channel_date,periods,version=decode_reports(rss,cap)
    raw=json.dumps({'rss_url':RSS,'cap_url':CAP,'rss_base64':base64.b64encode(rss).decode(),'cap_base64':base64.b64encode(cap).decode()},sort_keys=True,separators=(',',':')).encode()
    sha=hashlib.sha256(raw).hexdigest()
    return publish(ScientificProduct(id='d23-weekly-activity-reports',source_id='D23',title='GVP · archivo de reportes de actividad · '+', '.join(periods),
        collection_id='Smithsonian/USGS Weekly Volcanic Activity Report RSS + CAP 1.1',product_version=version,
        variable='published_activity_category',unit='categoría publicada',native_unit='categoría textual RSS',kind='historical',representation='points',
        issued_at=sent,issue_time_basis=f'CAP sent coincide con cada pubDate RSS. Canal RSS declara {channel_date.isoformat()} (puede diferir por zona): se conserva sin sustituir emisión por recuperación. Período de actividad es calendario local textual, sin inventar UTC.',
        retrieved_at=now,ingested_at=now,original_url=RSS,license_url='https://volcano.si.edu/terms_of_use.cfm',attribution='Smithsonian Global Volcanism Program / USGS Volcano Hazards Program; observatorios primarios por reporte',
        checksum_sha256=sha,byte_size=len(raw),raw_file=f'd23-weekly-activity-reports/assets/{sha}.json',coverage=f'{len(samples)} reportes geolocalizados; períodos: '+', '.join(periods),cadence_seconds=86400,method_version='gvp-weekly-rss-cap-v1',
        limitation='Archivo preliminar de reportes publicados, no lista exhaustiva de actividad ni precursores en tiempo real. La fecha por registro es emisión; la actividad tiene período calendario local sin zona homogénea. El punto identifica el volcán, no zona de peligro. No se extraen intensidades, probabilidades ni fechas de próxima erupción del texto. El feed puede atrasarse: en la primera comprobación entregó 8–14 octubre frente a la página semanal de noviembre (descarga automatizada 403). Se muestra siempre el período recibido, sin sustituirlo por la recuperación. Canal RSS e ítems/CAP pueden diferir en zona: ambas etiquetas quedan accesibles.',samples=samples,
        verification=Verification(method='Todos los nombres, países, períodos y coordenadas GeoRSS cotejados con CAP independiente; categoría New/Continuing y emisión por ítem comparadas. Radio CAP cero conserva ubicación, sin inventar polígonos de alerta.',
            original_url=CAP,checked_at=now,expected=f'{len(samples)} reportes RSS',actual=f'{len(samples)} coincidencias CAP 1.1',passed=True)),raw,'.json')
