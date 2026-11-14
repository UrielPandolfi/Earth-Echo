"""ECMWF SEAS5 monthly ensemble means, explicitly selected through Open-Meteo.

The monthly precipitation API value is an ensemble-mean calendar-month TOTAL,
not a rate, individual ensemble member, climate anomaly or event probability.
"""
import csv
from datetime import datetime, timedelta, timezone
from functools import lru_cache
import hashlib
import io
import json
from urllib.parse import urlencode
import zipfile

import numpy as np

from earth_echo.connectors.http import download
from earth_echo.connectors.open_meteo import number, reserve_calls
from earth_echo.connectors.scientific_archive import pack_files
from earth_echo.contracts.products import ScientificProduct, ProductSample, Verification
from earth_echo.storage.products import publish

BASE = 'https://seasonal-api.open-meteo.com/v1/seasonal'
META = 'https://seasonal-api.open-meteo.com/data/ecmwf_seas5_monthly/static/meta.json'
DOC = 'https://open-meteo.com/en/docs/seasonal-forecast-api'
LICENSE = 'https://open-meteo.com/en/licence'
METHOD = 'seas5-monthly-native-cell-v1'
# An audited upstream source revision, NOT an assertion about the deployed binary.
AUDITED_SOURCE = 'https://github.com/open-meteo/open-meteo/blob/b485547236a73d528b721f448d5d19a1b6bd15c5/Sources/App/EcmwfSeas/'
REGIONS = [('pampa', 'Pampa', -35.5, -61.5), ('amazonia', 'Amazonía', -3.5, -60.5)]
VARIABLES = [('temperature_2m_mean', 'temperatura', 'Temperatura media mensual a2m', '°C'),
             ('precipitation_mean', 'precipitacion', 'Precipitación total mensual', 'mm')]


