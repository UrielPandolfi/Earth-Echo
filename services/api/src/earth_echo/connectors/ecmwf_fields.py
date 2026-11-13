"""Bounded GRIB messages from the official public IFS index, not a full run."""
import hashlib
import json
import math
from datetime import datetime, timedelta, timezone
import eccodes as ec
from earth_echo.connectors.http import download
from earth_echo.contracts.products import ScientificGrid, ScientificProduct, Verification
from earth_echo.science.units import kelvin_to_celsius, metres_to_mm
from earth_echo.storage.products import publish

PARAMETERS = {'2t':('Temperatura del aire a 2 m','K','°C',kelvin_to_celsius),
    '2d':('Punto de rocío a 2 m','K','°C',kelvin_to_celsius),
    'tp':('Precipitación acumulada 0–24 h','m','mm',metres_to_mm),
    '10u':('Viento zonal a 10 m','m s**-1','m/s',lambda v:v),
    '10v':('Viento meridional a 10 m','m s**-1','m/s',lambda v:v)}

def decode_message(raw: bytes, parameter: str, index: dict) -> tuple[ScientificGrid,dict]:
    handle = ec.codes_new_from_message(raw)
    try:
        if ec.codes_get(handle,'shortName') != parameter or ec.codes_get(handle,'gridType') != 'regular_ll':
            raise ValueError('Unexpected parameter or grid')
        ni,nj = ec.codes_get_long(handle,'Ni'),ec.codes_get_long(handle,'Nj')
        title,native,unit,convert = PARAMETERS[parameter]
        if ec.codes_get(handle,'units') != native or (ni,nj)!=(1440,721):
            raise ValueError('Unexpected units or resolution')
        initial = datetime.strptime(str(ec.codes_get_long(handle,'dataDate'))+f'{ec.codes_get_long(handle,"dataTime"):04d}', '%Y%m%d%H%M').replace(tzinfo=timezone.utc)
        valid = datetime.strptime(str(ec.codes_get_long(handle,'validityDate'))+f'{ec.codes_get_long(handle,"validityTime"):04d}', '%Y%m%d%H%M').replace(tzinfo=timezone.utc)
        if initial.strftime('%Y%m%d') != index['date'] or int(index['step']) != 24 or valid != initial+timedelta(hours=24):
            raise ValueError('GRIB time disagrees with independent index')
        if parameter=='tp' and (ec.codes_get(handle,'stepType')!='accum' or ec.codes_get_long(handle,'startStep')!=0):
            raise ValueError('Unknown accumulation window')
        values = ec.codes_get_values(handle)
        latitudes = ec.codes_get_array(handle,'latitudes')
        longitudes = ec.codes_get_array(handle,'longitudes')
        # 1° cell centres are exact nodes of the 0.25° mesh, with no duplicated dateline or poles.
        row_indices = list(range(2,nj-2,4))
        columns = sorted(range(2,ni,4),key=lambda c:((float(longitudes[c])+180)%360)-180)
        lats = [float(latitudes[r*ni]) for r in row_indices]
        lons = [((float(longitudes[c])+180)%360)-180 for c in columns]
        missing = ec.codes_get_double(handle,'missingValue')
        selected = [None if not math.isfinite(float(values[r*ni+c])) or values[r*ni+c]==missing else convert(float(values[r*ni+c])) for r in row_indices for c in columns]
        if lats[0] != 89.5 or lats[-1] != -89.5 or lons[0] != -179.5 or lons[-1] !=179.5:
            raise ValueError('Unsupported scanning order')
        probe = ec.codes_grib_find_nearest(handle,lats[90],lons[180])[0]
        expected = convert(float(probe['value']))
        actual = selected[90*len(columns)+180]
        if not math.isclose(actual,expected,abs_tol=1e-5): raise ValueError('GRIB nearest-point verification failed')
        present = [v for v in selected if v is not None]
        grid = ScientificGrid(width=len(columns),height=len(row_indices),west=-180,east=180,south=-90,north=90,longitudes=lons,latitudes=lats,
            values=selected,minimum=min(present) if present else None,maximum=max(present) if present else None,missing_cells=selected.count(None),
            resolution='IFS 0,25° nativa; visualización 1°',sampling='Una de cada cuatro filas/columnas en centros 0,5°; sin promedio de área. GRIB original conserva el millón de nodos nativos.',quality_mask='Bitmap de GRIB y missingValue; ausencia no reemplazada por cero. Pronóstico de modelo, no medición directa.')
        return grid, {'initial':initial,'valid':valid,'expected':str(expected),'actual':str(actual),
            'version':f'GRIB{ec.codes_get_long(handle,"edition")}; tables={ec.codes_get_long(handle,"tablesVersion")}; process={ec.codes_get_long(handle,"generatingProcessIdentifier")}'}
    finally:
        ec.codes_release(handle)

