"""Sentinel-2 C1 surface reflectance and NDVI, a bounded public Pampa window."""
import hashlib
import io
import json
import math
import zipfile
from datetime import datetime,timedelta
from decimal import Decimal,localcontext
from urllib.parse import urlencode
import xml.etree.ElementTree as ET
import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.windows import Window
from earth_echo.connectors.http import download
from earth_echo.connectors.ranges import RangeSource,ArchivedRangeSource
from earth_echo.connectors.scientific_archive import pack_files
from earth_echo.connectors.tiff_native import native_window
from earth_echo.contracts.products import ScientificGrid,ScientificProduct,ScientificCalculation,CalculationInput,Verification
from earth_echo.science.vegetation import ndvi
from earth_echo.storage.products import publish,read_product,products_root

ROOT='https://earth-search.aws.element84.com/v1'
COLLECTION='sentinel-2-c1-l2a'
PREFIX='https://e84-earth-search-sentinel-data.s3.us-west-2.amazonaws.com/sentinel-2-c1-l2a/'
KEY='d25-s2-pampa'
METHOD='s2-c1-native-qa-reflectance-ndvi-pampa-v1'
DOC='https://sentiwiki.copernicus.eu/web/s2-processing'
WEST,EAST,SOUTH,NORTH=-61.54,-61.46,-35.49,-35.43
WIDTH,HEIGHT=80,60
SCL={0:'Sin dato',1:'Saturado/defectuoso',2:'Sombra proyectada',3:'Sombra de nube',4:'Vegetación',5:'No vegetado',6:'Agua',7:'No clasificado',8:'Nube media',9:'Nube alta',10:'Cirro fino',11:'Nieve/hielo'}


def canonical(item):return json.dumps(item,sort_keys=True,separators=(',',':')).encode()


def xml_values(raw):
    # xml.etree does not resolve external entities. Reject declarations as well.
    if b'<!DOCTYPE' in raw or b'<!ENTITY' in raw:raise ValueError('Unexpected external XML declaration')
    return ET.fromstring(raw)


def node(root,name):
    found=[e.text for e in root.iter() if e.tag.split('}')[-1]==name]
    if len(found)!=1 or found[0] is None:raise ValueError('Missing/ambiguous Sentinel XML '+name)
    return found[0]


def asset_url(item,key):
    url=item['assets'][key]['href']
    if not url.startswith(PREFIX) or '/'+item['id']+'/' not in url or any(part in url for part in ('..','?','#')):
        raise ValueError('Unexpected Sentinel C1 distribution; no silent pre-C1/harmonized fallback')
    return url


def target_axes():
    return (np.array([WEST+(i+.5)*(EAST-WEST)/WIDTH for i in range(WIDTH)]),
            np.array([NORTH-(i+.5)*(NORTH-SOUTH)/HEIGHT for i in range(HEIGHT)]))


