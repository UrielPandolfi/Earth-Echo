"""Actual ERDDAP scientific subsets; globally sampled, never point events."""
import csv
import hashlib
import io
import json
import math
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from earth_echo.connectors.http import download
from earth_echo.connectors.netcdf_classic import ClassicNetCdf
from earth_echo.contracts.products import ScientificGrid, ScientificProduct, Verification

CRW = 'https://coastwatch.noaa.gov/erddap'
PRODUCTS = {
    'd15-sst-global': ('D15', CRW, 'noaacrwsstDaily', 'analysed_sst', 'degree_C', '°C', 'SST · CoralTemp mundial', 'observation', 20),
    'd15-hotspot-global': ('D15', CRW, 'noaacrwhotspotDaily', 'hotspot', 'degree_C', '°C', 'Coral HotSpot mundial', 'indicator', 20),
    'd15-dhw-global': ('D15', CRW, 'noaacrwdhwDaily', 'degree_heating_week', 'degree_Celsius_weeks', '°C·semana', 'Degree Heating Weeks mundial', 'indicator', 20),
}

def decode_grid(raw: bytes, variable: str, expected_unit: str, *, mask_name: str | None = None) -> tuple[ScientificGrid, datetime]:
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / 'field.nc'
        path.write_bytes(raw)
        dataset = ClassicNetCdf(path)
    attr = dataset.variables[variable]['attributes']
    if attr.get('units') != expected_unit:
        raise ValueError(f'Unexpected units: {attr.get("units")}')
    if dataset.variables['time']['attributes'].get('units') != 'seconds since 1970-01-01T00:00:00Z':
        raise ValueError('Unsupported time origin')
    times = dataset.values('time')
    if len(times) != 1:
        raise ValueError('Expected one time slice')
    lats = dataset.values('latitude')
    lons = dataset.values('longitude')
    raw_values = dataset.values(variable)
    mask = dataset.values(mask_name) if mask_name else None
    if len(raw_values) != len(lats) * len(lons) or (mask is not None and len(mask) != len(raw_values)):
        raise ValueError('Invalid grid dimensions')
    values = []
    for i, v in enumerate(raw_values):
        missing = not math.isfinite(v) or v == attr.get('_FillValue') or (mask is not None and mask[i] != 0)
        missing |= ('valid_min' in attr and v < attr['valid_min']) or ('valid_max' in attr and v > attr['valid_max'])
        values.append(None if missing else v * attr.get('scale_factor', 1) + attr.get('add_offset', 0))
    rows = sorted(range(len(lats)), key=lambda i: lats[i], reverse=True)
    columns = sorted(range(len(lons)), key=lambda i: lons[i])
    values = [values[r * len(lons) + c] for r in rows for c in columns]
    lats = [lats[r] for r in rows]
    lons = [lons[c] for c in columns]
    dy, dx = abs(lats[1] - lats[0]), lons[1] - lons[0]
    present = [v for v in values if v is not None]
    grid = ScientificGrid(width=len(lons), height=len(lats), longitudes=lons, latitudes=lats,
        west=max(-180, lons[0] - dx / 2), east=min(180, lons[-1] + dx / 2),
        south=max(-90, lats[-1] - dy / 2), north=min(90, lats[0] + dy / 2),
        values=values, minimum=min(present) if present else None, maximum=max(present) if present else None,
        missing_cells=values.count(None), resolution=f'{dx:.4g}° × {dy:.4g}° de visualización',
        sampling='Submuestreo regular por stride de centros nativos; vecino más cercano en pantalla. No es promedio de área. El NetCDF y la URL conservan los centros y valores científicos muestreados; el proveedor ofrece resolución nativa.',
        quality_mask='mask=0 (valid-water); tierra, hielo, faltante y relleno transparentes' if mask else '_FillValue y rango válido declarados por el producto; no se interpolan huecos')
    return grid, datetime.fromtimestamp(times[0], timezone.utc)

