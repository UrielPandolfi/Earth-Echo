"""FAO ASIS numeric exports locked to a real dekad/crop season, never RGB maps."""
import base64
import hashlib
import json
import math
import re
from datetime import datetime,timezone
from urllib.parse import urlencode,urlparse
import numpy as np
from rasterio.io import MemoryFile
from earth_echo.connectors.http import download
from earth_echo.contracts.products import ScientificProduct,ScientificGrid,Verification
from earth_echo.storage.products import publish

BASE='https://asis-esri.fao.org/image/rest/services/ASI_D/ImageServer'
ITEM='https://hqfao.maps.arcgis.com/sharing/rest/content/items/bca45971e87e46c182fbd048d3aee4ff?f=json'
VIEWS={'pampa':(-63.,-34.,224,224)}

def request_json(url,params=None):
    raw,_=download(url+('?' +urlencode(params) if params else ''),max_bytes=500_000)
    data=json.loads(raw)
    if 'error' in data: raise ValueError('FAO service rejected bounded request: '+str(data['error'].get('message','unknown')))
    return data

def dekad_window(name):
    match=re.fullmatch(r'ASIS\.ASI-D\.(\d{4})-(\d{2})-D([123])\.GS1\.LC-C',name)
    if not match: raise ValueError('Unknown ASIS date, crop mask or season')
    year,month,dekad=map(int,match.groups());day=(dekad-1)*10+1
    start=datetime(year,month,day,tzinfo=timezone.utc)
    end=datetime(year+int(month==12),1 if month==12 else month+1,1,tzinfo=timezone.utc) if dekad==3 else start.replace(day=day+10)
    return start,end

def decode_export(raw,width,height):
    with MemoryFile(raw) as memory,memory.open() as ds:
        if ds.count!=1 or ds.dtypes!=('float32',) or ds.crs.to_epsg()!=4326 or ds.scales!=(1.,) or ds.offsets!=(0.,):
            raise ValueError('Expected unrendered F32 WGS84 percentages')
        if (ds.width,ds.height)!=(width,height) or ds.transform.e>=0 or ds.transform.b or ds.transform.d: raise ValueError('Unexpected ASIS georeferencing')
        native=ds.read(1,masked=True)
        values=[None if np.ma.is_masked(v) or not math.isfinite(float(v)) or not 0<=float(v)<=100 else float(v) for v in native.flat]
        special=[None if np.ma.is_masked(v) or not math.isfinite(float(v)) or 0<=float(v)<=100 else int(v) if float(v).is_integer() and 101<=v<=255 else None for v in native.flat]
        lons=[ds.xy(0,c)[0] for c in range(width)];lats=[ds.xy(r,0)[1] for r in range(height)]
        return values,special,lons,lats,ds.bounds

