"""One published IMERG Final climatology, explicitly NOT recent rainfall."""
import hashlib
import io
import zipfile
from datetime import datetime, timezone
import h5py
import numpy as np
import rasterio
from earth_echo.connectors.http import download
from earth_echo.connectors.scientific_archive import pack_files
from earth_echo.contracts.products import ScientificProduct, ScientificGrid, Verification
from earth_echo.storage.products import publish

PAGE = 'https://gpm.nasa.gov/data/imerg/precipitation-climatology'
BASE = 'https://gpm.nasa.gov/sites/default/files/data/climatologies/2024/'
STEM = 'IMERG-Final.CLIM.200006-202305.V07B'
DOC = 'https://gpm.nasa.gov/resources/documents/imerg-v07-daily-and-grand-climatology-products-documentation'
KEY = 'd01-imerg-grand-climatology'


def text(value):
    return value.decode() if isinstance(value, bytes) else str(value)


def member(raw, name, limit):
    # NASA's NetCDF archive also contains AppleDouble metadata; never extract it.
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if len(archive.infolist()) > 5 or sum(i.file_size for i in archive.infolist()) > limit:
            raise ValueError('IMERG original archive exceeds budget')
        return archive.read(name)


def decode_climatology(nc_zip, tif_zip):
    nc_raw = member(nc_zip, STEM+'.nc4', 20_000_000)
    tif_raw = member(tif_zip, STEM+'.tif', 30_000_000)
    worldfile = member(tif_zip, STEM+'.tfw', 30_000_000)
    with h5py.File(io.BytesIO(nc_raw), 'r') as nc:
        metadata = {k: text(nc.attrs[k]) for k in ('title','description','source','version','history','comment','author')}
        if metadata['version'] != 'V07B' or metadata['source'] != 'IMERG Final Daily Precipitation (10.5067/GPM/IMERGDF/DAY/07)':
            raise ValueError('IMERG Final edition/source changed; review required')
        if metadata['description'] != 'Average of all valid daily precipitation from June 2000 to May 2023 at every 0.1 deg.':
            raise ValueError('IMERG climatology reference period changed')
        if metadata['history'] != 'File created on 2024-01-17 12:49:44 UTC.':
            raise ValueError('IMERG climatology creation metadata changed; review required')
        lat, lon = nc['lat'][:], nc['lon'][:]
        if lat.shape != (1800,) or lon.shape != (3600,) or not np.allclose(lat, np.arange(1800)*.1-89.95, atol=1e-5, rtol=0) or not np.allclose(lon, np.arange(3600)*.1-179.95, atol=1e-5, rtol=0):
            raise ValueError('Unexpected IMERG native coordinates')
        if text(nc['lat'].attrs['units']) != 'degrees_north' or text(nc['lon'].attrs['units']) != 'degrees_east':
            raise ValueError('Unexpected IMERG coordinate units')
        var = nc['precipitation']
        if var.shape != (3600,1800) or text(var.attrs['units']) != 'mm / yr' or text(var.attrs['coordinates']) != 'lat lon':
            raise ValueError('Unexpected IMERG precipitation dimensions/units')
        fill = float(np.asarray(var.attrs['_FillValue']).item())
        if fill != float(np.float32(-9999.9)) or float(np.asarray(var.attrs.get('scale_factor', 1)).item()) != 1 or float(np.asarray(var.attrs.get('add_offset', 0)).item()) != 0:
            raise ValueError('Unexpected IMERG packing or missing value')
        native = var[:].T[::-1]  # lon/lat asc -> north/south rows, west/east cols.
    with rasterio.open(io.BytesIO(tif_raw)) as tif:
        transform = tuple(tif.transform)[:6]
        if (tif.width,tif.height,tif.count,tif.dtypes,tif.crs.to_epsg()) != (3600,1800,1,('float32',),4326) or not np.allclose(transform,(.1,0,-180,0,-.1,90),atol=2e-9,rtol=0):
            raise ValueError('Independent IMERG TIFF georeferencing differs')
        # This original TIFF has no GDAL nodata tag. The explicit NetCDF fill and
        # publisher documentation define missingness, independently of its mask.
        independent = tif.read(1)
        if not np.array_equal(native, independent, equal_nan=True):
            raise ValueError('Independent IMERG TIFF values/missing mask disagree')
    if worldfile == b'0.1\n0\n0\n***\n-179.95\n  89.95\n':
        metadata['worldfile_status'] = 'El WorldFile original contiene *** en el paso vertical: inutilizable y excluido de georreferenciación. Se conservan sus bytes; no se corrigen ni se usan como prueba. CRS/transform TIFF y ejes CF sí coinciden.'
    else:
        tfw = [float(v) for v in worldfile.split()]
        if len(tfw)!=6 or not np.allclose(tfw,(.1,0,0,-.1,-179.95,89.95),atol=1e-6,rtol=0):
            raise ValueError('IMERG independent WorldFile differs')
        metadata['worldfile_status'] = 'WorldFile numérico cotejado con CRS/transform TIFF y ejes CF.'
    valid = (native != fill) & np.isfinite(native)
    if not valid.any() or (native[valid] < 0).any():
        raise ValueError('Invalid nonmissing IMERG precipitation')
    # Regular 1-degree footprint using every tenth native centre. Native cell
    # centres are 0.05 degrees southwest of footprint centres, stated explicitly.
    selected = native[5::10,4::10]
    values = [float(v) if v != fill and np.isfinite(v) else None for v in selected.flat]
    present = [v for v in values if v is not None]
    grid = ScientificGrid(width=360,height=180,west=-180,east=180,south=-90,north=90,
        longitudes=[-179.5+i for i in range(360)],latitudes=[89.5-i for i in range(180)],values=values,
        minimum=min(present),maximum=max(present),missing_cells=values.count(None),
        resolution='Producto IMERG 0,1°; vista 1°. Climatología, no lluvia del día.',
        sampling='Submuestreo regular cada 10 centros nativos; cada huella visual 1° toma el centro nativo 0,05° al sur/oeste de su centro. Sin promediar ni interpolar. Los 6.480.000 valores científicos permanecen en los originales NetCDF/GeoTIFF conservados.',
        quality_mask='Relleno NetCDF −9999,9 y no finitos permanecen ausentes; cero válido permanece cero. NASA exige ≥90% de entradas válidas en el período para publicar un valor. TIFF sin nodata explícito: máscara cotejada con NetCDF/documentación, no inferida de océano, color o cero. Sin incertidumbre o flags por celda adicionales.')
    # A separate per-coordinate TIFF sample verifies display indexing as well.
    row,col = 125,118
    expected = float(independent[row*10+5,col*10+4])
    actual = grid.values[row*360+col]
    if expected != actual:
        raise ValueError('IMERG display coordinate sample differs')
    return grid,metadata,{'native_missing':int((~valid).sum()),'latitude':float(lat[1799-(row*10+5)]),'longitude':float(lon[col*10+4]),'expected':expected,'actual':actual}


