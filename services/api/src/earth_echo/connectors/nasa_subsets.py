"""ORNL DAAC scientific subsets of original MODIS products, including QA and native grid."""
import hashlib
import json
import math
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from urllib.parse import urlencode
from pyproj import CRS, Transformer
from earth_echo.connectors.http import download
from earth_echo.contracts.products import ScientificGrid, ScientificProduct, Verification
from earth_echo.science.units import kelvin_to_celsius
from earth_echo.storage.products import publish

BASE = 'https://modis.ornl.gov/rst/api/v1'
REGIONS = {'pampa':(-35., -62., 'Pampa central; entorno de -35°, -62°'), 'amazonia':(-3., -60., 'Amazonía central; entorno de -3°, -60°')}
SINUSOIDAL = CRS.from_proj4('+proj=sinu +R=6371007.181 +nadgrids=@null +wktext +units=m +no_defs')

def good_vi(quality: int, reliability: int) -> bool:
    return reliability == 0 and quality >= 0 and quality & 3 == 0 and (quality >> 2) & 15 <= 2 and (quality >> 6) & 3 != 3 and not quality & ((1 << 8)|(1 << 10)|(1 << 14)|(1 << 15)) and (quality >> 11) & 7 == 1

def reproject_subset(body: dict, values: list[float | None], quality_note: str) -> ScientificGrid:
    nx, ny = int(body['ncols']), int(body['nrows'])
    cell, x0, y0 = float(body['cellsize']), float(body['xllcorner']), float(body['yllcorner'])
    if len(values) != nx * ny or nx < 2 or ny < 2:
        raise ValueError('Invalid native grid shape')
    inverse = Transformer.from_crs(SINUSOIDAL, 'EPSG:4326', always_xy=True)
    forward = Transformer.from_crs('EPSG:4326', SINUSOIDAL, always_xy=True)
    west, south, east, north = inverse.transform_bounds(x0,y0,x0+nx*cell,y0+ny*cell,densify_pts=21)
    lons = [west+(c+.5)*(east-west)/nx for c in range(nx)]
    lats = [north-(r+.5)*(north-south)/ny for r in range(ny)]
    geographic = []
    for lat in lats:
        for lon in lons:
            x,y = forward.transform(lon,lat)
            c, r = math.floor((x-x0)/cell), ny-1-math.floor((y-y0)/cell)
            geographic.append(values[r*nx+c] if 0<=r<ny and 0<=c<nx else None)
    present = [v for v in geographic if v is not None]
    return ScientificGrid(width=nx,height=ny,west=west,east=east,south=south,north=north,longitudes=lons,latitudes=lats,
        values=geographic,minimum=min(present) if present else None,maximum=max(present) if present else None,
        missing_cells=geographic.count(None),resolution=f'Nativa sinusoidal: {cell:g} m; vista WGS84 {nx}×{ny}',
        sampling='Reproyección sinusoidal MODIS (esfera R=6371007.181 m) a WGS84 mediante vecino más cercano. Se conservan la malla nativa y los enteros originales en JSON.',quality_mask=quality_note)

