"""RAPID regional processed transport series; no global AMOC collapse clock."""
import hashlib
import html
import io
import math
import re
import statistics
import struct
from datetime import datetime,timezone
import h5py
from netCDF4 import num2date
from earth_echo.connectors.http import download
from earth_echo.contracts.products import ScientificProduct,ProductSample,Verification
from earth_echo.storage.products import publish

URL='https://rapid.ac.uk/sites/default/files/rapid_data/data/RAPID_transports_v2024-2.nc'
PAGE='https://rapid.ac.uk/data'
DOC='https://rapid.ac.uk/sites/default/files/rapid_data/data/moc_transports_supporting_information_2026.pdf'
DOI='10.5285/5c39bf4e-5140-5546-e063-7086abc027bc'
VARIABLES={
    'amoc_depth_1m':('d34-amoc-monthly','AMOC · transporte mensual en 26,5° N','Sv'),
    'heat_trans_1m':('d34-heat-monthly','RAPID · transporte mensual de calor en 26,5° N','PW'),
    'frwa_trans_1m':('d34-freshwater-monthly','RAPID · transporte mensual de agua dulce en 26,5° N','Sv'),
}


def native_text(value):
    return value.decode() if isinstance(value,bytes) else str(value)


def decode_transports(raw):
    result={}
    with h5py.File(io.BytesIO(raw),'r') as f:
        attrs={k:native_text(v) for k,v in f.attrs.items()}
        if attrs.get('Dataset_version')!='v2024-2' or attrs.get('DOI')!=DOI:
            raise ValueError('RAPID edition/DOI changed; scientific review required')
        time=f['time_1m']
        units=native_text(time.attrs['units']);calendar=native_text(time.attrs['calendar'])
        if units!='days since 1950-01-01' or calendar!='gregorian':raise ValueError('Unexpected RAPID time reference/calendar')
        times=[]
        for item in num2date(time[:],units=units,calendar=calendar):
            times.append(datetime(item.year,item.month,item.day,item.hour,item.minute,item.second,tzinfo=timezone.utc))
        if len(times)<2 or len(times)>1000 or any(a>=b for a,b in zip(times,times[1:])):
            raise ValueError('Invalid monthly RAPID timeline')
        if times[0].date().isoformat()!=attrs.get('time_coverage_start') or times[-1].date().isoformat()!=attrs.get('time_coverage_end'):
            raise ValueError('RAPID native time coordinate and declared coverage disagree')
        for variable,(key,title,unit) in VARIABLES.items():
            data=f[variable]
            if data.shape!=(len(times),) or native_text(data.attrs.get('Units',''))!=unit:
                raise ValueError(f'Unexpected RAPID units/dimensions: {variable}')
            if data.attrs.get('scale_factor',1)!=1 or data.attrs.get('add_offset',0)!=0:
                raise ValueError('Unexpected RAPID packing; no implicit conversion')
            if data.chunks is not None or data.dtype.str not in ('<f8','=f8') or data.id.get_offset() is None:
                raise ValueError('Native binary cross-check requires published contiguous little-endian doubles')
            decoded=data[:].tolist()
            independent=struct.unpack_from('<'+'d'*len(times),raw,data.id.get_offset())
            if any(a!=b for a,b in zip(decoded,independent) if not(math.isnan(a) and math.isnan(b))):
                raise ValueError('Independent RAPID native binary values disagree')
            values=[float(v) if math.isfinite(v) else None for v in decoded]
            result[variable]=[ProductSample(id=variable+'-'+stamp.strftime('%Y%m'),time=stamp,value=value,
                quality='Serie observacional procesada del proveedor; media mensual, no lectura instantánea. Relleno NaN permanece ausente. No hay incertidumbre mensual actualizada incluida en este producto.',
                attributes={'periodo_mensual':stamp.strftime('%Y-%m'),'seccion':'RAPID-MOCHA-WBTS, Atlántico 26,5° N; transporte integrado de sección',
                    'signo':'Positivo hacia el norte; negativo hacia el sur', 'Units_nativo':unit,'variable_nativa':variable,
                    'Long_name_nativo':native_text(data.attrs.get('Long_name','')),'File_creation_date':attrs.get('File_creation_date'),
                    'soporte_temporal':'Punto CF representativo del mes (día 15); no observación instantánea',
                    'calidad_entradas':'Incluye procesamiento, reemplazos/climatologías e insumos de reanálisis del proveedor; ver documento de edición. Sin diagnóstico de colapso.'}) for stamp,value in zip(times,values)]
    return result,attrs