def fetch_ecmwf(now: datetime) -> str:
    # Only one deterministic 24 h step, five variables (~3 MB), latest mature 00/12 UTC cycle.
    candidate = now-timedelta(hours=8)
    initial = candidate.replace(hour=12 if candidate.hour>=12 else 0,minute=0,second=0,microsecond=0)
    base = f'https://data.ecmwf.int/forecasts/{initial:%Y%m%d}/{initial:%H}z/ifs/0p25/oper/{initial:%Y%m%d%H}0000-24h-oper-fc'
    index_raw,_ = download(base+'.index',max_bytes=500_000)
    entries = [json.loads(line) for line in index_raw.splitlines()]
    results = []
    for param,(title,native,unit,convert) in PARAMETERS.items():
        entry = next(r for r in entries if r.get('param')==param and r.get('levtype')=='sfc' and r.get('type')=='fc')
        offset,length = int(entry['_offset']),int(entry['_length'])
        if not 0<length<2_000_000: raise ValueError('GRIB message exceeds budget')
        raw,headers = download(base+'.grib2',max_bytes=length,headers={'Range':f'bytes={offset}-{offset+length-1}'})
        if len(raw)!=length or not raw.startswith(b'GRIB') or not raw.endswith(b'7777'):
            raise ValueError('Range server did not return the requested complete GRIB message')
        grid,meta = decode_message(raw,param,entry)
        sha = hashlib.sha256(raw).hexdigest()
        key = f'd07-ifs-{param}-24h'
        p = ScientificProduct(id=key,source_id='D07',title=title+' · IFS +24 h',collection_id='IFS oper fc 0p25',product_version=meta['version'],
            variable=param,unit=unit,native_unit=native,kind='forecast',representation='field',initialized_at=meta['initial'],issued_at=None,
            issue_time_basis='Inicialización en GRIB; hora de emisión no informada en el mensaje. La recuperación no se usa como emisión.',
            valid_from=meta['initial'] if param=='tp' else meta['valid'],valid_to=meta['valid'] if param=='tp' else None,
            retrieved_at=now,ingested_at=now,original_url=base+'.grib2',license_url='https://www.ecmwf.int/en/forecasts/datasets/open-data',
            attribution='ECMWF IFS Open Data · CC BY 4.0',checksum_sha256=sha,byte_size=len(raw),raw_file=f'{key}/assets/{sha}.grib2',
            coverage='Mundial; malla de modelo atmosférico. No resuelve impactos locales.',cadence_seconds=43200,method_version='ifs-index-range-grid-v1',
            limitation='Pronóstico determinista externo, un plazo +24 h. Sin probabilidades ni detector de ola de calor, tormenta o inundación. '+('Acumulado desde la inicialización, convertido m→mm; no es tasa ni profundidad de inundación.' if param=='tp' else ''),grid=grid,
            verification=Verification(method=f'Metadatos GRIB cotejados contra índice oficial; valor vía ecCodes nearest independiente del orden de arrays; Range bytes={offset}-{offset+length-1}',original_url=base+'.index',
                checked_at=now,expected=meta['expected'],actual=meta['actual'],passed=True))
        results.append(publish(p,raw,'.grib2'))
    return 'unchanged' if all(r=='unchanged' for r in results) else 'stored'