def decode_assets(item,product_xml,granule_xml,sources):
    p=xml_values(product_xml);g=xml_values(granule_xml);props=item['properties']
    if item['collection']!=COLLECTION or node(p,'PRODUCT_URI')!=props['s2:product_uri'] or node(p,'PROCESSING_BASELINE')!=props['s2:processing_baseline']:
        raise ValueError('Sentinel edition/product metadata disagree')
    if float(props['s2:processing_baseline'])<5 or props.get('earthsearch:boa_offset_applied') is True:
        raise ValueError('Only qualified C1 original-offset encoding is supported')
    quant=Decimal(node(p,'BOA_QUANTIFICATION_VALUE'))
    offsets={int(e.attrib['band_id']):Decimal(e.text) for e in p.iter() if e.tag.split('}')[-1]=='BOA_ADD_OFFSET'}
    if quant!=10000 or offsets.get(3)!=-1000 or offsets.get(7)!=-1000:raise ValueError('Sentinel BOA scale/offset changed')
    stamp=datetime.fromisoformat(node(g,'SENSING_TIME').replace('Z','+00:00'))
    if stamp.tzinfo is None or abs((stamp-datetime.fromisoformat(props['datetime'].replace('Z','+00:00'))).total_seconds())>.001:
        raise ValueError('Sentinel sensing UTC disagrees with STAC')
    if node(g,'HORIZONTAL_CS_CODE')!='EPSG:32720' or props['proj:epsg']!=32720:raise ValueError('Unqualified Sentinel CRS/region')
    lons,lats=target_axes();xx,yy=Transformer.from_crs(4326,32720,always_xy=True).transform(*np.meshgrid(lons,lats))
    native={};quality=None;reference=None
    for key in ('red','nir','scl'):
        asset=item['assets'][key];source=sources[key];resolution=20 if key=='scl' else 10
        url=asset_url(item,key)
        if source.url!=url:raise ValueError('Retained Sentinel block URL does not match asset')
        expected_shape=[5490,5490] if key=='scl' else [10980,10980]
        transform=[resolution,0,600000,0,-resolution,6100000]
        if asset['proj:shape']!=expected_shape or asset['proj:transform']!=transform:raise ValueError('Unexpected STAC native georeferencing')
        geopos=next((e for e in g.iter() if e.tag.split('}')[-1]=='Geoposition' and e.attrib.get('resolution')==str(resolution)),None)
        size=next((e for e in g.iter() if e.tag.split('}')[-1]=='Size' and e.attrib.get('resolution')==str(resolution)),None)
        if geopos is None or size is None or [float(node(geopos,k)) for k in ('XDIM','ULX','YDIM','ULY')]!=[resolution,600000,-resolution,6100000] or [int(node(size,k)) for k in ('NROWS','NCOLS')]!=expected_shape:
            raise ValueError('Independent XML georeferencing disagrees')
        rows=np.floor((6100000-yy)/resolution).astype(int);cols=np.floor((xx-600000)/resolution).astype(int)
        align=1 if key=='scl' else 2
        r0=int(rows.min())//align*align;c0=int(cols.min())//align*align
        r1=(int(rows.max())+align)//align*align;c1=(int(cols.max())+align)//align*align
        window=Window(c0,r0,c1-c0,r1-r0)
        if window.width*window.height>2_000_000:raise ValueError('Sentinel window exceeds measured native budget')
        def opener(path,mode='rb',**kwargs):
            if str(path)!=url:raise FileNotFoundError(path)
            return source.open()
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR'),rasterio.open(url,opener=opener) as ds:
            rb=asset['raster:bands'][0];scale=1 if key=='scl' else float(1/quant);offset=0 if key=='scl' else float(offsets[3 if key=='red' else 7]/quant)
            if ds.count!=1 or ds.crs.to_epsg()!=32720 or list(ds.transform)[:6]!=transform or [ds.height,ds.width]!=expected_shape or ds.nodata!=0 or ds.dtypes[0]!=('uint8' if key=='scl' else 'uint16'):
                raise ValueError('Native Sentinel TIFF shape/CRS/encoding disagrees')
            if ds.scales[0]!=scale or ds.offsets[0]!=offset or (key!='scl' and (rb['scale']!=scale or rb['offset']!=offset)) or rb['nodata']!=0:
                raise ValueError('Native Sentinel TIFF/XML/STAC scale or nodata disagree')
            values=ds.read(1,window=window)
        independent,tags=native_window(source,window)
        keys={tags[34735][i]:tags[34735][i+3] for i in range(4,len(tags[34735]),4) if tags[34735][i+1]==0}
        if keys.get(3072)!=32720 or keys.get(1025)!=1 or tags[33550][:2]!=(resolution,resolution) or tags[33922]!=(0.,0.,0.,600000.,6100000.,0.) or not np.array_equal(values,independent):
            raise ValueError('Independent TIFF pixels/georeferencing disagree')
        sampled=values[rows-r0,cols-c0]
        native[key]=sampled
        if key=='scl':
            if not set(np.unique(values))<=set(SCL):raise ValueError('Unknown Sentinel SCL classes')
            quality=sampled
        if key=='red':reference={'native_window':list(window.flatten()),'native_red_cells':int(values.size)}
    return native,quality,stamp,reference


