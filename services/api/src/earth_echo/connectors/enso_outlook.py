"""Official CPC RONI tables, not probabilities read from a chart or ONI extrapolation."""
import hashlib
import html
from html.parser import HTMLParser
import json
import math
import re
import zipfile
from datetime import datetime,timezone
from earth_echo.connectors.http import download
from earth_echo.connectors.scientific_archive import pack_files
from earth_echo.contracts.products import ScientificProduct,ProductSample,Verification
from earth_echo.storage.products import publish

BASE='https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/'
DISCUSSION='https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_advisory/ensodisc.shtml'
MONTHS='January February March April May June July August September October November December'.split()
SHORT='Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()
PHASES=['La Niña','Neutral','El Niño']
STRENGTHS=['Index ≤ -2.0°C','-1.5°C ≥ Index > -2.0°C','-1.0°C ≥ Index > -1.5°C','-0.5°C ≥ Index > -1.0°C','−0.5°C < Index < 0.5°C','0.5°C ≤ Index < 1.0°C','1.0°C ≤ Index < 1.5°C','1.5°C ≤ Index < 2.0°C','Index ≥ 2.0°C']
STRENGTH_LABELS=['LN ≤−2','LN −2…−1,5','LN −1,5…−1','LN −1…−0,5','Neutral','EN 0,5…1','EN 1…1,5','EN 1,5…2','EN ≥2']
QUANTILES=[5,15,25,50,75,85,95]
METHOD='cpc-roni-official-tables-v1'
DEFINITION='RONI ERSSTv6: media móvil de tres meses de anomalías SST Niño3.4 (5°N–5°S,170–120°W), menos anomalía media tropical20°N–20°S y ajuste de varianza a Niño3.4. Base1991–2020. Fase de un trimestre: La Niña RONI≤−0,5°C, Neutral −0,5<RONI<0,5°C, El Niño RONI≥0,5°C. No se convierte automáticamente en episodio histórico de cinco estaciones consecutivas.'


class CpcTable(HTMLParser):
    def __init__(self,table_id='probabilities-table'):
        super().__init__(convert_charrefs=True)
        self.table_id=table_id
        self.depth=0;self.found=0;self.rows=[];self.row=None;self.cell=None;self.text=[]

    def handle_starttag(self,tag,attrs):
        if tag=='table':
            if self.depth:self.depth+=1
            elif dict(attrs).get('id')==self.table_id:self.depth=1;self.found+=1
        if self.depth and tag=='tr':self.row=[]
        if self.depth and tag in ('td','th'):self.cell=[]

    def handle_endtag(self,tag):
        if self.depth and tag in ('td','th') and self.cell is not None:
            self.row.append(' '.join(''.join(self.cell).split()));self.cell=None
        if self.depth and tag=='tr' and self.row is not None:
            self.rows.append(self.row);self.row=None
        if self.depth and tag=='table':self.depth-=1

    def handle_data(self,data):
        self.text.append(data)
        if self.cell is not None:self.cell.append(data)


def parse_table(raw,kind):
    table_id='outlook-table' if kind=='outlook' else 'probabilities-table'
    text=raw.decode('utf-8');parser=CpcTable(table_id);parser.feed(text)
    if parser.found!=1 or len(parser.rows)!=10:raise ValueError('Expected one CPC table and nine complete seasons')
    plain=' '.join(' '.join(parser.text).split())
    match=re.search(r'Issued ('+'|'.join(MONTHS)+r') (20\d{2})',plain)
    if not match:raise ValueError('CPC monthly issue not provided')
    edition=(int(match[2]),MONTHS.index(match[1])+1)
    expected=['Season',*(PHASES if kind=='probabilities' else STRENGTHS if kind=='strengths' else [str(q)+'%' for q in QUANTILES])]
    if parser.rows[0]!=expected:raise ValueError('CPC columns/units/category thresholds changed')
    if 'Relative Oceanic Niño Index (RONI)' not in plain or '1991–2020' not in plain:
        raise ValueError('CPC forecast index/reference definition changed')
    rows=[]
    for row in parser.rows[1:]:
        if len(row)!=len(expected):raise ValueError('Incomplete CPC season')
        values=[float(v) for v in row[1:]]
        if any(not math.isfinite(v) for v in values):raise ValueError('Missing CPC value, no zero fill')
        if kind!='outlook' and (any(not 0<=v<=100 or not v.is_integer() for v in values) or sum(values)!=100):
            raise ValueError('CPC rounded percentages must total100; do not renormalize')
        if kind=='outlook' and any(a>b for a,b in zip(values,values[1:])):raise ValueError('CPC RONI quantiles not monotonic')
        rows.append((row[0],values))
    # Independent direct extraction of the original numeric TDs, not parser state.
    table=re.search(r'<table\s+id="'+table_id+r'"\s*>(.*?)</table>',text,re.S)
    direct=[]
    if table:
        for row in re.findall(r'<tr\b[^>]*>(.*?)</tr>',table[1],re.S):
            cells=re.findall(r'<td>([-+\d.]+)</td>',row)
            if cells:direct.append([float(v) for v in cells])
    if direct!=[v for _,v in rows]:raise ValueError('Independent original HTML numeric extraction disagrees')
    return edition,rows


