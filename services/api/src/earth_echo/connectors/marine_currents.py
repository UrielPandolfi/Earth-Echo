"""Native public CMEMS SMOC ranges: actual CF axes, hourly mean, and depth."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal, localcontext
import hashlib
import io
import json
import zipfile
import h5py
import numpy as np
import netCDF4
from earth_echo.connectors.ranges import RangeSource, ArchivedRangeSource
from earth_echo.connectors.hdf_native import native_window
from earth_echo.connectors.scientific_archive import pack_files
from earth_echo.contracts.products import ScientificProduct, ScientificGrid, ScientificCalculation, CalculationInput, Verification
from earth_echo.science.flow import mean_velocity_norm
from earth_echo.storage.products import publish, read_product, products_root

ROOT = 'https://s3.waw3-1.cloudferro.com/mdl-native-14/native/GLOBAL_ANALYSISFORECAST_PHY_001_024/'
COLLECTION = 'cmems_mod_glo_phy_anfc_merged-uv_PT1H-i_202211'
DOC = 'https://data.marine.copernicus.eu/product/GLOBAL_ANALYSISFORECAST_PHY_001_024/description'
LICENSE = 'https://marine.copernicus.eu/user-corner/service-commitments-and-licence'
METHOD = 'cmems-smoc-native-northwest-1deg-v1'
GLOBAL_METHOD = 'cmems-smoc-native-global-1deg-v2'
VARIABLES = {
    'utotal': ('u-total', 'Componente este · corriente total SMOC', 'surface_sea_water_x_velocity'),
    'vtotal': ('v-total', 'Componente norte · corriente total SMOC', 'surface_sea_water_y_velocity'),
    'uo': ('u-eulerian', 'Componente este · corriente euleriana', 'eastward_sea_water_velocity'),
    'vo': ('v-eulerian', 'Componente norte · corriente euleriana', 'northward_sea_water_velocity'),
}


class UsedRanges(ArchivedRangeSource):
    def __init__(self, raw):
        super().__init__(raw); self.used = set()

    def read_at(self, offset, length):
        end = min(self.size, offset + length)
        if end > offset:self.used.update(range(offset // self.block_size * self.block_size, end, self.block_size))
        return super().read_at(offset, length)


def attr(value):
    if isinstance(value, bytes):return value.decode('utf8')
    if isinstance(value, np.ndarray) and value.size == 1:return attr(value.flat[0])
    return str(value)


def scientific_url(day):
    valid = day + timedelta(days=1)
    return ROOT + COLLECTION + f'/{valid:%Y/%m}/SMOC_{valid:%Y%m%d}_R{day:%Y%m%d}.nc'


def decode(source, day, *, worldwide=False):
    if source.url != scientific_url(day) or not source.etag or source.etag.startswith('W/'):
        raise ValueError('SMOC native URL/strong object version missing')
    with source.open() as reader, h5py.File(reader, 'r') as ds:
        if attr(ds.attrs.get('Conventions')) != 'CF-1.6' or attr(ds.attrs.get('institution')) != 'MERCATOR OCEAN' or attr(ds.attrs.get('source')) != 'MERCATOR GLO12, mfwamglo, FES2014' or 'hourly mean merged surface currents' not in attr(ds.attrs.get('title')):
            raise ValueError('SMOC native collection/source/mean metadata changed')
        lon, lat = ds['longitude'][...], ds['latitude'][...]
        expected_lon = (-180 + np.arange(4320) / 12).astype('f4')
        expected_lat = (-80 + np.arange(2041) / 12).astype('f4')
        if attr(ds['longitude'].attrs.get('units')) != 'degrees_east' or attr(ds['latitude'].attrs.get('units')) != 'degrees_north' or not np.array_equal(lon, expected_lon) or not np.array_equal(lat, expected_lat):
            raise ValueError('SMOC independent native CF axes disagree; no broker half-cell shift')
        depth = ds['depth'][...]
        if depth.shape != (1,) or attr(ds['depth'].attrs.get('units')) != 'm' or attr(ds['depth'].attrs.get('positive')) != 'Down' or depth[0] != np.float32(.494025):
            raise ValueError('SMOC surface depth changed')
        time = ds['time'][...]; units = attr(ds['time'].attrs.get('units'))
        if units != 'hours since 1950-01-01 00:00:00' or attr(ds['time'].attrs.get('calendar')) != 'gregorian' or len(time) != 24:
            raise ValueError('SMOC CF hourly time encoding changed')
        times = [datetime(1950, 1, 1, tzinfo=timezone.utc) + timedelta(hours=float(t)) for t in time]
        independent = netCDF4.num2date(time, units, calendar='gregorian', only_use_cftime_datetimes=False, only_use_python_datetimes=True)
        if times != [t.replace(tzinfo=timezone.utc) for t in independent] or times != [day + timedelta(days=1, minutes=30, hours=i) for i in range(24)]:
            raise ValueError('SMOC native CF timestamp/filename do not agree')
        # Keep the qualified northwest edition reproducible from its frozen
        # archive; production now requests one global surface hour, not3D/time.
        r0, r1, c0, c1 = (0,2041,0,4320) if worldwide else (1021,2041,0,2160)
        rows = np.array([int(np.argmin(abs(lat-y))) for y in np.arange(89.5,-79.6 if worldwide else 5.4,-1)])
        cols = np.array([int(np.argmin(abs(lon-x))) for x in np.arange(-179.5,180 if worldwide else 0,1)])
        values = {}; fills = {}
        for name in VARIABLES:
            variable = ds[name]
            if variable.shape != (24, 1, 2041, 4320) or variable.dtype != np.dtype('<f4') or variable.chunks != (1, 1, 1021, 2160) or attr(variable.attrs.get('units')) != 'm s-1' or attr(variable.attrs.get('standard_name')) != VARIABLES[name][2]:
                raise ValueError('SMOC velocity shape/units/meaning changed')
            if float(variable.attrs.get('scale_factor', 1)) != 1 or float(variable.attrs.get('add_offset', 0)) != 0:
                raise ValueError('SMOC unexpected scale/offset; no double conversion')
            fill = float(np.asarray(variable.attrs['_FillValue']).item()); fills[name] = fill
            manual = native_window(variable, (0, 0), r0, r1, c0, c1)
            library = variable[0, 0, r0:r1, c0:c1]
            if not np.array_equal(manual.view('u4'), library.view('u4')):
                raise ValueError('SMOC HDF5 independent raw chunk decoding disagrees bitwise')
            field = manual[np.ix_(rows-r0, cols-c0)]
            values[name] = [None if not np.isfinite(v) or float(v) == fill else float(v) for v in field.ravel()]
        metadata = {'collection': COLLECTION, 'native_source': attr(ds.attrs['source']), 'CF': 'CF-1.6', 'depth_m': float(depth[0]),
            'time_units': units, 'calendar': 'gregorian', 'time_coordinate': times[0].isoformat(),
            'temporal_statistic': 'hourly mean; original file has no explicit time_bounds, no averaging interval endpoints invented',
            'production_day_from_filename': day.date().isoformat(), 'initialization_time': None, 'issued_at': None,
            'native_latitude_limits': [float(lat[r0]), float(lat[r1-1])], 'native_longitude_limits': [float(lon[c0]), float(lon[c1-1])],
            'retained_components': list(VARIABLES), 'native_values_bitwise_checked': 4 * (r1-r0) * (c1-c0),
            'sampling': '1-degree view uses exact native1/12-degree centers, no spatial averaging. '+('Global model ocean domain80S–90N; original missing mask, not observations or local predictive validation.' if worldwide else 'Northwest quadrant only, not worldwide coverage.'),
            'fills': fills, 'method': GLOBAL_METHOD if worldwide else METHOD}
    return values, lon[cols].tolist(), lat[rows].tolist(), times[0], metadata


def products_from_ranges(range_bytes, day, retrieved_at, now, *, worldwide=False):
    source = UsedRanges(range_bytes)
    values, lons, lats, stamp, metadata = decode(source, day, worldwide=worldwide)
    # Retain only bytes actually needed to replay this qualified decoding.
    source.cache = {offset: source.cache[offset] for offset in sorted(source.used)}
    native = source.archive(metadata)
    raw = pack_files({'smoc.ranges.json': native}, {'schema_version': '1', 'assets': {'smoc.ranges.json': {
        'url': source.url, 'original_object_bytes': source.size, 'etag': source.etag, 'last_modified': source.modified,
        'retained_range_bytes': sum(len(v) for v in source.cache.values()), 'range_blocks': len(source.cache),
        'sha256': hashlib.sha256(native).hexdigest()}}, 'method': metadata['method'], 'native_metadata': metadata}, compression=zipfile.ZIP_DEFLATED)
    sha = hashlib.sha256(raw).hexdigest(); products = []
    for name, (suffix, title, standard_name) in VARIABLES.items():
        field = values[name]; present = [v for v in field if v is not None]
        grid = ScientificGrid(width=len(lons), height=len(lats), west=-180, east=180 if worldwide else 0, south=-80 if worldwide else 5, north=90,
            longitudes=lons, latitudes=lats, values=field, minimum=min(present) if present else None, maximum=max(present) if present else None, missing_cells=field.count(None),
            resolution=f'Nativo1/12° (~8–9km); vista1° ({len(lons)}×{len(lats)}centros)', sampling=metadata['sampling']+(' Centros lon−179,5…179,5/lat89,5…−79,5.' if worldwide else ' Centros lon−179,5…−0,5/lat89,5…5,5.')+' Sólo hora0/depth0.494025m. Posiciones CF originales.',
            quality_mask=f'_FillValue nativo {metadata["fills"][name]} o no finito→missing transparente. Cero y componentes negativas válidas. Sin flags de calidad adicionales; máscara de soporte no significa validación local.')
        count=metadata['native_values_bitwise_checked']
        verification = Verification(method=f'HDF5/h5py frente a decodificación independiente de chunks crudos con zlib y deshacer shuffle;{count}Float32 coinciden bit a bit, incluidos rellenos. Ejes nativos completos cotejados con fórmula regular1/12°; tiempos CF1950 con timedelta y netCDF4 independientes. Profundidad, unidades, objetoETag y coordenadas conservados.',
            original_url=source.url, checked_at=now, expected=f'{count}Float32 bitwise; CF/time/depth y relleno nativos',
            actual=f'{count}valores coincidentes; {name}: {len(present)} centros visibles válidos/{len(field)}; tiempo {stamp.isoformat()}; depth {metadata["depth_m"]}m', passed=True)
        products.append(ScientificProduct(id='d14-smoc-' + suffix, source_id='D14', title=title + (' · mundial' if worldwide else ' · océano norte occidental'),
            collection_id='GLOBAL_ANALYSISFORECAST_PHY_001_024 / ' + COLLECTION, product_version=f'edition202211 / filename R{day:%Y%m%d} / ETag{source.etag} / CF1.6',
            variable=name + ' / ' + standard_name, unit='m/s', native_unit='m s-1; Float32, sin escala/offset, least_significant_digit3 nativo', kind='forecast', representation='field',
            initialized_at=None, issued_at=None, observed_at=None, valid_from=stamp, valid_to=None,
            issue_time_basis=f'Coordenada temporal nativa {stamp.isoformat()} de un campo de media horaria; no observación instantánea. Archivo no contiene time_bounds: no se inventan extremos del promedio. CF horas desde1950, calendario gregorian, zona predeterminada CF=UTC. R{day:%Y%m%d} identifica día de producción del archivo, sin hora de inicialización/emisión acreditada: ambas null. Last-Modified del objeto es modificación de distribución, no emisión científica.',
            retrieved_at=retrieved_at, ingested_at=now, original_url=DOC, license_url=LICENSE,
            attribution='E.U. Copernicus Marine Service Information (CMEMS), Mercator Ocean; fuentes nativas MERCATOR GLO12, mfwamglo, FES2014. Subconjunto y selección de centros por Earth Echo, originales por rangos conservados.',
            checksum_sha256=sha, scientific_checksum_sha256=hashlib.sha256(json.dumps({'etag': source.etag, 'url': source.url, 'variable': name, 'values': field, 'metadata': metadata}, sort_keys=True).encode()).hexdigest(),
            byte_size=len(raw), raw_file=f'shared/{sha}.zip', coverage=('Dominio oceánico mundial del modelo:80°S–90°N,180°O–180°E, vista360×170centros1° desde malla1/12°, una media horaria superficial a0,494025m. Máscara nativa; sin perfiles verticales, otras horas o transporte de sección completo.' if worldwide else 'Subconjunto norte occidental del modelo global:5–90°N,180–0°O, vista1° desde centros1/12°, una media horaria superficial a0,494025m. No cobertura mundial, perfiles verticales ni toda una sección de transporte.'),
            cadence_seconds=86400, method_version=metadata['method'], grid=grid, verification=verification,
            limitation='Pronóstico físico externo SMOC nativo, medias horarias superficiales; no corriente observada, trayectoria de objeto o modelo propio validado. '+
                ('Componente total incluye circulación euleriana, deriva de oleaje y marea; no se confunde con corriente euleriana sola. ' if name in ('utotal', 'vtotal') else 'Componente euleriana separada de marea/deriva de oleaje; no se sustituye por componente total SMOC. ')+
                f'Profundidad real0,494025m y coordenada temporal00:30UTC del archivo conservadas, sin asignar inicialización/emisión a medianoche desde nombre R. Máscara de relleno no acredita calidad local o ausencia de error. Vista1° no conserva extremos entre centros; valores nativos pertinentes reproducibles desde rangos de {16 if worldwide else 4} chunks. El objeto completo tiene{source.size}B y no se descarga completo; ETag multipart fuerte conserva versión, no se afirma SHA del archivo completo. No salinidad/temperatura, oxígeno, HAB/toxicidad, inundación costera, transporte AMOC o colapso inferidos de estas componentes.'))
    for suffix, pair, title in [('speed-total', ('utotal', 'vtotal'), 'Norma de corriente media total SMOC'), ('speed-eulerian', ('uo', 'vo'), 'Norma de corriente media euleriana')]:
        first, second = [products[list(VARIABLES).index(k)] for k in pair]
        field = [mean_velocity_norm(a, b) for a, b in zip(first.grid.values, second.grid.values, strict=True)]
        present = [v for v in field if v is not None]
        index = next(i for i, value in enumerate(field) if value is not None)
        with localcontext() as context:
            context.prec = 50
            a, b = Decimal(str(first.grid.values[index])), Decimal(str(second.grid.values[index]))
            independent = float((a*a + b*b).sqrt())
        if abs(independent - field[index]) > 1e-14:
            raise ValueError('Independent SMOC Decimal vector norm disagrees')
        calculation = ScientificCalculation(method_version='mean-horizontal-velocity-norm-v1', formula='sqrt(mean(u)² + mean(v)²)', parameters={},
            inputs=[CalculationInput(product_id=p.id, variable=p.variable, unit=p.unit, checksum_sha256=p.checksum_sha256) for p in (first, second)], reference_url=DOC,
            reference_period=f'Misma media horaria de componentes, coordenada CF {stamp.isoformat()}, sin climatología o período de referencia para anomalías.',
            applicability='Norma del vector horizontal medio a0,494025m. No es media de las rapideces instantáneas, corriente máxima, probabilidad o nuevo modelo predictivo. Missing si falta una componente.')
        grid = first.grid.model_copy(update={'values': field, 'minimum': min(present), 'maximum': max(present), 'missing_cells': field.count(None), 'quality_mask': 'Máscara conjunta de u/v; hueco si falta cualquiera. Cero de ambas→norma cero válida.'})
        products.append(first.model_copy(update={'id': 'd14-smoc-' + suffix, 'title': title + ' · calculada', 'variable': suffix,
            'scientific_checksum_sha256': hashlib.sha256(json.dumps({'inputs': [first.scientific_checksum_sha256, second.scientific_checksum_sha256], 'formula': calculation.formula}).encode()).hexdigest(),
            'grid': grid, 'calculation': calculation, 'method_version': calculation.method_version, 'limitation': first.limitation+' Norma calculada de vector medio, no media de rapidez instantánea. No modelo entrenado ni validación predictiva.',
            'verification': first.verification.model_copy(update={'method': first.verification.method+' Norma por math.hypot cotejada con Decimal50 independiente.', 'expected': str(independent), 'actual': str(field[index])})}))
    return products, raw


def fetch_marine_currents(now):
    if now.tzinfo is None:raise ValueError('SMOC retrieval requires an aware UTC timestamp')
    now = now.astimezone(timezone.utc)
    # Official product updates daily; before12UTC keep using preceding production day.
    day = now.replace(hour=0, minute=0, second=0, microsecond=0) - (timedelta(days=1) if now.hour < 12 else timedelta())
    url = scientific_url(day)
    source = RangeSource(url, max_bytes=41_943_040, max_requests=320, deadline_seconds=540)
    current = read_product('d14-smoc-u-total', products_root())
    retrieved_at = now
    if current:
        raw = (products_root() / current.raw_file).read_bytes()
        if hashlib.sha256(raw).hexdigest() != current.checksum_sha256:
            raise ValueError('SMOC retained archive checksum changed')
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:cached = archive.read('smoc.ranges.json')
        previous = ArchivedRangeSource(cached)
        if (previous.url, previous.size, previous.etag) == (source.url, source.size, source.etag):
            source.cache.update(previous.cache); retrieved_at = current.retrieved_at
    # Six outputs share16native compressed surface chunks, not the whole file.
    decode(source, day, worldwide=True)
    products, raw = products_from_ranges(source.archive({}), day, retrieved_at, now, worldwide=True)
    results = [publish(p, raw, '.zip') for p in products]
    return 'unchanged' if all(r == 'unchanged' for r in results) else 'stored'