def fetch_asis(now: datetime):
    item=request_json(ITEM)
    if item.get('url')!=BASE or item.get('type')!='Image Service' or 'Percent' not in item.get('description',''): raise ValueError('FAO ASIS identity/unit changed')
    service=request_json(BASE,{'f':'json'});legend=request_json(BASE+'/legend',{'f':'json'})
    query=request_json(BASE+'/query',{'where':"Land_Type='Cropland' AND Season='Season 1'",'outFields':'OBJECTID,Name,Year,Dekad,Year_Dekad,Season,Land_Type,Variable','returnGeometry':'false',
        'orderByFields':'Year DESC,Year_Dekad DESC','resultRecordCount':1,'f':'json'})
    attributes=query['features'][0]['attributes'];oid=attributes['OBJECTID'];start,end=dekad_window(attributes['Name'])
    if start>now: raise ValueError('ASIS indicator reference is in the future')
    raster_info=request_json(BASE+f'/{oid}/info',{'f':'json'})
    rule={'mosaicMethod':'esriMosaicLockRaster','lockRasterIds':[oid],'ascending':True}
    archive={'item':item,'service':service,'legend':legend,'query':query,'raster_info':raster_info,'views':{}}
    decoded=[]
    for region,(west_centre,north_centre,width,height) in VIEWS.items():
        # Native centres/bounds; coarse exports select provider overviews of unknown aggregation.
        px=raster_info['pixelSizeX'];py=raster_info['pixelSizeY'];origin=raster_info['origin']
        column=round((west_centre-origin['x'])/px-.5);row=round((origin['y']-north_centre)/py-.5)
        west=origin['x']+column*px;north=origin['y']-row*py
        bbox=','.join(map(str,[west,north-height*py,west+width*px,north]))
        params={'bbox':bbox,'bboxSR':4326,'imageSR':4326,'size':f'{width},{height}','format':'tiff','pixelType':'F32','interpolation':'RSP_NearestNeighbor','mosaicRule':json.dumps(rule),'renderingRule':json.dumps({'rasterFunction':'None'}),'f':'json'}
        export_url=BASE+'/exportImage?'+urlencode(params);export=request_json(BASE+'/exportImage',params)
        output=export['href']
        if urlparse(output).scheme!='https' or urlparse(output).hostname!='asis-esri.fao.org': raise ValueError('Untrusted numeric export URL')
        raw,_=download(output,max_bytes=1_000_000)
        values,special,lons,lats,bounds=decode_export(raw,width,height)
        present=[v for v in values if v is not None]
        if not present: raise ValueError('No numeric ASIS values in selected view')
        index=max((i for i,v in enumerate(values) if v is not None),key=lambda i:values[i]);x,y=lons[index%width],lats[index//width]
        probe=request_json(BASE+'/getSamples',{'geometry':json.dumps({'x':x,'y':y,'spatialReference':{'wkid':4326}}),'geometryType':'esriGeometryPoint','mosaicRule':json.dumps(rule),'renderingRule':json.dumps({'rasterFunction':'None'}),'returnFirstValueOnly':'true','f':'json'})
        sample=probe['samples'][0];expected=float(sample['value'])
        if sample['rasterId']!=oid or not math.isclose(expected,values[index],abs_tol=1e-5): raise ValueError('Independent native sample disagrees with exported percentage')
        archive['views'][region]={'export_request':export_url,'export_response':export,'tiff_base64':base64.b64encode(raw).decode(),'check':probe}
        grid=ScientificGrid(width=width,height=height,west=bounds.left,east=bounds.right,south=bounds.bottom,north=bounds.top,longitudes=lons,latitudes=lats,values=values,
            minimum=min(present),maximum=max(present),missing_cells=values.count(None),resolution=f'Recorte nativo ~1 km ({abs(lons[1]-lons[0]):g}°), 224×224 centros',
            sampling='Exportación numérica F32 a píxel nativo y bordes alineados con origen del ráster, rasterFunction None, OBJECTID bloqueado y vecino más cercano. No RGB ni promedio de áreas. El porcentaje se refiere a superficie cultivada de unidades administrativas, no a una observación independiente por celda.',
            quality_mask='Dominio porcentual 0–100; nodata/NaN y códigos especiales fuera de dominio quedan ausentes. Cero válido se conserva. La tabla numérica de clases del servicio respondió vacía: no se atribuye un significado específico no verificado a 251–255.',
            quality_values=special,quality_legend={str(v):'Código especial nativo fuera del dominio porcentual; transparente. Consultar leyenda FAO retenida; equivalencia individual no acreditada.' for v in sorted({v for v in special if v is not None})})
        # Hash the complete downloaded numeric view, not a thumbnail; generated output URL is not science.
        science_sha=hashlib.sha256(raw+json.dumps(attributes,sort_keys=True).encode()+b'percent-domain-0-100-v1').hexdigest()
        decoded.append((region,grid,expected,values[index],science_sha))
    raw=json.dumps(archive,ensure_ascii=False,separators=(',',':')).encode();sha=hashlib.sha256(raw).hexdigest();results=[]
    for region,grid,expected,actual,science_sha in decoded:
        key=f'd20-asi-{region}-s1'
        p=ScientificProduct(id=key,source_id='D20',title=f'ASI FAO · {region} · estación 1',collection_id=f'ASI_D/{oid}',product_version=attributes['Name'],variable='agricultural_stress_index',unit='% de superficie cultivada afectada',native_unit='porcentaje F32; sin conversión de escala',
            kind='indicator',representation='field',valid_from=start,valid_to=end,issue_time_basis='Ventana calendario UTC del dekad nominal del nombre; no es hora de adquisición ni emisión. El índice acumula estrés desde el inicio de la estación, variable por zona.',
            retrieved_at=now,ingested_at=now,original_url=archive['views'][region]['export_request'],license_url='https://www.fao.org/giews/earthobservation/access.jsp',attribution='© FAO Agricultural Stress Index System (ASIS) · CC BY 4.0 y condiciones adicionales FAO',
            checksum_sha256=sha,scientific_checksum_sha256=science_sha,byte_size=len(raw),raw_file=f'shared/{sha}.json',coverage='Cropland, Season 1; recorte nativo ~2° de Pampa. Bordes exactos en grid; no cobertura mundial acreditada.',
            cadence_seconds=86400,method_version='fao-asi-native-locked-f32-v1',limitation='Indicador externo de porcentaje de área agrícola con VHI<35 desde el comienzo del ciclo, con ponderación fenológica, según FAO. No es probabilidad, rendimiento, causa demostrada ni humedad del suelo. Solo Cropland/Season 1; referencia climatológica declarada por el ítem 1984–2024. La ventana nominal dekadal identifica la edición, no limita el período acumulado del índice. Los códigos especiales se conservan y enmascaran conservadoramente; su correspondencia individual con clases de leyenda no está publicada en la tabla consultada. La vista mundial gruesa no pasó el cotejo contra píxel nativo (overviews del proveedor): no se publica.',grid=grid,
            verification=Verification(method='Máximo porcentual de cada GeoTIFF sin renderer cotejado por coordenada con getSamples del ráster bloqueado; F32, CRS, escala y estación comprobados',original_url=BASE+'/getSamples',checked_at=now,expected=str(expected),actual=str(actual),passed=True))
        results.append(publish(p,raw,'.json'))
    return 'unchanged' if all(r=='unchanged' for r in results) else 'stored'