def fetch_ocean(key: str, now: datetime) -> tuple[ScientificProduct, bytes, str]:
    source, base, dataset_id, var, native, unit, title, kind, stride = PRODUCTS[key]
    info_url = f'{base}/info/{dataset_id}/index.json'
    info_raw, _ = download(info_url, max_bytes=100_000)
    rows = json.loads(info_raw)['table']['rows']
    attrs = {(r[1], r[2]): r[4] for r in rows if r[0] == 'attribute'}
    latest = float(str(attrs[('time', 'actual_range')]).split(',')[-1])
    observed = datetime.fromtimestamp(latest, timezone.utc)
    if observed > now:
        raise ValueError('Provider time is in the future')
    stamp = observed.strftime('%Y-%m-%dT%H:%M:%SZ')
    selector = f'[({stamp})][0:{stride}:last][0:{stride}:last]'
    has_mask = any(r[0] == 'variable' and r[1] == 'mask' for r in rows)
    variables = var + selector + (',mask' + selector if has_mask else '')
    url = f'{base}/griddap/{dataset_id}.nc?{variables}'
    raw, _ = download(url, max_bytes=1_500_000)
    grid, decoded_time = decode_grid(raw, var, native, mask_name='mask' if has_mask else None)
    if decoded_time != observed:
        raise ValueError('Metadata and field disagree on time')
    # Independent serialization/request, including mask. A missing cell is checked as missing.
    index = next((i for i, v in enumerate(grid.values) if v is not None), 0)
    lat, lon = grid.latitudes[index // grid.width], grid.longitudes[index % grid.width]
    point_selector = f'[({stamp})][({lat})][({lon})]'
    csv_url = f'{base}/griddap/{dataset_id}.csv?{var}{point_selector}' + (f',mask{point_selector}' if has_mask else '')
    check_raw, _ = download(csv_url, max_bytes=10_000)
    check_rows = list(csv.reader(io.StringIO(check_raw.decode())))
    reference = float(check_rows[2][3])
    value = grid.values[index]
    if value is None or not math.isclose(value, reference, abs_tol=1e-6):
        raise ValueError('Independent CSV does not match NetCDF')
    sha = hashlib.sha256(raw).hexdigest()
    with tempfile.TemporaryDirectory() as temp:
        path=Path(temp)/'subset.nc'; path.write_bytes(raw); ds=ClassicNetCdf(path)
        # Every native number, including mask classes and axes, not just displayed values.
        scientific={'dimensions':ds.dimensions,'variables':{name:{'attributes':v['attributes'],'values':ds.values(name)} for name,v in ds.variables.items()}}
        science_sha=hashlib.sha256(json.dumps(scientific,sort_keys=True,default=str).encode()).hexdigest()
    limitation = ('SST analizada: no es temperatura del aire ni diagnóstico de ola de calor marina.' if var == 'analysed_sst' else
        'HotSpot: diferencia positiva de SST respecto de Maximum Monthly Mean; DHW: acumulación del estrés ≥1 °C durante 12 semanas. Indicadores importados de NOAA, sin confirmar blanqueamiento biológico ni pronóstico.')
    return ScientificProduct(id=key, source_id=source, title=title, collection_id=dataset_id, product_version='3.1',
        variable=var, unit=unit, native_unit=native, kind=kind, representation='field', observed_at=observed,
        retrieved_at=now, ingested_at=now, original_url=url,
        license_url='https://coralreefwatch.noaa.gov/satellite/', attribution='NOAA/NESDIS/STAR Coral Reef Watch',
        checksum_sha256=sha,scientific_checksum_sha256=science_sha, byte_size=len(raw), raw_file=f'{key}/assets/{sha}.nc',
        coverage='Océanos mundiales; extensión exacta en grid; tierra y hielo excluidos.', cadence_seconds=86400,
        method_version='erddap-global-stride-v1', limitation=limitation, grid=grid,
        verification=Verification(method='Celda NetCDF contrastada con descarga CSV independiente del mismo producto', original_url=csv_url,
            checked_at=now, expected=str(reference), actual=str(value), passed=True)), raw, '.nc'