def verify_published_mean(samples,page):
    text=re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',page.decode('utf-8',errors='replace'))))
    if 'RAPID_transports_v2024-2.nc' not in text:raise ValueError('RAPID documentation now describes a different release')
    match=re.search(r'MOC\s*:\s*([\d.]+)\s*±\s*([\d.]+)\s*Sv',text)
    if not match:raise ValueError('Published RAPID MOC mean/SD not found')
    present=[s.value for s in samples if s.value is not None]
    actual=(statistics.mean(present),statistics.stdev(present))
    expected=(float(match[1]),float(match[2]))
    if tuple(round(v,1) for v in actual)!=expected:raise ValueError('Published RAPID mean/sample SD disagrees with native time series')
    return expected,actual


def fetch_rapid(now:datetime):
    # A directly published download URL is available without the optional email form.
    raw,_=download(URL,max_bytes=8_000_000)
    page,_=download(PAGE,max_bytes=500_000)
    series,attrs=decode_transports(raw)
    expected,actual=verify_published_mean(series['amoc_depth_1m'],page)
    sha=hashlib.sha256(raw).hexdigest();results=[]
    for variable,(key,title,unit) in VARIABLES.items():
        samples=series[variable]
        results.append(publish(ScientificProduct(id=key,source_id='D34',title=title,collection_id='RAPID-MOCHA-WBTS monthly integrated transports at 26.5N',
            product_version=attrs['Dataset_version'],variable=variable,unit=unit,native_unit=unit,kind='historical',representation='time_series',
            observed_at=samples[0].time,observation_end=samples[-1].time,
            issue_time_basis=f"File_creation_date={attrs.get('File_creation_date')} es fecha sin hora/zona; emisión UTC queda null. time_1m es coordenada CF gregorian en days since 1950-01-01, punto mensual representativo.",
            retrieved_at=now,ingested_at=now,original_url=URL,license_url=DOC,attribution='Moat et al. (2026), RAPID-MOCHA-WBTS / NERC / NSF / NOAA; doi:'+DOI,
            checksum_sha256=sha,byte_size=len(raw),raw_file=f'shared/{sha}.nc',coverage=f'{len(samples)} medias mensuales abril 2004–noviembre 2024 de la sección RAPID 26,5° N. No cobertura oceánica mundial ni dato actual.',
            cadence_seconds=604800,method_version='rapid-v2024-2-monthly-v1',
            limitation='Historia observacional procesada, con componentes instrumentales, reanálisis e interpolaciones/climatologías del proveedor; no sensor global continuo ni pronóstico. Se conservan unidades nativas: Sv=10⁶ m³/s y PW=10¹⁵ W, positivo norte. Los tiempos representan medias mensuales; faltantes NaN permanecen null, sin rellenar. Datos terminan en noviembre 2024, edición v2024-2 creada 14/10/2026 sin hora/zona conocida. El archivo de incertidumbre separado llega sólo a 2015 y no se extrapola a 2024; no se inventa confianza. No determina tendencia secular significativa ni fecha/probabilidad de colapso AMOC. Una prueba adicional con máximos de perfiles verticales discretos no reprodujo exactamente la serie AMOC (diferencia ≤0,001617 Sv); se conserva la serie publicada, sin sustituirla ni declarar esa reconstrucción validada. Revisión semanal de esta edición fija; otra edición necesita revisión científica.',
            samples=samples,verification=Verification(method='Todos los valores mensuales decodificados también con struct desde offsets/dobles nativos independientes de h5py; Units (mayúscula), calendario CF, cobertura y DOI verificados. Media/SD AMOC cotejadas con estadísticas oficiales de la misma edición, sin validar predicción.',
                original_url=PAGE,checked_at=now,expected=f'MOC {expected[0]} ± {expected[1]} Sv (media/SD publicada, 1 decimal)',actual=f'MOC {actual[0]:.12f} ± {actual[1]:.12f} Sv; coinciden a 1 decimal; valores binarios '+variable+' coincidentes',passed=True)),raw,'.nc'))
    return 'unchanged' if all(r=='unchanged' for r in results) else 'stored'