def month_after(start, delta):
    n = start.year * 12 + start.month - 1 + delta
    return datetime(n // 12, n % 12 + 1, 1, tzinfo=timezone.utc)


def run_metadata(raw, now):
    meta = json.loads(raw)
    if 'O320 (ECMWF)' not in meta.get('crs_wkt', '') or 'World Geodetic System 1984' not in meta['crs_wkt']:
        raise ValueError('SEAS5 monthly native grid/CRS changed')
    keys = ('last_run_initialisation_time', 'last_run_availability_time', 'last_run_modification_time', 'data_end_time')
    if any(type(meta.get(k)) is not int for k in keys):
        raise ValueError('SEAS5 run timestamps missing')
    init, available, modified, end = [datetime.fromtimestamp(meta[k], timezone.utc) for k in keys]
    if init != month_after(init, 0) or not init <= available <= modified <= now - timedelta(minutes=10):
        raise ValueError('SEAS5 monthly run not yet stable or inconsistent timestamps')
    if end < month_after(init, 7):
        raise ValueError('SEAS5 incomplete seven-calendar-month horizon')
    return init, available, modified, end


def request_url(init):
    return BASE + '?' + urlencode({
        'latitude': ','.join(str(r[2]) for r in REGIONS),
        'longitude': ','.join(str(r[3]) for r in REGIONS),
        'models': 'ecmwf_seas5',  # Never the default EC46+SEAS5 seamless mix.
        'monthly': ','.join(v[0] for v in VARIABLES),
        'start_date': init.date().isoformat(),
        'end_date': (month_after(init, 7) - timedelta(days=1)).date().isoformat(),
        'timezone': 'GMT', 'elevation': 'nan,nan', 'cell_selection': 'nearest',
    })


@lru_cache(maxsize=1)
def gaussian_latitudes():
    # Independent Gaussian quadrature roots, not API coordinates or a local DTM.
    nodes, _ = np.polynomial.legendre.leggauss(640)
    return np.degrees(np.arcsin(nodes))


def check_native_cell(lat, lon, requested_lat, requested_lon):
    lats = gaussian_latitudes()
    ring = int(np.argmin(abs(lats - requested_lat)))
    count = 20 + 4 * min(ring, 639 - ring)
    expected_lon = ((round((requested_lon % 360) / 360 * count) % count) * 360 / count + 180) % 360 - 180
    # Provider Float32 coordinates can be calculated at 0..360 before wrapping.
    # One Float32 ULP near360 plus decimal formatting is <4e-5 degrees.
    if abs(lat - lats[ring]) > 4e-5 or abs(lon - expected_lon) > 4e-5:
        raise ValueError('SEAS5 coordinates do not match independently calculated O320 nearest cell')


def products_from_files(files, now):
    before = run_metadata(files['meta-before.json'], now)
    after = run_metadata(files['meta-after.json'], now)
    if before != after:
        raise ValueError('SEAS5 run changed during JSON/CSV retrieval; previous retained')
    init, available, modified, _ = before
    months = [month_after(init, i) for i in range(7)]
    dates = [d.date().isoformat() for d in months]
    locations = json.loads(files['monthly.json'])
    if not isinstance(locations, list) or len(locations) != len(REGIONS):
        raise ValueError('SEAS5 expected exactly two native cells')
    blocks = files['monthly.csv'].decode('utf-8').strip().split('\n\n')
    if len(blocks) != 2:
        raise ValueError('SEAS5 independent CSV structure changed')
    headers = list(csv.DictReader(io.StringIO(blocks[0])))
    rows = list(csv.DictReader(io.StringIO(blocks[1])))
    if len(headers) != 2 or len(rows) != 14:
        raise ValueError('SEAS5 independent CSV location/month counts disagree')
    checked = []
    for i, (location, region, header) in enumerate(zip(locations, REGIONS, headers, strict=True)):
        if location.get('utc_offset_seconds') != 0 or location.get('timezone') != 'GMT' or location.get('timezone_abbreviation') != 'GMT':
            raise ValueError('SEAS5 timestamps must be explicitly GMT/UTC')
        if location.get('location_id', 0) != i or int(header['location_id']) != i:
            raise ValueError('SEAS5 location IDs disagree')
        for name in ('latitude', 'longitude', 'elevation'):
            if number(location.get(name)) is None or number(location[name]) != number(header[name]):
                raise ValueError('SEAS5 JSON/CSV native coordinates/elevation disagree')
        if header['timezone'] != 'GMT' or header['timezone_abbreviation'] != 'GMT' or header['utc_offset_seconds'] != '0':
            raise ValueError('SEAS5 independent CSV timezone changed')
        check_native_cell(location['latitude'], location['longitude'], region[2], region[3])
        if location.get('monthly_units') != {'time': 'iso8601', 'temperature_2m_mean': '°C', 'precipitation_mean': 'mm'}:
            raise ValueError('SEAS5 monthly units changed; no implicit conversion')
        values = location['monthly']
        if set(values) != {'time', *(v[0] for v in VARIABLES)} or values['time'] != dates:
            raise ValueError('SEAS5 monthly dates/variables changed')
        native_rows = rows[i * 7:(i + 1) * 7]
        decoded = {}
        for variable, _, _, unit in VARIABLES:
            if len(values[variable]) != 7:
                raise ValueError('Incomplete SEAS5 monthly series')
            series = [number(v) for v in values[variable]]
            for j, row in enumerate(native_rows):
                if row['location_id'] != str(i) or row['time'] != dates[j] or number(row[variable + ' (' + unit + ')']) != series[j]:
                    raise ValueError('SEAS5 independent JSON/CSV values/mask/months disagree')
                if variable == 'precipitation_mean' and series[j] is not None and series[j] < 0:
                    raise ValueError('SEAS5 negative monthly total precipitation')
            decoded[variable] = series
        checked.append((location, region, decoded))
    url = request_url(init)
    urls = {'meta-before.json': META, 'meta-after.json': META, 'monthly.json': url, 'monthly.csv': url + '&format=csv'}
    manifest = {'schema_version': '1', 'model': 'ECMWF SEAS5, monthly ensemble mean, O320',
        'assets': {name: {'url': urls[name], 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()} for name, raw in files.items()},
        'audited_provider_source': [AUDITED_SOURCE + name for name in ('EcmwfSeasDomain.swift', 'EcmwfSeasVariable.swift', 'EcmwfSeasDownloader.swift')],
        'source_revision_scope': 'Audited transformation documentation, not asserted deployed server build/version.',
        'provider_transform': 'temperature K-273.15; tprate m/s * actual calendar-month seconds *1000 -> mm/month. Already performed upstream; Earth Echo does not repeat it.',
        'license': LICENSE, 'method': METHOD}
    raw = pack_files(files, manifest, compression=zipfile.ZIP_DEFLATED)
    sha = hashlib.sha256(raw).hexdigest()
    products = []
    for location, (region_key, region_name, lat, lon), decoded in checked:
        for variable, suffix, title, unit in VARIABLES:
            precip = variable == 'precipitation_mean'
            values = decoded[variable]
            quality = 'Media de ensemble del modelo SEAS5 sin corrección de sesgo. Valor numérico publicado; sin flags de calidad por celda. No observación ni probabilidad.'
            samples = [ProductSample(id=f'{d:%Y-%m}', map_eligible=False, time=d, valid_to=month_after(d, 1), value=value,
                quality=quality if value is not None else 'missing: proveedor publica null; no se interpola ni rellena con cero.',
                attributes={'nombre': f'{d:%Y-%m} · {region_name}', 'ensemble_statistic': 'provider ensemble mean; individual member not applicable',
                    'native_latitude': str(location['latitude']), 'native_longitude': str(location['longitude']),
                    'native_grid_elevation_m': str(location['elevation']), 'requested_latitude': str(lat), 'requested_longitude': str(lon),
                    'model': 'ECMWF SEAS5', 'monthly_product': 'ope_s2_ifs-seas_od_msmm_em',
                    'statistic': 'Total del mes calendario, media del ensemble' if precip else 'Temperatura a2m media del mes calendario y del ensemble',
                    'calendar_days': str((month_after(d, 1) - d).days), 'run_available_at': available.isoformat(),
                    'scale_offset': 'Ya convertido por proveedor: m/s × segundos del mes ×1000; sin nueva escala' if precip else 'Ya convertido por proveedor: K−273,15; sin nuevo offset',
                    'quality_mask': 'null→missing; cero publicado válido. No hay flags adicionales proporcionados.'}) for d, value in zip(months, values, strict=True)]
            scientific = {'run': [d.isoformat() for d in before], 'cell': [location['latitude'], location['longitude'], location['elevation']], 'variable': variable, 'values': values, 'method': METHOD}
            verification = Verification(method='Todos los valores, null, meses, unidades, coordenadas y altura cotejados entre respuestas JSON y CSV independientes. Celda más próxima O320 calculada con raíces de Legendre de orden640 y longitudes de cada anillo. Metadatos mensuales antes/después idénticos, antigüedad de publicación≥10min.',
                original_url=url + '&format=csv', checked_at=now, expected='7 meses calendario; JSON=CSV; coordenadas de celda nativa O320; corrida estable',
                actual=f'7/7 meses {init:%Y-%m}…{months[-1]:%Y-%m}; {values.count(None)} ausentes; celda {location["latitude"]},{location["longitude"]}; corrida {init.isoformat()}', passed=True)
            products.append(ScientificProduct(id=f'd09-seas5-{region_key}-{suffix}', source_id='D09', title=f'{title} · SEAS5 · {region_name}',
                collection_id='ECMWF SEAS5 / ope_s2_ifs-seas_od_msmm_em / Open-Meteo ecmwf_seas5_monthly',
                product_version=f'SEAS5 / init {init.isoformat()} / provider modification {modified.isoformat()}', variable=variable, unit=unit,
                native_unit='mm por mes calendario, media de ensemble' if precip else '°C, media mensual de ensemble a2m', kind='forecast', representation='time_series',
                initialized_at=init, issued_at=None, observed_at=None, valid_from=init, valid_to=month_after(init, 7),
                issue_time_basis=f'Inicialización mensual {init.isoformat()}, disponibilidad del distribuidor {available.isoformat()}. Recuperación en su campo separado. Emisión ECMWF no proporcionada: null. Se coteja meta ecmwf_seas5_monthly antes/después; API de valores no expone ID de corrida, por lo que esa asociación depende de estabilidad temporal del distribuidor. generationtime_ms sólo mide latencia de API.',
                retrieved_at=now, ingested_at=now, original_url=url, license_url=LICENSE,
                attribution='ECMWF SEAS5; Weather data by Open-Meteo.com, CC BY4.0. Earth Echo selecciona dos celdas/variables, conserva valores y decodifica períodos/ausencias. Sin respaldo o validación de los proveedores.',
                checksum_sha256=sha, scientific_checksum_sha256=hashlib.sha256(json.dumps(scientific, sort_keys=True).encode()).hexdigest(), byte_size=len(raw), raw_file=f'shared/{sha}.zip',
                coverage=f'Una celda nativa O320 (~36km) en {region_name}: {location["latitude"]}°, {location["longitude"]}° WGS84, solicitada {lat}°, {lon}°. Siete meses calendario; no cobertura regional completa ni malla mundial descargada.',
                cadence_seconds=86400, method_version=METHOD, samples=samples, verification=verification,
                limitation='Pronóstico externo ECMWF SEAS5, media mensual del ensemble, sin miembros individuales/dispersión ni calibración contra reforecasts. Distribución pública Open-Meteo distinta de cliente/dataset CDS C3S; uso gratuito local no comercial. models=ecmwf_seas5 evita mezcla EC46. Celda nativa más próxima, elevation=nan desactiva ajuste altitudinal; sin interpolación temporal/espacial por Earth Echo. '+
                    ('precipitation_mean representa total de precipitación del mes en mm, promediado sobre el ensemble: proveedor integra tprate con segundos reales de cada mes; no tasa diaria. ' if precip else 'Temperatura del aire a2m media mensual; no SST, extremo diario o temperatura de superficie terrestre. ')+
                    'Meses civiles [inicio,fin) UTC, incluyendo el mes inicial que puede haber comenzado; no tiempo observado. Metadatos usan intervalo representativo31d, no duración fija de todos los meses. No hay climatología/anomalía, probabilidades de sequía/inundación/calor/helada ni habilidad predictiva local acreditada. null permanece ausente y cero válido. En fallo se conserva la corrida válida con su edad.'))
    return products, raw


def fetch_seasonal_monthly(now):
    before, _ = download(META, max_bytes=20_000)
    init, *_ = run_metadata(before, now)
    url = request_url(init)
    files = {'meta-before.json': before}
    for name, address in [('monthly.json', url), ('monthly.csv', url + '&format=csv')]:
        reserve_calls(locations=2, variables=2, hours=(month_after(init, 7) - init).total_seconds() / 3600)
        files[name] = download(address, max_bytes=200_000)[0]
    files['meta-after.json'] = download(META, max_bytes=20_000)[0]
    products, raw = products_from_files(files, now)
    results = [publish(p, raw, '.zip') for p in products]
    return 'unchanged' if all(r == 'unchanged' for r in results) else 'stored'
