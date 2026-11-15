"""Explore two fixed pairs using only retained and rechecked scientific inputs."""
import hashlib
import io
import json
import math
import os
import zipfile
from datetime import datetime,timezone
from pathlib import Path

import numpy as np

from earth_echo.contracts.analyses import AssociationView,AssociationPairView,AssociationPoint
from earth_echo.contracts.products import CalculationInput
from earth_echo.connectors.roni_history import decode_history
from earth_echo.connectors.rapid_transport import decode_transports
from earth_echo.ingest.sst_anomalies import checked_history
from earth_echo.ingest.d15_history import series_path
from earth_echo.paths import repo_root
from earth_echo.science.associations import METHOD,QuarterPair,analyze_pairs,MIN_PAIRS,MIN_PER_QUARTER,DRAWS,SEED
from earth_echo.storage.products import read_product,products_root,atomic_json


def analysis_dir():return repo_root()/'data/real/analyses/associations'


def native_source(key,now):
    source=read_product(key)
    if source is None:raise ValueError('Retained association input unavailable: '+key)
    raw=(products_root()/source.raw_file).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=source.checksum_sha256:raise ValueError('Association native checksum differs')
    if key=='d48-roni-history':
        if source.unit!='°C (RONI)' or source.method_version!='cpc-roni-history-ersstv6-v1':raise ValueError('Qualified RONI ERSSTv6 required')
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            original=archive.read('definition.html')
        native,_=decode_history(original,now)
    else:
        if source.unit!='Sv' or source.product_version!='v2024-2':raise ValueError('Qualified RAPID v2024-2 Sv required')
        native,_=decode_transports(raw);native=native['amoc_depth_1m']
    if [(s.time,s.valid_to,s.value) for s in native]!=[(s.time,s.valid_to,s.value) for s in source.samples]:raise ValueError('Association source samples differ from original')
    return source


def mean_quarter(monthly,year,quarter):
    values=[monthly.get((year,month)) for month in range(quarter*3-2,quarter*3+1)]
    return math.fsum(values)/3 if all(v is not None for v in values) else None


