"""Actual Sentinel-3A OC4Me L3 chlorophyll via the public NOAA distribution."""
import csv
import hashlib
import io
import json
import math
import re
from datetime import datetime,timezone
from earth_echo.connectors.http import download
from earth_echo.connectors.netcdf_classic import ClassicNetCdf
from earth_echo.connectors.ocean_fields import decode_grid
from earth_echo.contracts.products import ScientificProduct,Verification
from earth_echo.storage.products import publish

BASE='https://coastwatch.noaa.gov/erddap'
DATASET='noaacwS3AOLCIchlaDaily'


def decode_sentinel(raw):
    ds=ClassicNetCdf(raw)
    if ds.attributes.get('platform')!='Sentinel-3A' or ds.attributes.get('institution')!='Copernicus Program':
        raise ValueError('Expected actual Copernicus Sentinel-3A data, not a NASA substitute')
    if ds.values('altitude')!=[0.] or ds.variables['altitude']['attributes'].get('units')!='m':
        raise ValueError('Expected surface product at altitude zero')
    attrs=ds.variables['chlor_a']['attributes']
    if attrs.get('cw_processing_algorithm')!='OC4Me Algorithm' or attrs.get('cw_product_status')!='Experimental':
        raise ValueError('OLCI algorithm/status changed; scientific review required')
    grid,stamp=decode_grid(raw,'chlor_a','mg m^-3')
    # No clipping to the visualization color bar (native values can exceed 64.7).
    grid.color_scale='log10'
    if any(v is not None and v<=0 for v in grid.values):
        raise ValueError('Nonpositive native concentration: retain original and review log display, do not silently mask zero')
    grid.quality_mask='NaN/_FillValue transparentes; huecos de la grilla L3 conservados. No hay QA por píxel descargado; graphics es overlay gráfico, no una máscara de calidad. Producto Experimental.'
    grid.sampling='Stride 24 de centros del producto L3 nativo 0.0375° (~4 km), campo visual 0.9°. Sin promedio adicional, relleno de nubes ni creación de señales. La agregación geométrica OC4Me pertenece al proveedor. Valores mg/m³ originales, color log10 solamente para visualizar.'
    # Preserve complete scientific bytes/attributes; exclude only the two ERDDAP
    # request-history lines, retaining original Sentinel-SAFE/cwutils processing.
    globals_=dict(ds.attributes)
    globals_['history']='\n'.join(line for line in globals_.get('history','').splitlines()
        if not re.match(r'^\d{4}-\d{2}-\d{2}T[^ ]+ (?:\(local files\)|https://coastwatch\.noaa\.gov/erddap/griddap/)',line))
    science={'global_attributes':globals_,'dimensions':ds.dimensions,'variables':{k:{'attributes':v['attributes'],'values':ds.values(k)} for k,v in ds.variables.items()}}
    checksum=hashlib.sha256(json.dumps(science,sort_keys=True,default=str).encode()).hexdigest()
    return grid,stamp,ds,checksum


def fetch_sentinel_chlorophyll(now:datetime):
    info,_=download(f'{BASE}/info/{DATASET}/index.json',max_bytes=200_000)
    rows=json.loads(info)['table']['rows']
    attrs={(r[1],r[2]):r[4] for r in rows if r[0]=='attribute'}
    latest=datetime.fromtimestamp(float(str(attrs[('time','actual_range')]).split(',')[-1]),timezone.utc)
    if latest>now:raise ValueError('Sentinel baseline time is in the future')
    stamp=latest.strftime('%Y-%m-%dT%H:%M:%SZ')
    selector=f'[({stamp})][0][0:24:last][0:24:last]'
    url=f'{BASE}/griddap/{DATASET}.nc?chlor_a{selector}'
    raw,_=download(url,max_bytes=1_500_000)
    grid,decoded,ds,science_sha=decode_sentinel(raw)
    if decoded!=latest:raise ValueError('Sentinel metadata and field dates disagree')
    index=max((i for i,v in enumerate(grid.values) if v is not None),key=lambda i:grid.values[i],default=None)
    if index is None:raise ValueError('Selected satellite field contains no finite scientific sample; previous retained')
    lat,lon=grid.latitudes[index//grid.width],grid.longitudes[index%grid.width]
    check_url=f'{BASE}/griddap/{DATASET}.csv?chlor_a[({stamp})][0][({lat})][({lon})]'
    csv_raw,_=download(check_url,max_bytes=10_000)
    check=list(csv.reader(io.StringIO(csv_raw.decode())))
    reference=float(check[2][check[0].index('chlor_a')])
    if not math.isclose(reference,grid.values[index],rel_tol=1e-6,abs_tol=1e-6):raise ValueError('Independent CSV disagrees with native Sentinel NetCDF')
    sha=hashlib.sha256(raw).hexdigest()
    return publish(ScientificProduct(id='d25-s3a-chlorophyll',source_id='D25',title='Clorofila · Sentinel-3A OC4Me · experimental',collection_id=DATASET,
        product_version=ds.attributes.get('history','').splitlines()[0]+'; OC4Me Experimental; baseline ESA no informado',
        variable='chlor_a',unit='mg/m³',native_unit='mg m^-3',kind='observation',representation='field',observed_at=latest,
        issue_time_basis='time es Time Baseline del agregado diario L3, no hora de pasada individual. date_created=2021 identifica metadatos de colección, no emisión del campo; emisión UTC no proporcionada.',
        retrieved_at=now,ingested_at=now,original_url=url,license_url=ds.attributes['infoUrl'],
        attribution='Contains modified Copernicus Sentinel data. Copernicus Program / Sentinel-3A OLCI; procesamiento y distribución NOAA/NESDIS/STAR/CoastWatch.',
        checksum_sha256=sha,scientific_checksum_sha256=science_sha,byte_size=len(raw),raw_file=f'd25-s3a-chlorophyll/assets/{sha}.nc',
        coverage='Campo L3 de ámbito oceánico mundial; extensión exacta en grid y solo celdas válidas observadas/agregadas. Nubes/tierra/huecos quedan ausentes; no cobertura completa efectiva en cada día.',
        cadence_seconds=86400,method_version='sentinel3a-oc4me-noaa-stride24-v1',grid=grid,
        limitation='Producto Experimental OC4Me de Sentinel-3A, agregado geométrico L3 redistribuido/modificado por NOAA; no producto NASA OceanColor D17 ni escena Sentinel-2/InSAR. Es concentración de clorofila, no especie de alga, toxicidad, hipoxia ni enfermedad humana. La fecha es baseline del producto diario; se conserva aun con demora del proveedor. Resolución nativa publicada 0.0375° y vista cada 24 centros (0.9°), sin interpolar faltantes. Valores por encima de colorBarMaximum=64.7 se conservan: colorBar no es rango válido ni control de calidad. Escala log10 modifica solo color, no datos. No hay flags QA individuales en este subconjunto; graphics no se usó como calidad. No habilita detección de HAB ni pronóstico biológico. Otras rutas Sentinel-1/2/5P y descarga/procesamiento CDSE siguen pendientes de credenciales/permisos.',
        verification=Verification(method='Máximo del NetCDF científico cotejado con CSV independiente por fecha/altitud/latitud/longitud; plataforma, unidades, algoritmo/estado experimental y ausencia NaN comprobados. Fuente Copernicus distinta de NASA, con atribución obligatoria conservada.',
            original_url=check_url,checked_at=now,expected=str(reference)+' mg/m³',actual=str(grid.values[index])+' mg/m³',passed=True)),raw,'.nc')
