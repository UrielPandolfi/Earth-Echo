"""Calculate from one retained RAPID asset, without another external download."""
import calendar
import hashlib
import io
import math
from datetime import datetime,timezone
import h5py
import numpy as np
from earth_echo.connectors.rapid_transport import decode_transports
from earth_echo.contracts.products import ScientificProduct,ScientificCalculation,CalculationInput,CalculationResult,ProductSample,Verification
from earth_echo.science.transport_trend import annual_means,slope_per_decade
from earth_echo.storage.products import read_product,products_root,publish

METHOD='rapid-annual-ols-2005-2023-v1'
REFERENCE='https://www.itl.nist.gov/div898/handbook/pmd/section4/pmd431.htm'


def derive_transport_trend(now:datetime):
    source=read_product('d34-amoc-monthly')
    if source is None or source.unit!='Sv' or source.product_version!='v2024-2':
        raise ValueError('Verified RAPID v2024-2 monthly Sv input required')
    raw=(products_root()/source.raw_file).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=source.checksum_sha256:raise ValueError('Retained RAPID checksum differs')
    native,_=decode_transports(raw)
    if [(s.time,s.value) for s in source.samples]!=[(s.time,s.value) for s in native['amoc_depth_1m']]:
        raise ValueError('Stored monthly RAPID input differs from native asset')
    annual=annual_means(source.samples)
    slope=slope_per_decade(annual)
    # Independent implementation: native HDF values, NumPy weighted means and SVD least squares.
    with h5py.File(io.BytesIO(raw),'r') as f:
        values=f['amoc_depth_1m'][:]
        independent=[]
        for year in range(2005,2024):
            indices=[i for i,s in enumerate(native['amoc_depth_1m']) if s.time.year==year]
            valid=len(indices)==12 and np.isfinite(values[indices]).all()
            weights=[calendar.monthrange(year,native['amoc_depth_1m'][i].time.month)[1] for i in indices]
            independent.append((year,float(np.average(values[indices],weights=weights)) if valid else None))
    if any((a is None)!=(b is None) or (a is not None and not math.isclose(a,b,abs_tol=1e-12,rel_tol=0)) for (_,a),(_,b) in zip(annual,independent,strict=True)):
        raise ValueError('Independent annual means disagree')
    present=[(y,v) for y,v in independent if v is not None]
    x=np.array([y-2005 for y,_ in present]);y=np.array([v for _,v in present])
    expected=float(np.linalg.lstsq(np.column_stack((np.ones(len(x)),x)),y,rcond=None)[0][1]*10)
    if not math.isclose(slope,expected,abs_tol=1e-10,rel_tol=0):raise ValueError('Independent annual OLS slope disagrees')
    samples=[ProductSample(id=f'rapid-annual-{year}',time=datetime(year,1,1,tzinfo=timezone.utc),
        valid_to=datetime(year+1,1,1,tzinfo=timezone.utc),value=value,map_eligible=False,
        quality='Media de 12 meses ponderada por días gregorianos, incluidos bisiestos. Año incompleto/mes ausente permanece null; no interpolación.',
        attributes={'periodo':str(year),'soporte_temporal':'Año calendario [time, valid_to); no lectura instantánea',
            'meses_requeridos':'12','unidad':'Sv','seccion':'RAPID 26,5° N; positivo norte'}) for year,value in annual]
    calculation=ScientificCalculation(method_version=METHOD,
        formula='A_y = Σ(días_mes × AMOC_mes) / Σ(días_mes), sólo 12 meses válidos; b_década = 10 × Σ((año−media_año) × (A_y−media_A)) / Σ((año−media_año)²)',
        parameters={'first_year':2005,'last_year':2023,'required_months':12,'minimum_complete_years':15,'years_per_decade':10},
        inputs=[CalculationInput(product_id=source.id,variable=source.variable,unit=source.unit,checksum_sha256=source.checksum_sha256)],
        reference_url=REFERENCE,reference_period='2005-01-01 a 2024-01-01 exclusivo; años calendario 2005–2023. Se excluyen 2004 y 2024 parciales por diseño, antes de calcular.',
        applicability='Pendiente descriptiva OLS de medias anuales, cada año válido con igual peso. No prueba de significación: sin intervalo de confianza, atribución, corrección de autocorrelación o extrapolación; depende del período seleccionado y de la edición observacional procesada.',
        result=CalculationResult(label='Pendiente descriptiva · 2005–2023',value=slope,unit='Sv/década'))
    product=ScientificProduct(id='d34-amoc-annual-trend',source_id='D34',title='AMOC · medias anuales y pendiente descriptiva · 2005–2023',
        collection_id=source.collection_id+' / Earth Echo descriptive annual analysis',product_version=source.product_version,
        variable='annual_mean_amoc_transport',unit='Sv',native_unit='Sv (medias mensuales)',kind='indicator',representation='time_series',
        observed_at=datetime(2005,1,1,tzinfo=timezone.utc),observation_end=datetime(2024,1,1,tzinfo=timezone.utc),
        issued_at=None,issue_time_basis='Análisis histórico; no emisión de pronóstico. Intervalo anual con extremo final exclusivo.',
        retrieved_at=source.retrieved_at,ingested_at=now,original_url=source.original_url,license_url=source.license_url,
        attribution=source.attribution+' · agregación y pendiente descriptiva Earth Echo',checksum_sha256=source.checksum_sha256,
        byte_size=len(raw),raw_file=source.raw_file,coverage=f'{len(present)} de 19 años calendario completos de RAPID 26,5° N, 2005–2023. Análisis regional de sección, no tendencia mundial.',
        cadence_seconds=604800,method_version=METHOD,
        limitation='Agregado y pendiente descriptivos calculados de la serie observacional procesada RAPID v2024-2. Años parciales 2004 y 2024 excluidos por regla fija; media anual ponderada por días del mes. Año con un mes faltante queda null y se excluye del ajuste, sin relleno. Mínimo 15 años completos de los 19. La pendiente describe sólo este período: no demuestra una tendencia secular significativa, causalidad, aceleración, probabilidad o fecha de colapso, ni predice transporte futuro. No se asignan p-valores, intervalos o confianza que ignoren autocorrelación e incertidumbre de entradas. El experimento SST sigue experimental.',
        samples=samples,calculation=calculation,verification=Verification(method='Valores mensuales cotejados contra el NetCDF nativo; todas las medias anuales cotejadas con numpy.average independiente y pendiente con numpy.linalg.lstsq (SVD), frente a sumas centradas de la implementación. Comprueba aritmética, no significación científica.',
            original_url=source.original_url,checked_at=now,expected=f'{expected:.15g} Sv/década (SVD); {len(present)} años',actual=f'{slope:.15g} Sv/década; medias anuales coinciden a 1e-12 Sv',passed=True))
    return publish(product,raw,'.nc')
