"""Native LHASA regional nowcast through bounded, replayable GeoTIFF byte ranges."""
import hashlib
import math
import re
from datetime import datetime,timezone
import numpy as np
import rasterio
from rasterio.windows import Window
from earth_echo.connectors.http import download
from earth_echo.connectors.ranges import RangeSource,ArchivedRangeSource
from earth_echo.contracts.products import ScientificProduct,ScientificGrid,Verification
from earth_echo.storage.products import publish

BASE='https://portal.nccs.nasa.gov/datashare/landslides/nrt/hazard/tif/'

def fetch_lhasa(now: datetime) -> str:
    listing,_=download(BASE,max_bytes=500_000)
    names=sorted(set(re.findall(r'href="([^"]+\.tif)"',listing.decode())))
    names=[n for n in names if re.fullmatch(r'\d{8}T\d{4}\.tif',n) and datetime.strptime(n[:-4],'%Y%m%dT%H%M').replace(tzinfo=timezone.utc)<=now]
    if not names: raise ValueError('No dated LHASA product')
    name=names[-1]; source=RangeSource(BASE+name)
    def opener(path,mode='rb',**kwargs):
        if not str(path).endswith(name): raise FileNotFoundError(path)
        return source.open()
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR'),rasterio.open(source.url,opener=opener) as ds:
        if ds.crs.to_epsg()!=4326 or ds.descriptions[0]!='p_landslide' or ds.count!=1: raise ValueError('Unknown LHASA scientific band')
        r1,c1=ds.index(-124,50);r2,c2=ds.index(-123,51)
        window=Window(min(c1,c2),min(r1,r2),abs(c2-c1),abs(r2-r1))
        native=ds.read(1,window=window)
        row_indices=sorted(range(native.shape[0]),key=lambda r:ds.xy(int(window.row_off)+r,0)[1],reverse=True)
        cols=list(range(native.shape[1]))
        lats=[ds.xy(int(window.row_off)+r,0)[1] for r in row_indices]
        lons=[ds.xy(0,int(window.col_off)+c)[0] for c in cols]
        values=[None if not math.isfinite(float(native[r,c])) or native[r,c]==ds.nodata else float(native[r,c]) for r in row_indices for c in cols]
        present=[v for v in values if v is not None]
        if not present: raise ValueError('Regional LHASA window is entirely missing; no zero substitution')
        if min(present)<0 or max(present)>1: raise ValueError('LHASA p_landslide outside [0,1]')
        index=max((i for i,v in enumerate(values) if v is not None),key=lambda i:values[i])
        lat,lon=lats[index//len(cols)],lons[index%len(cols)]
        expected=float(next(ds.sample([(lon,lat)]))[0]); actual=values[index]
        if expected!=actual: raise ValueError('LHASA coordinate sample disagrees with array orientation')
        dx=lons[1]-lons[0];dy=lats[0]-lats[1]
        grid=ScientificGrid(width=len(cols),height=len(row_indices),west=lons[0]-dx/2,east=lons[-1]+dx/2,south=lats[-1]-dy/2,north=lats[0]+dy/2,
            longitudes=lons,latitudes=lats,values=values,minimum=min(present),maximum=max(present),missing_cells=values.count(None),resolution='Nativa 30 segundos de arco (~1 km), sin reducción en este recorte',
            sampling='Ventana nativa de GeoTIFF, filas ordenadas norte→sur desde el eje ascendente del proveedor. Sin promediar overviews; bloques HTTP originales conservados para replay local.',
            quality_mask='nodata=-9999 y NaN ausentes; ceros válidos se conservan. Sin observación no se declara terreno seguro.')
        metadata={'window':list(window.flatten()),'band':1,'description':ds.descriptions[0],'crs':str(ds.crs),'transform':list(ds.transform),'nodata':ds.nodata,'native_file_bytes':source.size}
    raw=source.archive(metadata)
    # A new reader reconstructs the same scalar entirely from retained provider blocks.
    replay=ArchivedRangeSource(raw)
    with rasterio.open(source.url,opener=lambda path,mode='rb':replay.open() if str(path).endswith(name) else (_ for _ in []).throw(FileNotFoundError(path))) as ds:
        if float(next(ds.sample([(lon,lat)]))[0])!=actual: raise ValueError('LHASA raw-block replay failed')
    sha=hashlib.sha256(raw).hexdigest()
    p=ScientificProduct(id='d24-lhasa-bc',source_id='D24',title='LHASA · Columbia Británica',collection_id='LHASA NRT hazard p_landslide',product_version=f'{name}; ETag={source.etag}; versión de modelo no codificada',
        variable='p_landslide',unit='1 (salida del modelo LHASA)',native_unit='p_landslide [0,1], definición LHASA',kind='indicator',representation='field',
        observed_at=datetime.strptime(name[:-4],'%Y%m%dT%H%M').replace(tzinfo=timezone.utc),retrieved_at=now,ingested_at=now,original_url=source.url,
        license_url='https://github.com/nasa/LHASA',attribution='NASA GSFC / LHASA / NCCS',checksum_sha256=sha,byte_size=len(raw),raw_file=f'd24-lhasa-bc/assets/{sha}.json',
        coverage='Recorte nativo ~1° de Columbia Británica (-124 a -123°, 50 a 51°). El original nominal abarca ±60°; este producto local no acredita el resto.',cadence_seconds=43200,
        method_version='lhasa-native-range-window-v1',limitation=f'Nowcast/modelo importado, no un deslizamiento observado ni una alerta geotécnica de cada ladera. La fecha es la referencia del archivo NRT, no hora de un evento. Se transfirieron {source.transferred} bytes en {source.requests} rangos de un GeoTIFF de {source.size} bytes; se conservan esos rangos, no el archivo mundial completo.',grid=grid,
        verification=Verification(method='Valor de máxima salida del recorte cotejado por coordenada y repetido con un lector nuevo desde bloques originales archivados',original_url=source.url,checked_at=now,expected=str(expected),actual=str(actual),passed=True))
    return publish(p,raw,'.json')
