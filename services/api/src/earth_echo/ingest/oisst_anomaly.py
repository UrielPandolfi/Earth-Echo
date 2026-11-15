"""Expose the daily NOAA anomaly already present in the retained SST original."""
import hashlib
import io
import math
from datetime import datetime,timezone

import h5py
import netCDF4
import numpy as np

from earth_echo.contracts.products import ScientificGrid,ScientificProduct,Verification
from earth_echo.science.field_aggregation import oisst_degree_means
from earth_echo.storage.products import read_product,products_root,publish

PRODUCT_ID='d13-oisst-anomaly-global'
METHOD='oisst-native-anomaly-area-display-v1'
PAGE='https://www.ncei.noaa.gov/products/optimum-interpolation-sst'


def anomaly_from_source(source,raw,now):
    if source.id!='d13-oisst-global' or source.source_id!='D13' or source.variable!='sst' or source.unit!='°C':raise ValueError('Qualified OISST SST source required')
    if not source.product_version.startswith('v2.1') or 'v02r01' not in source.original_url:raise ValueError('Qualified OISSTv2.1 edition required')
    if hashlib.sha256(raw).hexdigest()!=source.checksum_sha256:raise ValueError('OISST retained checksum differs')
    with netCDF4.Dataset('oisst-anomaly.nc',memory=raw) as ds:
        variable=ds['anom']
        if variable.shape!=(1,1,720,1440) or variable.dtype!=np.dtype('int16') or variable.units!='Celsius' or variable.long_name!='Daily sea surface temperature anomalies':raise ValueError('Unexpected native OISST anomaly definition')
        if '1971-2000 OI.v2 SST' not in ds.references:raise ValueError('OISST anomaly climatology changed; scientific review required')
        if (int(variable.valid_min),int(variable.valid_max),int(variable._FillValue))!=(-1200,1200,-999) or float(variable.add_offset)!=0 or not math.isclose(float(variable.scale_factor),.01,abs_tol=1e-9,rel_tol=0):raise ValueError('OISST native scale/mask/range changed')
        lat=np.asarray(ds['lat'][:]);lon=np.asarray(ds['lon'][:])
        if not np.array_equal(lat,np.arange(720,dtype=np.float32)*.25-89.875) or not np.array_equal(lon,np.arange(1440,dtype=np.float32)*.25+.125):raise ValueError('Native OISST axes differ')
        native=variable[0,0,:,:]
        moment=netCDF4.num2date(ds['time'][0],ds['time'].units,only_use_cftime_datetimes=False)
        observed=datetime(moment.year,moment.month,moment.day,moment.hour,moment.minute,moment.second,tzinfo=timezone.utc)
        if observed!=source.observed_at or observed.strftime('%Y%m%d') not in source.original_url:raise ValueError('Native OISST anomaly/source date differs')
    # Independent HDF reader, explicit short-domain masking BEFORE scaling.
    # _FillValue=-999 lies INSIDE[-1200,1200], so valid_range alone is wrong.
    with h5py.File(io.BytesIO(raw),'r') as ds:
        encoded=ds['anom'][0,0,:,:]
        valid=(encoded!=-999)&(encoded>=-1200)&(encoded<=1200)
        decoded=encoded.astype(np.float32)*np.float32(ds['anom'].attrs['scale_factor'][0])
    if not np.array_equal(np.ma.getmaskarray(native),~valid) or not np.array_equal(np.asarray(native)[valid],decoded[valid]):raise ValueError('Independent native anomaly scaling/mask disagrees')
    means,count=oisst_degree_means(native,lat)
    # Verify EVERY display cell by a separate loop/compensated summation.
    for row in range(180):
        for column in range(360):
            values=[];weights=[]
            for r in range(row*4,row*4+4):
                weight=math.cos(math.radians(float(lat[r])))
                for c in range(column*4,column*4+4):
                    if valid[r,c]:values.append(float(decoded[r,c]));weights.append(weight)
            if len(values)!=int(count[row,column]):raise ValueError('Independent native support count differs')
            if len(values)>=8:
                independent=math.fsum(v*w for v,w in zip(values,weights,strict=True))/math.fsum(weights)
                if not math.isclose(float(means[row,column]),independent,abs_tol=5e-12,rel_tol=0):raise ValueError('Independent area mean disagrees')
    columns=list(range(180,360))+list(range(180))
    values=[float(means[r,c]) if count[r,c]>=8 else None for r in range(179,-1,-1) for c in columns]
    support=[int(count[r,c]) for r in range(179,-1,-1) for c in columns]
    present=[v for v in values if v is not None]
    if not present:raise ValueError('No qualified daily OISST anomaly cells')
    grid=ScientificGrid(width=360,height=180,west=-180,east=180,south=-90,north=90,longitudes=[-179.5+i for i in range(360)],latitudes=[89.5-i for i in range(180)],
        values=values,minimum=min(present),maximum=max(present),missing_cells=values.count(None),resolution='Nativa0,25°; vista de medias1°',color_center=0,
        sampling='Cada celda de vista es media cos(lat) de4×4centros nativos válidos, mínimo8/16. Sólo fracción oceánica válida; costa no se extrapola a tierra. Centros1° exactos, filas norte→sur y columnas−180…180; no interpolación adicional, pines o detección de eventos.',
        quality_mask='Fill−999 y rango válido se aplican al short antes de escala0,01; máscaras netCDF/HDF coinciden. Soporte de vista<8/16→null. Hielo puede usar SST proxy del análisis NOAA; error/ice nativos permanecen en mismo original. Los conteos de soporte no son nuevos flags del proveedor.',
        quality_values=support,quality_legend={str(n):f'{n}/16celdas nativas válidas; '+('vista ausente' if n<8 else 'media oceánica disponible') for n in range(17)})
    product=ScientificProduct(id=PRODUCT_ID,source_id='D13',title='Anomalía diaria SST · NOAA OISST · base1971–2000',collection_id=source.collection_id,product_version=source.product_version,
        variable='anom',unit='°C',native_unit='Celsius, short×scale_factor nativo',kind='indicator',representation='field',observed_at=observed,
        retrieved_at=source.retrieved_at,ingested_at=now,original_url=source.original_url,license_url=PAGE,attribution=source.attribution+' · anomalía publicada NOAA; media de visualización Earth Echo',
        issue_time_basis='Análisis diario, coordenada CF representativa12UTC; no hora de emisión/inicialización o medición instantánea. No se fabrica time_bounds.',
        checksum_sha256=source.checksum_sha256,byte_size=len(raw),raw_file=source.raw_file,coverage='Campo oceánico mundial de anomalía publicada respecto a climatología OI.v21971–2000, interpolada por NOAA de mensual1° a diaria0,25°. Tierra/fondo ausentes; vista1°mínimo8/16válidos.',
        cadence_seconds=86400,method_version=METHOD,
        limitation='Anomalía absoluta publicada en°C, no score estandarizado o probabilidad. Base1971–2000 distinta de referencia regional2014–2021 y de normal1991–2020. No se calcula aquí otra climatología ni se restan campos incompatibles. Análisis OISST interpolado/mezclado; preliminar si así se identifica el archivo. Un día/celda cálida no es evento MHW de cinco días, estrés coralino confirmado, ola de calor del aire, causalidad o pronóstico. La reducción1°es sólo vista, no preserva extremos subcelda; los valores científicos0,25°/anom/err/ice/SST se conservan compartidos sin nueva descarga.',
        grid=grid,verification=Verification(method='Los1.036.800shorts/máscaras escalados se cotejaron netCDF4/HDF5;64.800medias y conteos de soporte se comprobaron con bucle/Math.fsum independientes. Fecha/CF/ejes/base1971–2000 y SHA cotejados con original SST retenido.',
            original_url=PAGE,checked_at=now,expected='Original diario OISSTv2.1; máscara/escala nativas y medias cos(lat), mínimo8/16',actual=f'{int(valid.sum())}celdas nativas válidas; {len(present)}medias visibles, {values.count(None)}ausentes; sin diferencia>5e-12°C',passed=True))
    return product


def derive_oisst_anomaly(now):
    source=read_product('d13-oisst-global')
    if source is None:raise ValueError('Retained daily OISST source unavailable; previous anomaly retained')
    raw=(products_root()/source.raw_file).read_bytes()
    product=anomaly_from_source(source,raw,now)
    return publish(product,raw,'.nc')
