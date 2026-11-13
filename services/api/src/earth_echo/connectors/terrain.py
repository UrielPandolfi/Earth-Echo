"""A single public GLO-90 tile as static DSM context, not terrain for flood prediction."""
import hashlib
from datetime import datetime
import math
import numpy as np
from rasterio.io import MemoryFile
from earth_echo.connectors.http import download
from earth_echo.contracts.products import ScientificGrid,ScientificProduct,Verification
from earth_echo.storage.products import publish

TILE='Copernicus_DSM_COG_30_S36_00_W063_00_DEM'
URL=f'https://copernicus-dem-90m.s3.amazonaws.com/{TILE}/{TILE}.tif'

def fetch_dem(now: datetime) -> str:
    raw,headers=download(URL,max_bytes=8_000_000)
    with MemoryFile(raw) as memory, memory.open() as ds:
        if ds.crs.to_epsg()!=4326 or ds.count!=1 or ds.transform.b or ds.transform.d or ds.transform.a<=0 or ds.transform.e>=0:
            raise ValueError('Unsupported native DEM georeferencing')
        if ds.scales[0]!=1 or ds.offsets[0]!=0: raise ValueError('Unknown DSM scale')
        # Read native pixels, not COG overviews (the distributor's overviews are averages).
        native=ds.read(1,masked=True)
        rows=list(range(2,ds.height,5)); cols=list(range(2,ds.width,5))
        lons=[ds.xy(0,c)[0] for c in cols]; lats=[ds.xy(r,0)[1] for r in rows]
        values=[None if np.ma.is_masked(native[r,c]) or not math.isfinite(float(native[r,c])) else float(native[r,c]) for r in rows for c in cols]
        dx=lons[1]-lons[0]; dy=lats[0]-lats[1]
        reference=float(next(ds.sample([(lons[0],lats[0])]))[0]); actual=values[0]
        if not math.isclose(actual,reference,abs_tol=1e-5): raise ValueError('Independent coordinate sample disagrees with array')
        present=[v for v in values if v is not None]
        grid=ScientificGrid(width=len(cols),height=len(rows),west=lons[0]-dx/2,east=lons[-1]+dx/2,south=lats[-1]-dy/2,north=lats[0]+dy/2,
            longitudes=lons,latitudes=lats,values=values,minimum=min(present),maximum=max(present),missing_cells=values.count(None),
            resolution='GLO-90, 3 segundos de arco nativos (~90 m); vista cada 5 centros (~450 m)',
            sampling='Submuestreo de la banda nativa, sin usar overviews promediados. GeoTIFF conserva 1200×1200 centros, etiqueta PixelIsPoint y transformación exacta.',
            quality_mask='Máscara/nodata del GeoTIFF. Cero válido se conserva. DSM incluye vegetación y construcciones; no se infiere calidad vertical desde resolución.')
        version=f'GLO-90 COG; ETag={headers.get("ETag",headers.get("Etag","no informado"))}'
    sha=hashlib.sha256(raw).hexdigest()
    p=ScientificProduct(id='d30-dem-pampa',source_id='D30',title='Relieve DSM GLO-90 · Pampa',collection_id=TILE,product_version=version,variable='surface_elevation',unit='m sobre EGM2008',native_unit='m sobre EGM2008 (EPSG 3855)',
        kind='static_context',representation='field',retrieved_at=now,ingested_at=now,original_url=URL,license_url='https://copernicus-dem-90m.s3.amazonaws.com/readme.html',
        attribution='Copernicus DEM · DLR / Airbus Defence and Space · Unión Europea / ESA',checksum_sha256=sha,byte_size=len(raw),raw_file=f'd30-dem-pampa/assets/{sha}.tif',
        coverage='Una tesela de ~1° de Pampa, sudoeste -63°, -36°. Extensión exacta y ajuste de PixelIsPoint en grid; no descarga mundial.',cadence_seconds=2592000,
        method_version='glo90-native-centres-v2',limitation='Contexto estático de superficie; alturas ortométricas EGM2008 según Product Handbook 5.0 de Copernicus DEM (https://dataspace.copernicus.eu/sites/default/files/media/files/2024-06/geo1988-copernicusdem-spe-002_producthandbook_i5.0.pdf). Sin fecha de adquisición por píxel en este COG. No es terreno desnudo, altura elipsoidal, nivel del agua ni modelo hidráulico. Distribuidor identifica colección 2021; la edición DGED no está codificada en la tesela: se identifica archivo por ETag y SHA-256.',grid=grid,
        verification=Verification(method='Valor de la banda nativa cotejado con muestreo por coordenada independiente; CRS/transformación/PixelIsPoint leídos del GeoTIFF',original_url=URL,checked_at=now,expected=str(reference),actual=str(actual),passed=True))
    return publish(p,raw,'.tif')