def product_from_originals(files, now: datetime, *, retrieved_at: datetime | None = None):
    assets = {name:{'url':BASE+name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)} for name,raw in files.items()}
    grid,metadata,check = decode_climatology(files[STEM+'.nc4.zip'],files[STEM+'.tif.zip'])
    raw = pack_files(files,{'schema_version':'1','assets':assets,'native_metadata':metadata})
    sha = hashlib.sha256(raw).hexdigest()
    product = ScientificProduct(id=KEY,source_id='D01',title='Precipitación media anual · climatología IMERG Final · 2000–2023',
        collection_id=STEM,product_version='V07B; creación 2024-01-17',variable='climatological_precipitation',unit='mm/año',native_unit='mm / yr',kind='historical',representation='field',
        observed_at=datetime(2000,6,1,tzinfo=timezone.utc),observation_end=datetime(2023,6,1,tzinfo=timezone.utc),
        issued_at=None,issue_time_basis='Período climático [junio 2000, junio 2023), extremo final exclusivo. Creación original literal '+metadata['history']+' No es emisión de forecast ni disponibilidad de lluvia reciente.',
        retrieved_at=retrieved_at or now,ingested_at=now,original_url=BASE+STEM+'.nc4.zip',license_url=DOC,
        attribution='NASA IMERG Algorithm Team / PPS / GES DISC, Jackson Tan y George J. Huffman. IMERG V07 Daily and Grand Climatology Products; producto diario fuente doi:10.5067/GPM/IMERGDF/DAY/07. Dominio público según autores.',
        checksum_sha256=sha,byte_size=len(raw),raw_file=f'shared/{sha}.zip',
        coverage='Climatología mundial de precipitación media anual, junio 2000–mayo 2023; no todas las celdas polares cumplen la cobertura mínima. Un campo histórico agregado, no observaciones actuales.',
        cadence_seconds=2592000,method_version='imerg-final-v07b-grand-climatology-nearest-v1',grid=grid,
        limitation='Referencia histórica de precipitación media anual IMERG Final V07B, junio 2000–mayo 2023. No representa lluvia reciente, el acumulado de un año concreto, tendencia ni pronóstico. Final incorpora calibración tardía: no reproduce la información disponible en tiempo real. Sin observaciones recientes compatibles no habilita anomalías, SPI, probabilidades ni detección de extremos/sequía. NASA exige ≥90% de entradas válidas; no se descargaron conteos o incertidumbre por celda. Se cotejaron todos los valores, máscaras y coordenadas NetCDF/TIFF. Un archivo auxiliar WorldFile defectuoso se conserva y excluye; los ejes CF y la georreferenciación interna del TIFF coinciden. IMERG Early/Late/Final recientes siguen pendientes de acceso Earthdata/PPS y conector separado.',
        verification=Verification(method='Todos los nodos/máscaras cotejados entre NetCDF/h5py (lon,lat ascendente) y GeoTIFF/rasterio (lat norte→sur), CRS/transform coincidentes con ejes CF. WorldFile defectuoso excluido. Celda de visualización cotejada por su índice/coordenada nativos. No valida la habilidad del producto.',
            original_url=BASE+STEM+'.tif.zip',checked_at=now,
            expected=f'6480000 nodos; TIFF {check["expected"]} mm/año en {check["latitude"]}°, {check["longitude"]}°',
            actual=f'6480000 nodos coincidentes; {check["native_missing"]} ausentes nativos; celda {check["actual"]} mm/año',passed=True))
    return product,raw


def fetch_imerg_climatology(now: datetime):
    listing,_ = download(PAGE,max_bytes=250_000)
    files = {}
    for ext,limit in [('nc4',22_000_000),('tif',30_000_000)]:
        name = STEM+'.'+ext+'.zip'
        if BASE.removeprefix('https://gpm.nasa.gov')+name not in listing.decode(errors='replace'):
            raise ValueError('Official IMERG climatology scientific link changed')
        files[name],_ = download(BASE+name,max_bytes=limit)
    product,raw = product_from_originals(files,now)
    return publish(product,raw,'.zip')
