"""Persist an independently checked analysis of retained CoralTemp history."""
import calendar
import hashlib
import json
import math
from datetime import datetime,timezone

import numpy as np
from netCDF4 import Dataset,num2date

from earth_echo.contracts.geometry import GeographicExtent
from earth_echo.contracts.products import ScientificProduct,ScientificCalculation,CalculationInput,ProductSample,Verification
from earth_echo.ingest.d15_history import series_path,month_file
from earth_echo.connectors.crw_sst import GRIDDAP,SOURCE_PAGE
from earth_echo.science.anomalies import METHOD,REFERENCE_URL,THRESHOLD,MAD_FACTOR,seasonal_departures
from earth_echo.science.series import MonthValue
from earth_echo.storage.products import publish

PRODUCT_ID='d15-sst-seasonal-departures'


def checked_history(payload):
    if payload.get('data_mode')!='real' or payload.get('source_id')!='D15' or payload.get('collection_id')!='noaacrwsstDaily' or payload.get('product_version')!='3.1' or payload.get('region_id')!='caribe-occidental':
        raise ValueError('Verified CoralTemp v3.1 Caribbean history required')
    rows=[MonthValue(int(p['year']),int(p['month']),p['value'],int(p['present_days']),int(p['expected_days'])) for p in payload['months']]
    assets={(a['year'],a['month']):a for a in payload['assets']}
    if len(assets)!=len(payload['assets']):raise ValueError('Duplicate history asset')
    native_axes=None
    support=None
    for row in rows:
        asset=assets.get((row.year,row.month))
        if asset is None:
            if row.value is not None or row.present_days:raise ValueError('Monthly value has no retained original')
            continue
        path=month_file(row.year,row.month)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=asset['sha256'] or path.stat().st_size!=asset['bytes']:
            raise ValueError('CoralTemp native history checksum differs')
        # Independent library/masked arrays, not the custom classic NetCDF
        # reader and accumulation used by the original history ingestion.
        with Dataset(path) as ds:
            native=ds['analysed_sst']
            if native.units!='degree_C' or native.standard_name!='sea_surface_temperature':raise ValueError('Native SST unit/variable differs')
            lat=np.asarray(ds['latitude'][:],dtype=np.float64)
            lon=np.asarray(ds['longitude'][:],dtype=np.float64)
            region=payload['region']
            if native_axes is None:
                # ERDDAP selected nearest endpoint centres: 21x21 at0.05deg.
                # The requested1deg bbox is not the actual cell-edge support.
                if len(lat)!=21 or len(lon)!=21 or not np.allclose(np.diff(lat),0.05,atol=8e-6,rtol=0) or not np.allclose(np.diff(lon),0.05,atol=8e-6,rtol=0):raise ValueError('Native SST grid differs')
                if not np.allclose([lat[0],lat[-1],lon[0],lon[-1]],[region['south']+0.025,region['north']+0.025,region['west']+0.025,region['east']+0.025],atol=4e-6,rtol=0):raise ValueError('Native SST coverage differs')
                native_axes=(lat,lon)
                support=GeographicExtent(west=float(lon.min()-0.025),east=float(lon.max()+0.025),south=float(lat.min()-0.025),north=float(lat.max()+0.025),crosses_antimeridian=False)
            elif not (np.array_equal(lat,native_axes[0]) and np.array_equal(lon,native_axes[1])):raise ValueError('SST grid changed between months')
            dates=num2date(ds['time'][:],ds['time'].units)
            if any(d.year!=row.year or d.month!=row.month for d in dates) or len({(d.year,d.month,d.day) for d in dates})!=len(dates):raise ValueError('Native SST dates differ or repeat')
            values=np.ma.masked_invalid(native[:])
            weights=np.broadcast_to(np.cos(np.deg2rad(lat))[:,None],values.shape[1:])
            daily=np.ma.average(values,weights=np.broadcast_to(weights,values.shape),axis=(1,2))
            present=int(daily.count())
            expected_days=calendar.monthrange(row.year,row.month)[1]
            independent=round(float(daily.mean()),4) if present/expected_days>=0.8 else None
        if row.expected_days!=expected_days or row.present_days!=present or (row.value is None)!=(independent is None) or (independent is not None and not math.isclose(row.value,independent,abs_tol=1e-9,rel_tol=0)):
            raise ValueError('Independent native SST monthly aggregation disagrees')
    if support is None:raise ValueError('No native SST support available')
    return rows,support


