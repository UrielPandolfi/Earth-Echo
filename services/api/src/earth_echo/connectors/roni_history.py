"""Published ERSSTv6 RONI history from the same CPC bytes as the outlook."""
import hashlib
import html
import json
import math
import re
from datetime import datetime
from earth_echo.connectors.enso_outlook import CpcTable,BASE,DEFINITION,SHORT,add_months
from earth_echo.contracts.products import ScientificProduct,ProductSample,Verification

KEY='d48-roni-history'
METHOD='cpc-roni-history-ersstv6-v1'
TABLE='roni-v5-table2'  # Legacy HTML element ID; the published scientific version is v6.


def decode_history(raw,now):
    text=raw.decode('utf-8');parser=CpcTable(TABLE);parser.feed(text)
    plain=html.unescape(re.sub('<[^>]+>',' ',text))
    if parser.found!=1 or not all(s in plain for s in ('ERSSTv6','1991–2020','variance','20°N–20°S')):
        raise ValueError('Unexpected published RONI historical table/definition')
    header=['Year The year']
    for month in range(1,13):
        months=[SHORT[(month-2+j)%12] for j in range(3)]
        header.append(''.join(m[0] for m in months)+' '+' '.join(months))
    native=[]
    for row in parser.rows:
        if row and row[0].startswith('Year'):
            if row!=header:raise ValueError('RONI season columns changed')
            continue
        if not row or not re.fullmatch(r'\d{4}',row[0]) or not 1<=len(row)-1<=12:
            raise ValueError('Incomplete RONI historical row')
        values=[None if v=='' else float(v) for v in row[1:]]
        if any(v is not None and (not math.isfinite(v) or not -10<=v<=10) for v in values):raise ValueError('Invalid RONI native index; no zero substitution')
        native.append((int(row[0]),values))
    if not native or [y for y,_ in native]!=list(range(1950,native[-1][0]+1)) or native[-1][0]>now.year:
        raise ValueError('RONI historical years missing/duplicated/out of order')
    if any(len(v)!=12 for _,v in native[:-1]):raise ValueError('Only final RONI year may omit unpublished seasons')
    # Independent raw-HTML extraction also handles the legal omitted final </tr>.
    match=re.search(r'<table\b[^>]*id="'+TABLE+r'"[^>]*>(.*?)</table>',text,re.S)
    direct=[]
    if match:
        for row in re.findall(r'<tr\b[^>]*>(.*?)(?:</tr>|(?=<tr\b)|(?=</tbody>))',match[1],re.S):
            head=re.search(r'<th\b[^>]*>(.*?)</th>',row,re.S)
            year=html.unescape(re.sub('<[^>]+>','',head[1])).strip() if head else ''
            if not re.fullmatch(r'\d{4}',year):continue
            cells=[html.unescape(re.sub('<[^>]+>','',v)).strip() for v in re.findall(r'<td\b[^>]*>(.*?)</td>',row,re.S)]
            direct.append((int(year),[None if not v else float(v) for v in cells]))
    if direct!=native:raise ValueError('Independent RONI original HTML extraction disagrees')
    samples=[]
    for year,values in native:
        for month in range(1,13):
            value=values[month-1] if month<=len(values) else None
            start=add_months(year,month,-1);end=add_months(year,month,2)
            if value is not None and end>now:raise ValueError('Unfinished future RONI season presented as historical')
            season=header[month].split()[0]
            samples.append(ProductSample(id=f'{year}-{season}',time=start,valid_to=end,value=value,
                quality='Índice publicado ERSSTv6/RONI; los valores más recientes son estimaciones revisables hasta dos meses según CPC. Sin clasificación automática de episodio.' if value is not None else 'No publicado en el año final: missing/null, no cero ni pronóstico.',
                attributes={'nombre':f'{season} {year}','native_year':str(year),'season':season,'native_value':None if value is None else str(value),'missing_reason':None if value is not None else 'Celda vacía/temporada no publicada en el último año',
                    'time_definition':'time=inicio y valid_to=fin exclusivo del trimestre civil UTC. El año nativo corresponde al mes central; DJF 1950 comienza en diciembre 1949. No fecha de pasada individual.',
                    'definition':DEFINITION}))
    return samples,native


def history_from_shared_archive(raw,base:ScientificProduct,now:datetime):
    samples,native=decode_history(raw,now)
    available=[s for s in samples if s.value is not None];latest=available[-1]
    scientific=hashlib.sha256(json.dumps({'native_rows':native,'definition':DEFINITION,'method':METHOD},sort_keys=True).encode()).hexdigest()
    return ScientificProduct.model_validate({**base.model_dump(),
        'id':KEY,'title':f'RONI · historia ERSSTv6 · 1950–{native[-1][0]}','collection_id':'NOAA CPC RONI ERSSTv6 published seasonal history',
        'product_version':f'ERSSTv6 / base 1991–2020 / último {latest.id}','variable':'relative_oceanic_nino_index','unit':'°C (RONI)','native_unit':'°C, valores publicados a 0,1°C',
        'kind':'historical','representation':'time_series','observed_at':latest.time,'observation_end':latest.valid_to,'issued_at':None,'initialized_at':None,'valid_from':None,'valid_to':None,
        'retrieved_at':base.retrieved_at,'ingested_at':now,'original_url':BASE,'attribution':'NOAA CPC / NCEI, Relative Oceanic Niño Index con reconstrucción ERSSTv6. Valores publicados, sin recalcular el índice en Earth Echo.',
        'scientific_checksum_sha256':scientific,'method_version':METHOD,'samples':samples,
        'issue_time_basis':'El rango observado identifica el último trimestre publicado, no una pasada o emisión. Año nativo=mes central; intervalos civiles definidos explícitamente. Sin hora UTC de emisión publicada. '+DEFINITION,
        'coverage':f'Historia Niño 3.4, años centrales 1950–{native[-1][0]}: {len(available)} valores publicados, {len(samples)-len(available)} temporadas del último año no publicadas permanecen null. Último {latest.id}={latest.value} °C. No observación mundial ni índice de impacto local.',
        'limitation':'Índice histórico publicado por CPC a partir de ERSSTv6: resta media tropical y ajusta varianza, con base 1991–2020. No es ONI, temperatura del aire o clasificación automática ENSO de cinco estaciones. Medias de tres meses solapadas, no observaciones mensuales independientes; época civil UTC explícita, año nativo del mes central. Las celdas no publicadas del año final quedan missing/null; cero 0,0 publicado sí es válido. Los valores más recientes pueden revisarse hasta dos meses por el filtro de ERSSTv6, según CPC. No se deriva tendencia lineal, significación, impacto o probabilidad. Se decodifica la tabla visible de la página actual v6: el ID HTML heredado roni-v5-table2 no determina la edición científica. Reutiliza exactamente el ZIP de referencia de los pronósticos; sin otra descarga del mismo activo.',
        'verification':Verification(method='Cada año/temporada/valor y vacío cotejados entre HTMLParser y extracción independiente del HTML original visible. Cabeceras repetidas, años consecutivos, referencia ERSSTv6/base, ausencia y secuencia de trimestres comprobadas. Se admite cierre de fila HTML implícito antes de tbody sin perder el último año; no se lee la tabla oculta vacía.',
            original_url=BASE,checked_at=now,expected=f'{len(native)} años consecutivos desde 1950; columnas DJF…NDJ; números/vacíos del original',actual=f'{len(available)} valores coincidentes y {len(samples)-len(available)} no publicados; último {latest.id}={latest.value} °C',passed=True)})
