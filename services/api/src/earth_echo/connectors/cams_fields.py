"""CAMS atmospheric composition through a measured public numeric distribution."""
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
from urllib.parse import urlencode
import zipfile
from earth_echo.connectors.http import download
from earth_echo.connectors.open_meteo import LICENSE, number, csv_sections, reserve_calls
from earth_echo.connectors.scientific_archive import pack_files
from earth_echo.contracts.products import ScientificProduct, ScientificGrid, Verification
from earth_echo.storage.products import publish, read_product, products_root

BASE = 'https://air-quality-api.open-meteo.com/v1/air-quality'
META = 'https://air-quality-api.open-meteo.com/data/cams_global/static/meta.json'
DOC = 'https://open-meteo.com/en/docs/air-quality-api'
METHOD = 'cams-global-native-centers-12deg-v1'
SOURCE = 'https://github.com/open-meteo/open-meteo/blob/b485547236a73d528b721f448d5d19a1b6bd15c5/Sources/App/Cams/'
LATITUDES = list(range(84, -85, -12))
LONGITUDES = list(range(-174, 175, 12))
COORDS = [(lat, lon) for lat in LATITUDES for lon in LONGITUDES]
BATCHES = [COORDS[i:i + 90] for i in range(0, len(COORDS), 90)]
VARIABLES = {
    'pm2_5': ('pm25', 'PM2,5 superficial', 'μg/m³', 'pm2p5, kg/m³ ×1e9 ya convertido por distribuidor'),
    'pm10': ('pm10', 'PM10 superficial', 'μg/m³', 'pm10, kg/m³ ×1e9 ya convertido por distribuidor'),
    'dust': ('dust-bin3', 'Polvo 0,9–20μm · fracción aermr06', 'μg/m³', 'aermr06 nivel137, kg/kg ×1,223803kg/m³ ×1e9 ya convertido por distribuidor; densidad fija aproximada'),
    'aerosol_optical_depth': ('aod550', 'Aerosoles en columna · AOD550', '', 'aod550, espesor óptico adimensional a550nm; escala1'),
}


def run_metadata(raw, now):
    meta = json.loads(raw)
    keys = ('last_run_initialisation_time', 'last_run_availability_time', 'last_run_modification_time', 'data_end_time')
    if any(type(meta.get(k)) is not int for k in keys) or 'WGS 84' not in meta.get('crs_wkt', '') or meta.get('temporal_resolution_seconds') != 3600 or meta.get('update_interval_seconds') != 43200:
        raise ValueError('CAMS global metadata/grid cadence changed')
    init, available, modified, end = [datetime.fromtimestamp(meta[k], timezone.utc) for k in keys]
    if init.hour not in (0, 12) or init.minute or init.second or not init <= available <= modified <= now - timedelta(minutes=10):
        raise ValueError('CAMS global run metadata not stable yet')
    if end < init + timedelta(hours=24):
        raise ValueError('CAMS domain does not contain chosen +24h instant')
    return init, available, modified, end


def request_url(init, batch):
    valid = (init + timedelta(hours=24)).strftime('%Y-%m-%dT%H:00')
    return BASE + '?' + urlencode({'latitude': ','.join(str(c[0]) for c in batch),
        'longitude': ','.join(str(c[1]) for c in batch), 'domains': 'cams_global',
        'hourly': ','.join(VARIABLES), 'start_hour': valid, 'end_hour': valid,
        'timezone': 'GMT', 'cell_selection': 'nearest', 'elevation': ','.join('nan' for _ in batch)})