def add_months(year,month,delta):
    n=year*12+month-1+delta
    return datetime(n//12,n%12+1,1,tzinfo=timezone.utc)


def products_from_files(files,now):
    parsed={k:parse_table(files[k+'.html'],k) for k in ('probabilities','strengths','outlook')}
    editions={e for e,_ in parsed.values()}
    if len(editions)!=1:raise ValueError('Mixed CPC issue months; previous retained')
    year,month=next(iter(editions))
    if (year,month)>(now.year,now.month):raise ValueError('CPC issue lies in future')
    definition=html.unescape(re.sub('<[^>]+>',' ',files['definition.html'].decode('utf-8')))
    if not all(s in definition for s in ('ERSSTv6','1991–2020','variance','20°N–20°S')):raise ValueError('RONI method/ERSST version changed')
    # Only the forecast edition month is known; do not manufacture midnight as issuance.
    edition=f'{year:04}-{month:02}'
    native={k:rows for k,(_,rows) in parsed.items()}
    seasons=[r[0] for r in native['probabilities']]
    if any([r[0] for r in rows]!=seasons for rows in native.values()):raise ValueError('CPC table windows disagree')
    windows=[]
    for i,label in enumerate(seasons):
        start=add_months(year,month,i-1);end=add_months(start.year,start.month,3)
        months=[SHORT[(start.month+j-1)%12] for j in range(3)]
        if label!=''.join(m[0] for m in months)+' '+' '.join(months):raise ValueError('CPC season sequence/epoch changed')
        windows.append((start,end,label.split()[0]+f' {start.year}'+(f'–{end.year}' if end.year!=start.year and end.month!=1 else '')))
        p=native['probabilities'][i][1];s=native['strengths'][i][1]
        if p!=[sum(s[:4]),s[4],sum(s[5:])]:raise ValueError('Independent CPC strength bins do not match phase probabilities')
    scientific={'edition':edition,'tables':native,'definition':DEFINITION,'method':METHOD}
    science_sha=hashlib.sha256(json.dumps(scientific,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    raw=pack_files(files,{'schema_version':'1','assets':{n:{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'url':BASE+(n[:-5]+'/') if n not in ('definition.html',) else BASE} for n,b in files.items()}},compression=zipfile.ZIP_DEFLATED)
    sha=hashlib.sha256(raw).hexdigest();products=[]
    for kind,title,variable in [('probabilities','Probabilidades de fase ENSO','enso_phase_probability'),('strengths','Probabilidades de intensidad ENSO','enso_strength_probability'),('outlook','RONI previsto · percentiles','RONI_forecast_percentile')]:
        probabilities=kind!='outlook';columns=PHASES if kind=='probabilities' else STRENGTHS if kind=='strengths' else ['p'+str(q) for q in QUANTILES]
        samples=[]
        for i,(_,values) in enumerate(native[kind]):
            start,end,season=windows[i]
            for j,(column,value) in enumerate(zip(columns,values,strict=True)):
                definition_=f'Probabilidad oficial CPC de {column} para {season}, intervalo civil [{start.date()},{end.date()}) UTC. '+DEFINITION+' Porcentajes enteros publicados:0% y100% son aproximados, no imposibilidad/certeza absoluta. No probabilidad de impacto local.' if probabilities else None
                samples.append(ProductSample(id=f'{start:%Y-%m}-'+('phase' if kind=='probabilities' else 'strength' if kind=='strengths' else 'quantile')+f'-{j}',time=start,valid_to=end,value=value,category=column,
                    probability=value/100 if probabilities else None,probability_definition=definition_,quality='Pronóstico externo oficial CPC por consenso de expertos/modelos, no validación Earth Echo. Números/intervalos publicados conservados;0% es aproximado.' if probabilities else 'Percentil del RONI previsto oficial. No es probabilidad de evento ni intervalo de confianza de una observación.',
                    attributes={'nombre':season+' · '+(STRENGTH_LABELS[j] if kind=='strengths' else column),'season':season,'season_order':str(i),'column':column,'column_order':str(j),'column_label':STRENGTH_LABELS[j] if kind=='strengths' else column,'issued_month':edition,'native_value':str(int(value)) if probabilities else str(value),'time_definition':'Inicio/fin exclusivo del trimestre civil UTC; no instante de una observación ni emisión. Estaciones solapadas; algunas ya iniciadas al emitir.', 'RONI_definition':DEFINITION,**({'percentile_level':str(QUANTILES[j]/100)} if not probabilities else {})}))
        verification=Verification(method='Celdas de tres tablas HTML oficiales extraídas con HTMLParser y cotejadas con extracción numérica independiente directa de los TD originales. Nueve ventanas y edición coinciden. Por cada estación, suma de las cuatro clases frías/las cuatro cálidas de tabla de intensidad coincide exactamente con tabla de fase; neutral coincide, total100 sin renormalizar. Siete percentiles ordenados y unidades/definición RONI verificados.',original_url=BASE+'strengths/',checked_at=now,expected='9 estaciones×3 fases y9 categorías intensidad, totales100%, grupos coincidentes;7 percentiles RONI ordenados',actual=f'Edición{edition};9/9 ventanas y cotejos satisfactorios; números originales coincidentes',passed=True)
        products.append(ScientificProduct(id='d48-roni-'+kind,source_id='D48',title=title+' · CPC · '+edition,collection_id='NOAA CPC official RONI / '+kind,product_version=edition+' / RONI ERSSTv6 / base1991–2020',variable=variable,unit='%' if probabilities else '°C (RONI)',native_unit='porcentaje entero' if probabilities else '°C de RONI, percentiles5/15/25/50/75/85/95',kind='forecast',representation='table',observed_at=None,initialized_at=None,issued_at=None,issue_time_basis=f'El proveedor declara Issued {MONTHS[month-1]} {year}; no proporciona día/hora UTC de las tablas. issued_at e initialized_at quedan null. El inicio de un trimestre civil no es emisión. '+DEFINITION,valid_from=windows[0][0],valid_to=windows[-1][1],retrieved_at=now,ingested_at=now,original_url=BASE+kind+'/',license_url='https://www.weather.gov/disclaimer',attribution='NOAA Climate Prediction Center / NCEP / NWS, official RONI outlook. Tablas oficiales de consenso, sin recalibración o modelo Earth Echo.',checksum_sha256=sha,scientific_checksum_sha256=science_sha,byte_size=len(raw),raw_file=f'shared/{sha}.zip',coverage='Niño3.4,5°N–5°S/170–120°W, índice climático regional con influencia mundial. Nueve trimestres móviles; no malla mundial, pines, trayectoria o pronóstico local de impactos.',cadence_seconds=86400,method_version=METHOD,samples=samples,verification=verification,
            limitation='Pronóstico externo oficial CPC con edición mensual; revisión diaria conserva cada edición retenida sin rejuvenecer ventanas. RONI resta media tropical y ajusta varianza: no es ONI histórico ni se pega a esa serie. Referencia1991–2020/ERSSTv6 del índice de verificación; consenso de expertos y múltiples modelos con inicializaciones distintas/no única acreditada. Algunas estaciones ya comenzaron cuando se emite; son períodos civiles solapados, no nueve meses independientes ni fecha de desastre. Probabilidades de fase/intensidad no son probabilidades de inundación, sequía o daño local. Cero/cien publicados son aproximados; se conservan sin inventar épsilon o certeza. Los percentiles son valores de RONI en°C, no una nueva probabilidad calculada. No se deriva diagnóstico de evento de cinco estaciones desde estas probabilidades. No demuestra habilidad local o validación predictiva de modelo propio. '+DEFINITION))
    return products,raw


def fetch_enso_outlook(now:datetime):
    files={name+'.html':download(BASE+name+'/',max_bytes=100_000)[0] for name in ('probabilities','strengths','outlook')}
    files['definition.html']=download(BASE,max_bytes=150_000)[0]
    products,raw=products_from_files(files,now)
    results=[publish(p,raw,'.zip') for p in products]
    return 'unchanged' if all(r=='unchanged' for r in results) else 'stored'