def products_from_files(files,now,sources=None):
    item=json.loads(files['item.json'])
    sources=sources or {k:ArchivedRangeSource(files[k+'-ranges.json']) for k in ('red','nir','scl')}
    native,quality,stamp,reference=decode_assets(item,files['product_metadata.xml'],files['granule_metadata.xml'],sources)
    if stamp>now:raise ValueError('Sentinel scene lies in future')
    if 'red-ranges.json' not in files:
        for key,source in sources.items():files[key+'-ranges.json']=source.archive({'encoding':'Exact provider COG ranges, first native IFD; display subset in method'})
    manifest={'schema_version':'1','method':METHOD,'assets':{n:{'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)} for n,b in files.items()},'window':reference}
    archive=pack_files(files,manifest,compression=zipfile.ZIP_DEFLATED);sha=hashlib.sha256(archive).hexdigest()
    lons,lats=target_axes();valid=np.isin(quality,[4,5]);grids={}
    for key in ('red','nir'):
        values=np.where(valid & (native[key]!=0),native[key].astype(float)*.0001-.1,np.nan)
        grids[key]=[None if not math.isfinite(v) else float(v) for v in values.flatten()]
    grids['ndvi']=[ndvi(r,n) for r,n in zip(grids['red'],grids['nir'],strict=True)]
    present_index=next((i for i,v in enumerate(grids['ndvi']) if v is not None),None)
    if present_index is None:raise ValueError('No qualified land sample in Sentinel scene; no zero fill')
    with localcontext() as ctx:
        ctx.prec=40
        r,n=(Decimal(int(native[k].flat[present_index])) for k in ('red','nir'))
        expected=float((n-r)/(n+r-2000))
    actual=grids['ndvi'][present_index]
    if not math.isclose(expected,actual,rel_tol=1e-12,abs_tol=1e-12):raise ValueError('Independent native-DN Decimal NDVI disagrees')
    verification=Verification(method='Todos los DN de ventanas nativas rojo/NIR/SCL cotejados rasterio frente a lector independiente struct+zlib/predictor TIFF. CRS/transform/forma contrastados con XML, STAC y GeoTIFF. Escala/desplazamiento BOA XML y TIFF coinciden. NDVI cotejado con Decimal de 40 dígitos desde DN nativos, sin duplicar corrección de offset.',original_url=asset_url(item,'product_metadata'),checked_at=now,expected=f'NDVI Decimal={expected}; {reference["native_red_cells"]} DN rojos',actual=f'NDVI={actual}; todos los DN/máscaras/georreferenciación coinciden',passed=True)
    products=[]
    for key,title,variable in [('red','Reflectancia roja B04','surface_reflectance_B04'),('nir','Reflectancia infrarroja B08','surface_reflectance_B08'),('ndvi','NDVI calculado','NDVI')]:
        values=grids[key];present=[v for v in values if v is not None]
        if not present:raise ValueError('Sentinel band has no qualified values')
        grid=ScientificGrid(width=WIDTH,height=HEIGHT,west=WEST,east=EAST,south=SOUTH,north=NORTH,longitudes=lons.tolist(),latitudes=lats.tolist(),values=values,minimum=min(present),maximum=max(present),missing_cells=values.count(None),
            resolution='Bandas nativas 10 m UTM 20S; calidad SCL 20 m. Vista WGS84 0,001° (~91×111 m en Pampa).',
            sampling='Vecino nativo contenedor de cada centro WGS84, transformado con PROJ de EPSG:4326 a 32720; sin promediar, interpolar huecos o usar overviews AVERAGE. SCL de 20 m por el mismo punto. Ventanas completas y bloques TIFF originales permiten reproducir valores nativos de 10 m.',
            quality_mask='Sólo SCL=4/5 (vegetación/no vegetado) y DN!=0 en cada banda. SCL 0/1/2/3/6/7/8/9/10/11 ausentes. Reflectancia=(DN-1000)/10000; negativos de recuperación conservados en bandas, NDVI ausente si algún componente<0 o suma≤0. No se inventa confianza ni se identifica salud del cultivo.',quality_values=quality.flatten().tolist(),quality_legend={str(k):v for k,v in SCL.items()})
        calculation=ScientificCalculation(method_version=METHOD,formula='NDVI=(rho_B08-rho_B04)/(rho_B08+rho_B04); rho=(DN+BOA_ADD_OFFSET)/BOA_QUANTIFICATION_VALUE',parameters={'BOA_ADD_OFFSET_DN':-1000,'BOA_QUANTIFICATION_VALUE':10000,'minimum_reflectance_for_NDVI':0,'SCL_land_vegetation':4,'SCL_land_not_vegetated':5},
            inputs=[CalculationInput(product_id=KEY+'-'+k,variable='surface_reflectance_B04' if k=='red' else 'surface_reflectance_B08',unit='1 (reflectancia)',checksum_sha256=sha) for k in ('red','nir')],reference_url=DOC,reference_period='Una pasada; no climatología/anomalía ni referencia temporal de estrés.',applicability='Índice espectral local en tierra clasificada SCL4/5, componentes no negativas y denominador positivo. No rendimiento, sequía, pérdida agrícola, tendencia ni probabilidad.') if key=='ndvi' else None
        products.append(ScientificProduct(id=KEY+'-'+key,source_id='D25',title=title+' · Sentinel-2 · Pampa',collection_id=item['id'],product_version=f'Copernicus Sentinel-2 C1 L2A / baseline {item["properties"]["s2:processing_baseline"]} / '+item['properties']['s2:product_uri'],variable=variable,unit='1 (NDVI)' if key=='ndvi' else '1 (reflectancia)',native_unit='uint16 DN, BOA offset -1000 / quantification 10000; SCL uint8',kind='indicator' if calculation else 'observation',representation='field',observed_at=stamp,issued_at=None,issue_time_basis='SENSING_TIME UTC del XML nativo, cotejado con STAC a 1 ms. generation_time es procesamiento del producto, no emisión de pronóstico; consta en la versión/metadatos originales.',retrieved_at=now,ingested_at=now,original_url=asset_url(item,'red'),license_url='https://sentinels.copernicus.eu/documents/247904/690755/Sentinel_Data_Legal_Notice',attribution='Contains modified Copernicus Sentinel data (2026). ESA / Copernicus Sentinel-2 MSI, procesamiento C1 L2A, COG y distribución pública Element 84 Earth Search / AWS. NDVI calculado por Earth Echo.',checksum_sha256=sha,byte_size=len(archive),raw_file=f'shared/{sha}.zip',coverage='Ventana Pampa [-61,54,-61,46] × [-35,49,-35,43], ~7×7 km. Una pasada seleccionada dentro de 30 días, nube global de tesela≤40%; la máscara local SCL determina disponibilidad real. No cobertura mundial ni selección por salud/peligro.',cadence_seconds=86400,method_version=METHOD,grid=grid,calculation=calculation,verification=verification,
            limitation='Reflectancia de superficie óptica y NDVI local, con huecos de calidad. No humedad del suelo, rendimiento, diagnóstico de estrés/causa ni probabilidad de evento. Esta ruta C1 conserva el offset original: se aplica exactamente una vez y se coteja con XML/TIFF, sin confiar en la colección pre-C1 con metadatos de harmonización ambiguos. SCL es clasificación del proveedor, no garantía de cielo despejado o exactitud por píxel. Negativos de reflectancia recuperada se conservan en bandas si pasan QA; NDVI tiene dominio conservador explícito. 80×60 centros WGS84 son una vista por vecino más cercano, no agregados o eventos. El ZIP compartido conserva rangos exactos, versiones/ETag, XML y respuesta STAC; no contiene los COG completos de cientos de MB. Otras regiones, Sentinel-1/InSAR, 5P y servicios CDSE autenticados siguen pendientes. No hay serie/tendencia temporal nueva ni validación predictiva.'))
    return products,archive


def fetch_sentinel_vegetation(now:datetime):
    params={'collections':COLLECTION,'bbox':f'{WEST},{SOUTH},{EAST},{NORTH}','datetime':(now-timedelta(days=30)).isoformat()+'/'+now.isoformat(),'limit':30,'sortby':'-properties.datetime'}
    search_url=ROOT+'/search?'+urlencode(params)
    search,_=download(search_url,max_bytes=1_500_000);result=json.loads(search)
    candidates=[f for f in result['features'] if f.get('collection')==COLLECTION and 0<=float(f['properties']['eo:cloud_cover'])<=40 and datetime.fromisoformat(f['properties']['datetime'].replace('Z','+00:00'))<=now]
    if not candidates:raise ValueError('No qualified Sentinel C1 scene in bounded 30-day search; previous retained')
    item=max(candidates,key=lambda f:f['properties']['datetime'])
    current=read_product(KEY+'-ndvi')
    if current is not None and current.method_version==METHOD:
        retained=(products_root()/current.raw_file).read_bytes()
        if hashlib.sha256(retained).hexdigest()!=current.checksum_sha256:raise ValueError('Retained Sentinel asset checksum disagrees')
        with zipfile.ZipFile(io.BytesIO(retained)) as archive:
            if archive.read('item.json')==canonical(item) and all((p:=read_product(KEY+'-'+k)) is not None and p.checksum_sha256==current.checksum_sha256 and p.method_version==METHOD for k in ('red','nir')):
                return 'unchanged'  # Successful discovery, not a new scientific download/date.
    files={'search.json':search,'item.json':canonical(item),'search-url.txt':search_url.encode()}
    for key in ('product_metadata','granule_metadata'):files[key+'.xml']=download(asset_url(item,key),max_bytes=2_000_000)[0]
    sources={}
    for key in ('red','nir','scl'):
        source=RangeSource(asset_url(item,key),max_bytes=8_000_000,max_requests=16);source.block_size=524288;sources[key]=source
    products,archive=products_from_files(files,now,sources)
    results=[publish(p,archive,'.zip') for p in products]
    return 'unchanged' if all(r=='unchanged' for r in results) else 'stored'