def build_associations(now):
    raw=series_path().read_bytes();months,support=checked_history(json.loads(raw))
    sst={(m.year,m.month):m.value for m in months}
    sst_sha=hashlib.sha256(raw).hexdigest()
    roni=native_source('d48-roni-history',now);amoc=native_source('d34-amoc-monthly',now)
    quarterly_roni={}
    for s in roni.samples:
        if s.time.month in (1,4,7,10):
            quarterly_roni[(s.time.year,(s.time.month-1)//3+1)]=s.value
    monthly_amoc={}
    for s in amoc.samples:
        key=(s.time.year,s.time.month)
        if key in monthly_amoc:raise ValueError('Duplicate RAPID monthly input')
        monthly_amoc[key]=s.value
    cases=[('enso-sst','ENSO y SST del Caribe',roni,2025,'RONI ERSSTv6','°C (RONI)','Niño3.4, corregido por media tropical20S–20N; base1991–2020',quarterly_roni),
        ('amoc-sst','AMOC y SST del Caribe',amoc,2023,'Transporte AMOC RAPID','Sv','Sección RAPID26,5N; transporte integrado, positivo norte',None)]
    results=[]
    for key,title,source,end_year,x_name,x_unit,scope,qroni in cases:
        pairs=[QuarterPair(year,q,qroni.get((year,q)) if qroni is not None else mean_quarter(monthly_amoc,year,q),mean_quarter(sst,year,q)) for year in range(2014,end_year+1) for q in range(1,5)]
        result=analyze_pairs(pairs)
        present=[p for p in pairs if p.x is not None and p.y is not None]
        if result['status']=='evaluated':
            # Separate implementation: explicit 4-intercept design and SVD.
            design=np.array([[float(p.quarter==q) for q in range(1,5)]+[p.year-2014+(p.quarter-.5)/4] for p in present])
            x=np.array([p.x for p in present]);y=np.array([p.y for p in present])
            rx=x-design@np.linalg.lstsq(design,x,rcond=None)[0];ry=y-design@np.linalg.lstsq(design,y,rcond=None)[0]
            expected=float(np.corrcoef(rx,ry)[0,1])
            if not math.isclose(result['residual_r'],expected,abs_tol=1e-11,rel_tol=0):raise ValueError('Independent association SVD/correlation disagrees')
            if not math.isclose(result['raw_r'],float(np.corrcoef(x,y)[0,1]),abs_tol=1e-12,rel_tol=0):raise ValueError('Independent raw correlation disagrees')
            for p,a,b in zip(present,rx,ry,strict=True):
                r=result['residuals'][(p.year,p.quarter)]
                if not np.allclose(r,[a,b],atol=1e-11,rtol=0):raise ValueError('Independent association residuals differ')
        points=[]
        for p in pairs:
            start=datetime(p.year,p.quarter*3-2,1,tzinfo=timezone.utc)
            end=datetime(p.year+(p.quarter==4),1 if p.quarter==4 else p.quarter*3+1,1,tzinfo=timezone.utc)
            residual=result['residuals'].get((p.year,p.quarter),(None,None))
            points.append(AssociationPoint(year=p.year,quarter=p.quarter,start=start,end=end,x=p.x,y=p.y,residual_x=residual[0],residual_y=residual[1]))
        warnings=[
            'Asociación contemporánea exploratoria de un par fijado a priori; desfase0, sin buscar el máximo entre retrasos o regiones.',
            'JFM/AMJ/JAS/OND no se solapan; se promedian tres medias mensuales con igual peso para SST/AMOC, no por días. RONI conserva su trimestre publicado.',
            'Cada variable pierde cuatro interceptos estacionales y una tendencia lineal, ajustados sobre el soporte conjunto completo del período retrospectivo. Los datos de referencia del detector de anomalías no se reutilizan como umbral de correlación.',
            'Los intervalos aproximados95% son condicionales a esos ajustes, con bootstrap circular de residuos emparejados en bloques4y8trimestres/1000réplicas; no incluyen incertidumbre de instrumentos, referencia o estimación de tendencias. Suponen residuos aproximadamente estacionarios y dependencia limitada al bloque; pocos años y variación de longitud pueden cambiar el intervalo.',
            'No hay prueba de significación, corrección por dos pares o p-valor; no se selecciona el intervalo más favorable ni se considera excluir cero como evidencia causal. Confusores, error común y dirección causal no identificados; sin validación predictiva.',
        ]
        if key=='enso-sst':warnings.append('RONI resta SST media tropical que incluye el Caribe: puede existir acoplamiento matemático y fuentes climáticas compartidas. La asociación no demuestra teleconexión causal independiente; RONI y ONI son índices distintos y no se mezclan.')
        results.append(AssociationPairView(id=key,title=title,status=result['status'],reason=result['reason'],x_name=x_name,y_name='SST trimestral Caribe',x_unit=x_unit,y_unit='°C',x_scope=scope,
            y_scope=f'CoralTempv3.1,441celdas0,05°, bordes nativos{support.west:.5f}/{support.south:.5f}/{support.east:.5f}/{support.north:.5f}; no SST global o temperatura del aire',
            **{k:result[k] for k in ('n_pairs','missing_pairs','raw_r','residual_r','slope_x_per_year','slope_y_per_year','intervals')},points=points,
            inputs=[CalculationInput(product_id=source.id,variable=source.variable,unit=source.unit,checksum_sha256=source.checksum_sha256),CalculationInput(product_id='d15-sst-seasonal-departures',variable='retained regional monthly SST input',unit='°C',checksum_sha256=sst_sha)],warnings=warnings))
    view=AssociationView(status='evaluated' if any(p.status=='evaluated' for p in results) else 'not_evaluable',method_version=METHOD,execution_id='',computed_at=now,
        parameters={'minimum_pairs':MIN_PAIRS,'minimum_per_quarter':MIN_PER_QUARTER,'bootstrap_draws':DRAWS,'seed':SEED,'primary_block_quarters':4,'sensitivity_block_quarters':8,'lag_quarters':0,'interval_coverage':.95},
        references=['https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/correlat.htm','https://doi.org/10.1214/aos/1176347265','https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/'],
        verification='Entradas nativas redecodificadas/hashes verificados,144medias SST cotejadas con NetCDF independiente; ambas correlaciones y todos los residuos contrastados con diseño explícito NumPy/SVD. No demuestra causalidad ni habilidad predictiva.',pairs=results)
    canonical=view.model_dump(mode='json',exclude={'computed_at','execution_id','stale_inputs'})
    execution=hashlib.sha256(json.dumps(canonical,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest()
    return view.model_copy(update={'execution_id':execution})


def derive_associations(now):
    view=build_associations(now);folder=analysis_dir();current=folder/'current.json'
    if current.is_file() and AssociationView.model_validate_json(current.read_bytes()).execution_id==view.execution_id:return 'unchanged'
    encoded=view.model_dump_json().encode()
    if len(encoded)>2_000_000:raise ValueError('Association report exceeded2MB limit')
    analysis_root=folder.parent
    used=sum(p.stat().st_size for root in (analysis_root,products_root()) if root.exists() for p in root.rglob('*') if p.is_file())
    budget=int(os.getenv('EARTH_ECHO_PRODUCT_STORE_MAX_BYTES','512000000'))
    if not 32_000_000<=budget<=2_000_000_000:raise ValueError('Scientific storage budget must be32MB…2GB')
    if used+2*len(encoded)>budget:raise OSError('Scientific storage budget reached; previous analyses retained')
    atomic_json(folder/'revisions'/(view.execution_id+'.json'),view.model_dump(mode='json'))
    atomic_json(current,view.model_dump(mode='json'))
    for old in sorted((folder/'revisions').glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[4:]:old.unlink()
    return 'stored'