def fetch_modis(product: str, region: str, now: datetime) -> list[str]:
    lat, lon, coverage = REGIONS[region]
    dates_raw,_ = download(f'{BASE}/{product}/dates?'+urlencode({'latitude':lat,'longitude':lon}),max_bytes=100_000)
    dates = json.loads(dates_raw)['dates']
    days = 16 if product == 'MOD13Q1' else 8
    # Only complete composites: the date is the START of the composite, not acquisition instant.
    available = [d for d in dates if datetime.fromisoformat(d['calendar_date']).replace(tzinfo=timezone.utc)+timedelta(days=days) <= now]
    chosen = available[-1]
    start = datetime.fromisoformat(chosen['calendar_date']).replace(tzinfo=timezone.utc)
    bands_raw,_ = download(f'{BASE}/{product}/bands', max_bytes=100_000)
    bands = {b['band']:b for b in json.loads(bands_raw)['bands']}
    params = {'latitude':lat,'longitude':lon,'startDate':chosen['modis_date'],'endDate':chosen['modis_date'],'kmAboveBelow':20,'kmLeftRight':20}
    url = f'{BASE}/{product}/subset?'+urlencode(params)
    subset_raw,_ = download(url,max_bytes=3_000_000)
    body = json.loads(subset_raw)
    records = {r['band']:r for r in body['subset']}
    raw = json.dumps({'band_metadata':json.loads(bands_raw),'native_subset':body,'date_discovery':chosen},ensure_ascii=False,sort_keys=True).encode()
    sha = hashlib.sha256(raw).hexdigest()
    names = ['250m_16_days_NDVI','250m_16_days_EVI'] if product == 'MOD13Q1' else ['LST_Day_1km','LST_Night_1km']
    # A separate single-band request validates the delivered raw values and georeferencing.
    check_url = url+'&band='+names[0]
    check_raw,_ = download(check_url,max_bytes=500_000)
    check = json.loads(check_raw)
    checked_record = next(r for r in check['subset'] if r['band']==names[0])
    if checked_record['data'] != records[names[0]]['data'] or any(check[k] != body[k] for k in ['xllcorner','yllcorner','cellsize','nrows','ncols']):
        raise ValueError('Independent single-band download does not match')
    results = []
    for band in names:
        metadata, record = bands[band], records[band]
        original = record['data']
        low, high = [float(v) for v in metadata['valid_range'].split(' to ')]
        fill = float(metadata['fill_value'])
        scale, offset = float(metadata.get('scale_factor',1)), float(metadata.get('add_offset',0))
        if product == 'MOD13Q1':
            quality = records['250m_16_days_VI_Quality']['data']
            reliability = records['250m_16_days_pixel_reliability']['data']
            valid = [good_vi(int(q),int(r)) for q,r in zip(quality,reliability,strict=True)]
            quality_note = 'pixel_reliability=0, MODLAND=0, utilidad≤2, sin aerosol alto, nube adyacente/mixta, nieve ni sombra; solo tierra.'
            unit = '1'
        else:
            if metadata.get('units') != 'Kelvin' or scale != .02:
                raise ValueError('Unexpected LST metadata')
            quality = records['QC_Day' if 'Day' in band else 'QC_Night']['data']
            valid = [int(q)==0 for q in quality]
            quality_note = 'QC=0: LST de buena calidad, error LST≤1 K y emisividad≤0,01; relleno/nube ausentes. Compuesto de cielo despejado.'
            unit = '°C'
        decoded = [None if not ok or v==fill or not low<=v<=high else float(v)*scale+offset for v,ok in zip(original,valid,strict=True)]
        if product == 'MOD11A2': decoded = [kelvin_to_celsius(v) for v in decoded]
        grid = reproject_subset(body,decoded,quality_note)
        short = band.split('_')[-1].lower() if product=='MOD13Q1' else ('lst-day' if 'Day' in band else 'lst-night')
        key = f'd04-{short}-{region}' if product=='MOD13Q1' else f'd05-{short}-{region}'
        # Verify scale numerically against decimal arithmetic, independent of float decode.
        idx = next((i for i,v in enumerate(decoded) if v is not None),None)
        actual = decoded[idx] if idx is not None else None
        expected = (Decimal(str(original[idx]))*Decimal(metadata.get('scale_factor','1'))+Decimal(metadata.get('add_offset','0'))-(Decimal('273.15') if unit=='°C' else 0)) if idx is not None else None
        if expected is not None and not math.isclose(float(expected),actual,abs_tol=1e-8): raise ValueError('Scale verification failed')
        p = ScientificProduct(id=key,source_id='D04' if product=='MOD13Q1' else 'D05',title=f'{short.upper()} · {region}',
            collection_id=product,product_version=f'ORNL proc_date={record["proc_date"]}; tile={record["tile"]}',variable=band,
            unit=unit,native_unit=metadata.get('units','1'),kind='observation',representation='field',
            observed_at=start,observation_end=min(start+timedelta(days=days),datetime(start.year+1,1,1,tzinfo=timezone.utc)),
            retrieved_at=now,ingested_at=now,original_url=url,license_url='https://daac.ornl.gov/MODIS/',attribution='NASA MODIS / ORNL DAAC',
            checksum_sha256=sha,byte_size=len(raw),raw_file=f'shared/{sha}.json',coverage=f'{coverage}; subconjunto de ~40×40 km, no cobertura mundial.',
            cadence_seconds=86400,method_version='ornl-modis-qa-nearest-v1',
            limitation='Índice de verdor; no confirma sequía ni rendimiento agrícola.' if product=='MOD13Q1' else 'Temperatura de superficie de cielo despejado, diurna/nocturna; no es temperatura del aire ni ola de calor.',grid=grid,
            verification=Verification(method=f'Banda y georreferenciación cotejadas con petición independiente; escala decimal; raw[{idx}]={original[idx] if idx is not None else "missing"}',
                original_url=check_url,checked_at=now,expected=str(expected),actual=str(actual),passed=True))
        results.append(publish(p,raw,'.json'))
    return results