def build_sst_anomalies(now:datetime):
    raw=series_path().read_bytes();payload=json.loads(raw)
    months,support=checked_history(payload)
    rows=seasonal_departures(months)
    # Independent reference/score with NumPy. Does not validate a disaster model.
    for row in rows:
        baseline=np.array([m.value for m in months if 2014<=m.year<=2021 and m.month==row.month and m.value is not None and m.present_days/m.expected_days>=0.8])
        if len(baseline)>=8:
            center=float(np.median(baseline));mad=float(np.median(np.abs(baseline-center)))
            if row.median_c!=center or row.mad_c!=mad:raise ValueError('Independent seasonal median/MAD differs')
            if row.modified_z is not None:
                expected=float(0.6745*(row.sst_c-center)/mad)
                if not math.isclose(row.modified_z,expected,abs_tol=1e-12,rel_tol=0):raise ValueError('Independent modified score differs')
    def text(value):return None if value is None else str(value)
    samples=[]
    for row in rows:
        end_year=row.year+(row.month==12);end_month=1 if row.month==12 else row.month+1
        samples.append(ProductSample(id=f'{row.year}-{row.month:02}',time=datetime(row.year,row.month,1,tzinfo=timezone.utc),valid_to=datetime(end_year,end_month,1,tzinfo=timezone.utc),
            value=row.departure_c,category=row.classification,map_eligible=False,
            quality='Desvío mensual respecto a mediana del mismo mes2014–2021. Sólo2022–2025 evaluado fuera de referencia. MAD cero/referencia incompleta/valor ausente: score null; no daño o probabilidad.',
            attributes={'sst_c':text(row.sst_c),'reference_median_c':text(row.median_c),'reference_mad_c':text(row.mad_c),'reference_years':str(row.reference_n),'modified_z':text(row.modified_z),'assessment':row.classification}))
    checksum=hashlib.sha256(raw).hexdigest()
    count=sum(row.modified_z is not None for row in rows)
    flagged=sum(row.classification in {'warm_departure','cold_departure'} for row in rows)
    calculation=ScientificCalculation(method_version=METHOD,formula='d = SST_mes − mediana(SST_mismo_mes,2014…2021); MAD = mediana(|SST_ref−mediana_ref|); M=0,6745×d/MAD; candidato si |M|>3,5, sólo año>2021',
        parameters={'reference_first_year':2014,'reference_last_year':2021,'minimum_reference_years':8,'modified_z_threshold':THRESHOLD,'mad_factor':MAD_FACTOR,'minimum_day_coverage':0.8},
        inputs=[CalculationInput(product_id='d15-monthly-history',variable='regional_monthly_sst',unit='°C',checksum_sha256=checksum)],reference_url=REFERENCE_URL,
        reference_period='2014-01 a2022-01 exclusivo; ocho valores por mes calendario. No normal climática de30años.',
        applicability='Etiquetado descriptivo de posibles desvíos, no test de significación ni probabilidad calibrada. Umbral fijado por regla publicada, no ajustado al resultado. Recorte Caribe solicitado1°, soporte real21×21celdas0,05°≈1,05° por selección de extremos nearest de ERDDAP. No detecta olas de calor marinas diarias o blanqueamiento.')
    product=ScientificProduct(id=PRODUCT_ID,source_id='D15',title='SST Caribe · anomalías mensuales respecto a referencia · 2022–2025',collection_id='noaacrwsstDaily / retained regional monthly history',product_version='3.1',
        variable='monthly_sst_departure_from_seasonal_reference_median',unit='°C',native_unit='degree_C',kind='indicator',representation='time_series',
        observed_at=datetime(2014,1,1,tzinfo=timezone.utc),observation_end=datetime(2026,1,1,tzinfo=timezone.utc),
        retrieved_at=datetime.fromtimestamp(series_path().stat().st_mtime,timezone.utc),ingested_at=now,
        issue_time_basis='Análisis histórico calculado; retrieved_at es fecha del agregado local, no nueva descarga NASA/NOAA o emisión de pronóstico.',
        original_url=GRIDDAP.removesuffix('.nc')+'.html',license_url='https://coralreefwatch.noaa.gov/satellite/docs/disclaimer.php',attribution='NOAA Coral Reef Watch CoralTemp v3.1 · agregación y etiquetado descriptivo Earth Echo',
        checksum_sha256=checksum,byte_size=len(raw),raw_file=f'shared/{checksum}.json',extent=support,
        coverage=f'Historia mensual2014–2025 del recorte Caribe,21×21celdas0,05°, bordes≈16,50–17,55N/67,50–66,45O; {count} meses evaluables2022–2025; {flagged} candidatos estadísticos. Sin alarmas actuales.',cadence_seconds=86400,method_version=METHOD,
        limitation='Referencia corta de ocho años, estacionalidad por mes; no normal climática. Se preservan candidatos como observaciones, no se eliminan. Regla exploratoria3,5×MAD normalizada, sin tasas de falsa alarma/daño, múltiples comparaciones o probabilidad. Un resultado dentro del umbral no demuestra ausencia de estrés. No incorpora datos posteriores a2025; no es alerta actual, MHW de cinco días, causalidad, pronóstico ni validación del experimento SST.',
        samples=samples,calculation=calculation,verification=Verification(method='144 agregados cotejados contra originales NetCDF con biblioteca independiente, máscaras, unidades, fechas, ponderación y hashes; medianas/MAD/score cotejados también con NumPy.',
            original_url=SOURCE_PAGE,checked_at=now,expected=f'{len(months)} agregados originales y referencia congelada',actual=f'{len(months)} agregados coinciden; {count} evaluables; {flagged} candidatos, sin probabilidad',passed=True))
    return product,raw


def derive_sst_anomalies(now:datetime):
    product,raw=build_sst_anomalies(now)
    return publish(product,raw,'.json')