def products_from_files(files, now):
    before = run_metadata(files['meta-before.json'], now)
    if before != run_metadata(files['meta-after.json'], now):
        raise ValueError('CAMS run changed during global subset retrieval')
    init, available, modified, _ = before
    valid = init + timedelta(hours=24)
    values = {key: [] for key in VARIABLES}
    coordinates = []
    urls = {'meta-before.json': META, 'meta-after.json': META}
    for batch_index, batch in enumerate(BATCHES):
        prefix = f'batch{batch_index:02}'
        url = request_url(init, batch)
        urls[prefix + '.json'], urls[prefix + '.csv'] = url, url + '&format=csv'
        locations = json.loads(files[prefix + '.json'])
        headers, rows = csv_sections(files[prefix + '.csv'])
        if not isinstance(locations, list) or len(locations) != len(batch) or len(headers) != len(batch) or len(rows) != len(batch):
            raise ValueError('CAMS JSON/CSV incomplete global subset batch')
        for i, (location, header, row, (lat, lon)) in enumerate(zip(locations, headers, rows, batch, strict=True)):
            if location.get('location_id', 0) != i or header['location_id'] != str(i) or row['location_id'] != str(i):
                raise ValueError('CAMS batch location IDs disagree')
            if location.get('timezone') != 'GMT' or location.get('timezone_abbreviation') != 'GMT' or location.get('utc_offset_seconds') != 0 or header['timezone'] != 'GMT' or header['timezone_abbreviation'] != 'GMT' or header['utc_offset_seconds'] != '0':
                raise ValueError('CAMS timestamps require GMT/UTC')
            for name, requested, origin in [('latitude', lat, -90), ('longitude', lon, -180)]:
                coord = number(location.get(name))
                if coord is None or coord != number(header[name]) or abs(coord - requested) > 4e-5 or abs(coord - (origin + round((coord - origin) / .4) * .4)) > 4e-5:
                    raise ValueError('CAMS native0.4-degree coordinates do not match independent requested centers/CSV')
            if number(location.get('elevation')) != number(header['elevation']):
                raise ValueError('CAMS omitted elevation/CSV NaN disagree')
            units = {'time': 'iso8601', **{key: spec[2] for key, spec in VARIABLES.items()}}
            if location.get('hourly_units') != units:
                raise ValueError('CAMS units changed; surface concentration and column AOD must remain separate')
            hourly = location['hourly']
            if set(hourly) != set(units) or hourly['time'] != [valid.strftime('%Y-%m-%dT%H:00')] or row['time'] != hourly['time'][0]:
                raise ValueError('CAMS instant/variable columns changed')
            for key, (_, _, unit, _) in VARIABLES.items():
                if len(hourly[key]) != 1:
                    raise ValueError('CAMS only one native-aligned forecast instant requested')
                value = number(hourly[key][0])
                if value != number(row[key + ' (' + unit + ')']):
                    raise ValueError('CAMS independent JSON/CSV value or mask disagrees')
                if value is not None and value < 0:
                    raise ValueError('CAMS negative concentration/AOD rejected; no zero fill')
                values[key].append(value)
            coordinates.append((location['latitude'], location['longitude']))
    lons = [coordinates[i][1] for i in range(len(LONGITUDES))]
    lats = [coordinates[i * len(LONGITUDES)][0] for i in range(len(LATITUDES))]
    if any((lat, lon) != (lats[i // len(lons)], lons[i % len(lons)]) for i, (lat, lon) in enumerate(coordinates)):
        raise ValueError('CAMS returned centers do not form the declared regular display grid')
    if set(files) != set(urls):
        raise ValueError('CAMS archive missing/unexpected assets')
    manifest = {'schema_version': '1', 'method': METHOD, 'domain': 'cams_global 0.4 degrees; no European/greenhouse variable requested',
        'assets': {name: {'url': urls[name], 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()} for name, raw in files.items()},
        'audited_provider_source': [SOURCE + p for p in ('CamsDomain.swift', 'CamsDownload.swift')],
        'source_scope': 'Audited mapping/transformation, not asserted deployed binary/IFS chemistry cycle.',
        'transform': {key: spec[3] for key, spec in VARIABLES.items()},
        'dust_definition': 'https://codes.ecmwf.int/grib/param-db/210006',
        'display_sampling': '450 exact native0.4-degree centers, every12degrees, no spatial mean/interpolation. One instant+24h, aligned to3h for ml137 dust. No hourly interpolation requested.',
        'license': LICENSE}
    raw = pack_files(files, manifest, compression=zipfile.ZIP_DEFLATED)
    sha = hashlib.sha256(raw).hexdigest()
    products = []
    for key, (suffix, title, native_unit, transform) in VARIABLES.items():
        field = values[key]
        present = [v for v in field if v is not None]
        grid = ScientificGrid(width=len(lons), height=len(lats), west=-180, east=180, south=-90, north=90,
            longitudes=lons, latitudes=lats, values=field, minimum=min(present) if present else None, maximum=max(present) if present else None, missing_cells=field.count(None),
            resolution='CAMS global nativo0,4° (~45km); vista mundial12° (30×15 centros)',
            sampling='Centros nativos cada30pasos de0,4°, lat84…−84/lon−174…174; bloques de90ubicaciones, orden norte→sur/oeste→este. Valor de centro, no media del área12° ni campo que resuelva extremos regionales. Sin interpolación espacial por Earth Echo. Plazo+24h alineado a3h; no horas intermedias interpoladas.',
            quality_mask='null en JSON/CSV→missing transparente; cero físico conservado. Sin flags por píxel proporcionados por el distribuidor, sin atribuir QA de observaciones satelitales al pronóstico. No relleno/interpolación de huecos.')
        science = {'run': [d.isoformat() for d in before], 'variable': key, 'coordinates': coordinates, 'values': field, 'method': METHOD}
        verification = Verification(method='450centros y1800valores/máscaras de cuatro variables cotejados entre JSON y CSV independientes, unidades y UTC. Georreferenciación contra retícula0,4° ECMWF y orden regular global. Metadata de dominio antes/después idéntica y≥10min desde modificación. Revisión del mapeo/unidades del distribuidor y parámetro primario aermr06.',
            original_url=urls['batch00.csv'], checked_at=now, expected='450centros WGS84×4variables; unidades superficiales/columna separadas; un plazo nativo alineado',
            actual=f'450/450centros y1800celdas/máscaras coincidentes; {key}: {len(present)}valores, {field.count(None)}ausentes', passed=True)
        products.append(ScientificProduct(id='d12-cams-global-' + suffix, source_id='D12', title=title + ' · CAMS · mundial',
            collection_id='CAMS Global Atmospheric Composition Forecast / Open-Meteo cams_global', product_version=f'cams_global 0.4deg / domain init {init.isoformat()} / modification {modified.isoformat()} / chemistry cycle not exposed',
            variable='dust_aermr06_fixed_density' if key == 'dust' else key, unit=native_unit or '1', native_unit=(native_unit or 'adimensional; API publica cadena de unidad vacía') + ' · ' + transform,
            kind='forecast', representation='field', initialized_at=init, issued_at=None, observed_at=None, valid_from=valid, valid_to=None,
            issue_time_basis=f'Inicialización del dominio {init.isoformat()}, disponibilidad del distribuidor {available.isoformat()}. Plazo instantáneo+24h {valid.isoformat()}, no promedio de24h. Emisión ECMWF no publicada:null. La API no expone ID de corrida por valor: asociación mediante metadata estable antes/después, con esa limitación. Ciclo químico IFS no expuesto, no se inventa su versión. generationtime_ms es latencia de API.',
            retrieved_at=now, ingested_at=now, original_url=DOC, license_url=LICENSE,
            attribution='Copernicus Atmosphere Monitoring Service / ECMWF; Weather data by Open-Meteo.com, CC BY4.0. Earth Echo selecciona450centros de la distribución numérica, conserva unidades convertidas por proveedor y documenta reducción visual12°.',
            checksum_sha256=sha, scientific_checksum_sha256=hashlib.sha256(json.dumps(science, sort_keys=True).encode()).hexdigest(), byte_size=len(raw), raw_file=f'shared/{sha}.zip',
            coverage='Mundial,450centros cada12° de la malla0,4° del pronóstico CAMS global, un instante+24h. Vista muy reducida; no resolución de barrios/calles ni cobertura científica continua a12° promediada.',
            cadence_seconds=43200, method_version=METHOD, grid=grid, verification=verification,
            limitation='Pronóstico externo CAMS global por Open-Meteo, distinto de cliente ADS o archivo nativo con ciclo químico/ID de corrida expuestos. Dominio global explícito evita selección automática europea; las cuatro variables solicitadas pertenecen al producto global atmosférico, no gases invernadero. '+
                ('Polvo: mapeo documentado aermr06, fracción0,9–20μm en nivel137, convertida kg/kg→μg/m³ con densidad fija1,223803kg/m³. No suma de todas las fracciones de polvo, PM10 o densidad local medida; esta aproximación del distribuidor limita interpretación. ' if key == 'dust' else
                 'AOD550 total de aerosoles en toda la columna atmosférica, adimensional a550nm. No concentración superficial, polvo exclusivamente, toxicidad o índice de calidad del aire. ' if key == 'aerosol_optical_depth' else
                 'Concentración de partículas cerca de superficie, no AOD en columna ni concentración individual medida; conversión kg/m³→μg/m³ ya aplicada por proveedor. ')+
                'Sin conversión duplicada, estaciones de superficie/calibración local, identificación causal de humo/incendios, tendencia, norma/ventana de promediado AQI o probabilidad de daño. No se fabrica AQI/alerta sanitaria. Un plazo instantáneo alineado a3h evita interpolación temporal del polvo; productos superficiales del distribuidor tienen resolución horaria. Vista12° toma centros sin promediar ni preservar extremos entre ellos; valores nativos pertinentes retenidos en JSON/CSV. Sin flags de calidad por celda adicionales, null ausente/cero válido. Acceso gratuito local no comercial, cadencia12h y cuota persistente moderada.'))
    return products, raw


def fetch_cams(now):
    before, _ = download(META, max_bytes=20_000)
    init, *_ = run_metadata(before, now)
    current = read_product('d12-cams-global-pm25', products_root())
    if current:
        cached_raw = (products_root() / current.raw_file).read_bytes()
        if hashlib.sha256(cached_raw).hexdigest() != current.checksum_sha256:
            raise ValueError('Retained CAMS original checksum changed; no unverified reuse')
        with zipfile.ZipFile(io.BytesIO(cached_raw)) as archive:
            cached = {name: archive.read(name) for name in json.loads(archive.read('manifest.json'))['assets']}
        if json.loads(cached['meta-before.json']) == json.loads(before):
            after, _ = download(META, max_bytes=20_000)
            if json.loads(after) == json.loads(before):
                # Re-run the actual decoder, allowing metadata/method repairs,
                # while retaining the time these scientific bytes were fetched.
                products, raw = products_from_files(cached, now)
                products = [p.model_copy(update={'retrieved_at': current.retrieved_at}) for p in products]
                results = [publish(p, raw, '.zip') for p in products]
                return 'unchanged' if all(r == 'unchanged' for r in results) else 'stored'
            before = after
            init, *_ = run_metadata(before, now)
    files = {'meta-before.json': before}
    for i, batch in enumerate(BATCHES):
        url = request_url(init, batch)
        for suffix, address in [('json', url), ('csv', url + '&format=csv')]:
            reserve_calls(locations=len(batch), variables=4, hours=1)
            files[f'batch{i:02}.' + suffix] = download(address, max_bytes=200_000)[0]
    files['meta-after.json'] = download(META, max_bytes=20_000)[0]
    products, raw = products_from_files(files, now)
    results = [publish(p, raw, '.zip') for p in products]
    return 'unchanged' if all(r == 'unchanged' for r in results) else 'stored'
