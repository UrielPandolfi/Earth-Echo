"""Sentry known-object assessments; never terrestrial pins or undiscovered objects."""
import hashlib
import json
import math
from datetime import datetime
from urllib.parse import urlencode
from earth_echo.connectors.http import download
from earth_echo.contracts.products import ScientificProduct, ProductSample, Verification
from earth_echo.storage.products import publish

URL = 'https://ssd-api.jpl.nasa.gov/sentry.api'

def parse_sentry(payload: dict) -> list[ProductSample]:
    if payload['signature']['source'] != 'NASA/JPL Sentry Data API' or str(payload['signature']['version']) != '2.0':
        raise ValueError('Unknown Sentry schema')
    if int(payload['count']) != len(payload['data']): raise ValueError('Truncated Sentry summary')
    samples = []
    for row in payload['data']:
        probability = float(row['ip'])
        definition = f"Probabilidad acumulada de impacto publicada por Sentry para el objeto conocido {row['des']}, sumada sobre sus impactos potenciales en {row['range']}; solución vigente al recuperar."
        samples.append(ProductSample(id=row['des'],value=probability,probability=probability,probability_definition=definition,
            quality='Evaluación orbital importada, revisable con nuevas observaciones', attributes={
                'objeto':row.get('fullname',row['des']),'años_evaluados':row['range'],'última_observación_fecha':row.get('last_obs'),
                'última_observación_JD':str(row.get('last_obs_jd','')),'Palermo_máximo':str(row.get('ps_max','')),
                'Torino_máximo':str(row.get('ts_max','')),'diámetro_km':str(row.get('diameter','')),'impactos_potenciales':str(row.get('n_imp',''))}))
    return sorted(samples,key=lambda s:s.value)

def fetch_sentry(now: datetime) -> str:
    # Sequential only: JPL explicitly disallows concurrent requests.
    raw,_ = download(URL,max_bytes=2_000_000)
    payload = json.loads(raw)
    samples = parse_sentry(payload)
    if not samples: raise ValueError('Empty Sentry summary requires investigation')
    probe = samples[-1]
    check_url = URL+'?'+urlencode({'des':probe.id})
    check_raw,_ = download(check_url,max_bytes=2_000_000)
    original = json.loads(check_raw)
    reference = float(original['summary']['ip'])
    if not math.isclose(probe.value,reference,rel_tol=1e-5,abs_tol=1e-12):
        raise ValueError('Sentry object detail disagrees with summary')
    sha = hashlib.sha256(raw).hexdigest()
    p = ScientificProduct(id='d29-sentry',source_id='D29',title='Sentry · objetos conocidos',collection_id='CNEOS Sentry summary',
        product_version=payload['signature']['version'],variable='cumulative_impact_probability',unit='1 (probabilidad definida)',native_unit='1',
        kind='orbital_assessment',representation='table',retrieved_at=now,ingested_at=now,original_url=URL,
        license_url='https://ssd-api.jpl.nasa.gov/doc/sentry.html',attribution='NASA/JPL CNEOS Sentry',checksum_sha256=sha,byte_size=len(raw),raw_file=f'd29-sentry/assets/{sha}.json',
        coverage='Objetos detectados y evaluados por Sentry. No existe geometría de impacto terrestre en este resumen.',cadence_seconds=86400,
        method_version='sentry-summary-v1',limitation='No incluye objetos no descubiertos. Un acercamiento no es un impacto; las evaluaciones pueden retirarse o cambiar. No se inventa una fecha o lugar de desastre.',samples=samples,
        verification=Verification(method=f'Probabilidad acumulada del objeto {probe.id} contrastada con endpoint de detalle, consultas secuenciales',original_url=check_url,checked_at=now,
            expected=str(reference),actual=str(probe.value),passed=True))
    return publish(p,raw,'.json')
