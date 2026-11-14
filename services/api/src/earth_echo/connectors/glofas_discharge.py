"""Small, verified GloFAS v4 rolling forecasts, not gauged flow or flood depth."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
from urllib.parse import urlencode
import zipfile

from earth_echo.connectors.http import download
from earth_echo.connectors.open_meteo import LICENSE, number, csv_sections, reserve_calls
from earth_echo.connectors.scientific_archive import pack_files
from earth_echo.contracts.products import ScientificProduct, ProductSample, Verification
from earth_echo.storage.products import publish

BASE = 'https://flood-api.open-meteo.com/v1/flood'
META = 'https://flood-api.open-meteo.com/data/glofas_forecast_v4/static/meta.json'
DOC = 'https://open-meteo.com/en/docs/flood-api'
PRIMARY = 'https://confluence.ecmwf.int/spaces/CEMS/pages/242067364/Model+Output'
METHOD = 'glofas-v4-rolling-two-cells-v1'
REGIONS = [('rosario', 'entorno de Rosario', -32.925, -60.675), ('manaus', 'entorno de Manaus', -3.075, -60.025)]
MEMBERS = ['river_discharge'] + [f'river_discharge_member{i:02}' for i in range(1, 51)]
MEAN = 'river_discharge_mean'
SOURCE = 'https://github.com/open-meteo/open-meteo/blob/b485547236a73d528b721f448d5d19a1b6bd15c5/'


def run_metadata(raw, now):
    meta = json.loads(raw)
    keys = ('last_run_initialisation_time', 'last_run_availability_time', 'last_run_modification_time', 'data_end_time')
    if any(type(meta.get(k)) is not int for k in keys) or 'WGS 84' not in meta.get('crs_wkt', '') or meta.get('temporal_resolution_seconds') != 86400:
        raise ValueError('GloFAS daily grid/time metadata changed')
    init, available, modified, end = [datetime.fromtimestamp(meta[k], timezone.utc) for k in keys]
    if init.hour or init.minute or init.second or not init <= available <= modified <= now - timedelta(minutes=10):
        raise ValueError('GloFAS daily metadata not stable yet')
    if end < init + timedelta(days=8):
        raise ValueError('GloFAS forecast domain has incomplete seven-day horizon')
    return init, available, modified, end


def request_url(init):
    return BASE + '?' + urlencode({'latitude': ','.join(str(r[2]) for r in REGIONS),
        'longitude': ','.join(str(r[3]) for r in REGIONS), 'models': 'forecast_v4',
        'daily': 'river_discharge,river_discharge_mean', 'ensemble': 'true',
        'start_date': (init + timedelta(days=1)).date().isoformat(), 'end_date': (init + timedelta(days=7)).date().isoformat(),
        'timezone': 'GMT', 'elevation': 'nan,nan', 'cell_selection': 'nearest'})


def check_cell(lat, lon, requested_lat, requested_lon):
    # Native grid declared by GloFasDomain: (-180.025,-59.975), step0.05.
    # Requests are already native centers to avoid ties, river/terrain snapping.
    native_lat = -59.975 + round((lat + 59.975) / .05) * .05
    native_lon = -180.025 + round((lon + 180.025) / .05) * .05
    if max(abs(lat - native_lat), abs(lon - native_lon), abs(lat - requested_lat), abs(lon - requested_lon)) > 4e-5:
        raise ValueError('GloFAS native 0.05-degree cell disagrees; no arbitrary river reassignment')


def checked_mean(members, provided):
    if any(v is None for v in members) or provided is None:
        return None  # Do not silently average a varying, incomplete ensemble.
    independent = sum(Decimal(str(v)) for v in members) / Decimal(51)
    # API members and mean are rounded to0.01; upstream reduction uses Float32.
    # Bound includes both decimal roundings and standard sequential-sum gamma50.
    eps = Decimal(2) ** -24
    gamma = 50 * eps / (1 - 50 * eps)
    bound = Decimal('.01') + gamma * max(abs(Decimal(str(v))) for v in members)
    if abs(independent - Decimal(str(provided))) > bound:
        raise ValueError('GloFAS independent 51-member mean disagrees beyond rounding/Float32 bound')
    return provided


def products_from_files(files, now):
    before = run_metadata(files['meta-before.json'], now)
    if before != run_metadata(files['meta-after.json'], now):
        raise ValueError('GloFAS run metadata changed during retrieval')
    init, available, modified, _ = before
    dates = [(init + timedelta(days=i)).date().isoformat() for i in range(1, 8)]
    locations = json.loads(files['discharge.json'])
    headers, rows = csv_sections(files['discharge.csv'])
    if not isinstance(locations, list) or len(locations) != 2 or len(headers) != 2 or len(rows) != 14:
        raise ValueError('GloFAS expected two cells and seven days')
    checked = []
    for i, (location, region, header) in enumerate(zip(locations, REGIONS, headers, strict=True)):
        if location.get('location_id', 0) != i or header['location_id'] != str(i):
            raise ValueError('GloFAS location IDs disagree')
        if location.get('timezone') != 'GMT' or location.get('timezone_abbreviation') != 'GMT' or location.get('utc_offset_seconds') != 0 or header['timezone'] != 'GMT' or header['utc_offset_seconds'] != '0':
            raise ValueError('GloFAS time must preserve model GMT dates')
        for name in ('latitude', 'longitude', 'elevation'):
            native = number(location.get(name))
            if (name != 'elevation' and native is None) or native != number(header[name]):
                raise ValueError('GloFAS JSON/CSV coordinates/elevation disagree')
        check_cell(location['latitude'], location['longitude'], region[2], region[3])
        units = {'time': 'iso8601', **{key: 'm³/s' for key in [*MEMBERS, MEAN]}}
        if location.get('daily_units') != units:
            raise ValueError('GloFAS discharge units or 51-member identity changed')
        series = location['daily']
        if set(series) != set(units) or series['time'] != dates:
            raise ValueError('GloFAS daily labels/columns changed')
        decoded = {}
        for key in [*MEMBERS, MEAN]:
            if len(series[key]) != 7:
                raise ValueError('GloFAS incomplete daily series')
            values = [number(v) for v in series[key]]
            for j, row in enumerate(rows[i * 7:(i + 1) * 7]):
                if row['location_id'] != str(i) or row['time'] != dates[j] or number(row[key + ' (m³/s)']) != values[j]:
                    raise ValueError('GloFAS JSON/CSV values/mask/date disagree')
                if values[j] is not None and values[j] < 0:
                    raise ValueError('GloFAS negative discharge')
            decoded[key] = values
        means = [checked_mean([decoded[k][j] for k in MEMBERS], decoded[MEAN][j]) for j in range(7)]
        checked.append((location, region, decoded, means))
    url = request_url(init)
    urls = {'meta-before.json': META, 'meta-after.json': META, 'discharge.json': url, 'discharge.csv': url + '&format=csv'}
    manifest = {'schema_version': '1', 'method': METHOD, 'model': 'GloFAS v4 family, forecast_v4 rolling distribution; operational minor version not exposed',
        'assets': {name: {'url': urls[name], 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)} for name, raw in files.items()},
        'primary_time_definition': PRIMARY, 'native_variable': 'dis24; mean of preceding24h, timestamp labels END of period',
        'audited_upstream_source': [SOURCE + p for p in ('Sources/App/GloFas/GloFasDownloader.swift', 'Sources/App/Controllers/ForecastapiController.swift', 'Sources/App/Controllers/VariableDaily.swift')],
        'version_scope': 'Source audit revision, not asserted deployed binary. forecast_v4 can fall back to intermediate/seasonal data; no per-value run ID.', 'license': LICENSE}
    raw = pack_files(files, manifest, compression=zipfile.ZIP_DEFLATED)
    sha = hashlib.sha256(raw).hexdigest()
    products = []
    for location, (key, name, lat, lon), decoded, means in checked:
        samples = []
        for j, value in enumerate(means):
            start, end = init + timedelta(days=j), init + timedelta(days=j + 1)
            members = [decoded[k][j] for k in MEMBERS]
            samples.append(ProductSample(id=f'{start:%Y-%m-%d}', map_eligible=False, time=start, valid_to=end, value=value,
                quality='Pronóstico hidrológico externo; media publicada cotejada con51 miembros. Sin flags por celda ni validación de aforo local.' if value is not None else 'missing: media o ensemble incompleto; no se rellena con cero ni media de miembros disponibles.',
                attributes={'nombre': f'{start:%Y-%m-%d} · {name}', 'native_valid_time': end.isoformat(), 'time_definition': 'dis24: promedio de las24h anteriores al timestamp nativo de fin. time/valid_to expresan [inicio,fin)UTC.',
                    'native_latitude': str(location['latitude']), 'native_longitude': str(location['longitude']),
                    'returned_elevation_m': None if location.get('elevation') is None else str(location['elevation']), 'requested_latitude': str(lat), 'requested_longitude': str(lon),
                    'members_present': str(sum(v is not None for v in members)), 'ensemble_member_ids': '00 control,01…50 perturbados',
                    'provider_mean_m3_s': None if decoded[MEAN][j] is None else str(decoded[MEAN][j]),
                    'member00_control_m3_s': None if members[0] is None else str(members[0]), 'ensemble_values_m3_s': json.dumps(members, separators=(',', ':')),
                    'forecast_domain_init_reference': init.isoformat(), 'forecast_domain_available_at': available.isoformat(),
                    'model_identity': 'GloFAS v4 family; minor operational version not exposed by this distribution',
                    'quality_mask': 'JSON/CSV null or incomplete51 ensemble -> missing; physical zero retained.'}))
        science = {'metadata': [d.isoformat() for d in before], 'cell': [location['latitude'], location['longitude'], location.get('elevation')], 'members_and_mean': decoded, 'method': METHOD}
        verification = Verification(method='Todos los728 valores de miembros/media, fechas, null, unidades y coordenadas de dos celdas cotejados JSON/CSV. Retícula nativa0,05° verificada. Media de51 miembros recalculada independientemente con Decimal; cota explícita de redondeo decimal y sumaFloat32. Metadatos de dominio antes/después estables≥10min.',
            original_url=url + '&format=csv', checked_at=now, expected='2 celdas×7 días×52 series; media51 consistente, WGS84 y timestamp fin de24h',
            actual=f'728 valores/máscaras coincidentes;7/7 promedios examinados en {name}; {means.count(None)} medias ausentes', passed=True)
        products.append(ScientificProduct(id='d10-glofas-' + key, source_id='D10', title='Caudal previsto · GloFAS v4 · ' + name,
            collection_id='CEMS GloFAS / Open-Meteo forecast_v4 rolling', product_version=f'GloFAS v4 family / domain reference {init.isoformat()} / modification {modified.isoformat()} / minor unspecified',
            variable=MEAN, unit='m³/s', native_unit='m³/s; media de las24h anteriores, media del ensemble51', kind='forecast', representation='time_series',
            initialized_at=None, issued_at=None, observed_at=None, valid_from=init, valid_to=init + timedelta(days=7),
            issue_time_basis=f'Dominio de forecast consultado: inicialización de referencia {init.isoformat()}, disponibilidad {available.isoformat()}. Valores de API rolling sin ID de corrida y con fallback estacional/intermedio posible: no se acredita inicialización única por muestra; initialized_at=null. Emisión no publicada:null. Etiqueta nativa de cada día es fin de las24h promediadas; recuperación y período separados.',
            retrieved_at=now, ingested_at=now, original_url=url, license_url=LICENSE, attribution='Copernicus Emergency Management Service / GloFAS / ECMWF; Weather data by Open-Meteo.com, CC BY4.0. Earth Echo selecciona dos celdas y verifica/cambia etiquetas a intervalos UTC sin alterar caudales.',
            checksum_sha256=sha, scientific_checksum_sha256=hashlib.sha256(json.dumps(science, sort_keys=True).encode()).hexdigest(), byte_size=len(raw), raw_file=f'shared/{sha}.zip',
            coverage=f'Una celda nativa0,05° (~5km) en {name}: {location["latitude"]}°, {location["longitude"]}° WGS84. Siete intervalos24h. No aforo, río principal asignado, cuenca completa o cobertura mundial descargada.',
            cadence_seconds=86400, method_version=METHOD, samples=samples, verification=verification,
            limitation='Caudal modelado, pronóstico externo GloFAS familia v4 por distribución pública Open-Meteo; versión operativa menor no expuesta. No cliente EWDS ni GRIB nativo con corrida aislada. forecast_v4 prioriza forecast diario pero puede completar huecos con intermedio/estacional: se limita la petición a primeros7 días del dominio diario y conserva esa incertidumbre de procedencia; metadata estable no garantiza origen único por valor. 51 miembros00control+01…50, media publicada sin recalibrar; redondeo0,01m³/s y compresión del distribuidor, no precisión de aforo. Todos los miembros retenidos en API/original para inspección, sin líneas concatenadas entre miembros. Celda nearest explícita, sin ajuste de elevación; nombre sólo localiza entorno, no acredita cauce/gauge o representa el río principal de Manaus/Rosario. Caudal no es profundidad/área de inundación, umbral de retorno, aviso ni probabilidad. No hay observaciones de aforos, calibración local, tendencia o habilidad predictiva demostrada. Uso gratuito local no comercial. null/incompletos quedan ausentes, cero válido.'))
    return products, raw


def fetch_glofas(now):
    before, _ = download(META, max_bytes=20_000)
    init, *_ = run_metadata(before, now)
    url = request_url(init)
    files = {'meta-before.json': before}
    for name, address in [('discharge.json', url), ('discharge.csv', url + '&format=csv')]:
        reserve_calls(locations=2, variables=52, hours=168)
        files[name] = download(address, max_bytes=200_000)[0]
    files['meta-after.json'] = download(META, max_bytes=20_000)[0]
    products, raw = products_from_files(files, now)
    results = [publish(p, raw, '.zip') for p in products]
    return 'unchanged' if all(r == 'unchanged' for r in results) else 'stored'
