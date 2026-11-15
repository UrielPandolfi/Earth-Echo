"""Sentry known-object assessments; never terrestrial pins or undiscovered objects."""
import hashlib
import json
import math
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from urllib.parse import urlencode
from earth_echo.connectors.http import download
from earth_echo.contracts.products import ScientificProduct, ProductSample, Verification
from earth_echo.storage.products import publish

URL = 'https://ssd-api.jpl.nasa.gov/sentry.api'
SOURCE = 'NASA/JPL Sentry Data API'
VERSION = '2.0'
_DATE = re.compile(r'^(\d{4})-(\d{2})-(\d{2})\.(\d+)$')
_YEARS = re.compile(r'^\d{4}-\d{4}$')


def require_signature(payload: dict) -> str:
    signature = payload.get('signature') if isinstance(payload, dict) else None
    if not isinstance(signature, dict) or signature.get('source') != SOURCE or str(signature.get('version')) != VERSION:
        raise ValueError('Unknown Sentry schema')
    return str(signature['version'])


def probability_token(token) -> tuple[str, float]:
    if not isinstance(token, str):
        raise ValueError('Sentry probability must stay the published string')
    text = token.strip()
    if not text or any(mark in text.lower() for mark in ('inf', 'nan')):
        raise ValueError('Sentry probability is not a finite published value')
    try:
        value = float(text)
    except ValueError as error:
        raise ValueError('Sentry probability is not a finite published value') from error
    if not math.isfinite(value) or value < 0 or value > 1:
        raise ValueError('Sentry probability is outside 0–1')
    return text, value


def optional_number(token):
    if token is None or token == '':
        return None
    if isinstance(token, bool) or isinstance(token, (list, dict)):
        raise ValueError('Sentry numeric field has an unexpected type')
    if isinstance(token, str) and token.strip().lower() == 'nan':
        return None
    try:
        value = float(token)
    except (TypeError, ValueError) as error:
        raise ValueError('Sentry numeric field is not finite') from error
    if not math.isfinite(value):
        return None
    return value


def optional_int(token):
    value = optional_number(token)
    if value is None:
        return None
    if not value.is_integer():
        raise ValueError('Sentry integer field is not an integer')
    return int(value)


def impact_instant(token: str) -> datetime | None:
    match = _DATE.fullmatch(token or '')
    if not match:
        return None
    year, month, day, fraction = match.groups()
    try:
        start = datetime(int(year), int(month), int(day), tzinfo=timezone.utc)
    except ValueError:
        return None
    seconds = Decimal(f'0.{fraction}') * Decimal(86400)
    whole = int(seconds)
    micro = int((seconds - Decimal(whole)) * Decimal(1000000))
    return start + timedelta(seconds=whole, microseconds=micro)


def _require_table(payload: dict) -> list:
    require_signature(payload)
    rows = payload.get('data')
    if not isinstance(rows, list) or int(payload['count']) != len(rows):
        raise ValueError('Truncated Sentry table')
    return rows


def parse_sentry(payload: dict) -> list[ProductSample]:
    rows = _require_table(payload)
    samples = []
    seen = set()
    for row in rows:
        designation = row['des']
        if designation in seen:
            raise ValueError('Duplicate Sentry designation')
        seen.add(designation)
        if not _YEARS.fullmatch(str(row.get('range') or '')):
            raise ValueError('Sentry year range is not a published year span')
        text, probability = probability_token(row['ip'])
        definition = (
            f"Probabilidad acumulada de impacto publicada por Sentry para el objeto conocido {designation}, "
            f"referida al intervalo de años {row['range']}. No es una suma recalculada de escenarios ni una probabilidad en un lugar de la Tierra."
        )
        samples.append(ProductSample(id=designation, map_eligible=False, value=probability, probability=probability, probability_definition=definition,
            quality='Evaluación orbital importada, revisable con nuevas observaciones', attributes={
                'objeto': row.get('fullname') or designation, 'años_evaluados': row['range'], 'última_observación_fecha': row.get('last_obs'),
                'última_observación_JD': str(row.get('last_obs_jd') or ''), 'Palermo_máximo': str(row.get('ps_max') or ''),
                'Torino_máximo': str(row.get('ts_max') or ''), 'diámetro_km': str(row.get('diameter') or ''),
                'impactos_potenciales': str(row.get('n_imp') or ''), 'probabilidad_texto': text}))
    if not samples:
        raise ValueError('Empty Sentry summary requires investigation')
    return sorted(samples, key=lambda sample: sample.value)


def parse_impactors(payload: dict) -> list[dict]:
    rows = _require_table(payload)
    scenarios = []
    for row in rows:
        text, probability = probability_token(row['ip'])
        instant = impact_instant(str(row.get('date') or ''))
        sigma_kind = next((name for name in ('sigma_vi', 'sigma_lov', 'sigma_mc') if row.get(name) not in (None, '')), None)
        scenarios.append({
            'designation': row['des'], 'date_text': str(row['date']), 'date_utc': None if instant is None else instant,
            'probability': probability, 'probability_text': text, 'palermo': optional_number(row.get('ps')),
            'torino': optional_int(row.get('ts')), 'energy_mt': None if row.get('energy') in (None, '') else str(row['energy']),
            'method': None if row.get('method') in (None, '') else str(row['method']),
            'sigma_kind': sigma_kind, 'sigma_text': None if sigma_kind is None else str(row[sigma_kind]),
        })
    if not scenarios:
        raise ValueError('Empty Sentry virtual-impactor table requires investigation')
    return scenarios


def parse_removed(payload: dict) -> list[dict]:
    rows = _require_table(payload)
    removed = []
    seen = set()
    for row in rows:
        designation = row['des']
        if designation in seen:
            raise ValueError('Duplicate removed Sentry designation')
        seen.add(designation)
        stamp = str(row.get('removed') or '').strip()
        if not stamp:
            raise ValueError('Removed Sentry object has no removal time')
        removed.append({'designation': designation, 'removed_at': stamp})
    if not removed:
        raise ValueError('Empty Sentry removed table requires investigation')
    return removed


def _product(product_id, title, variable, raw, payload, now, coverage, method, limitation, verification, samples=None) -> str:
    sha = hashlib.sha256(raw).hexdigest()
    product = ScientificProduct(id=product_id, source_id='D29', title=title, collection_id='CNEOS Sentry',
        product_version=payload['signature']['version'], variable=variable, unit='1 (probabilidad definida)', native_unit='1',
        kind='orbital_assessment', representation='table', retrieved_at=now, ingested_at=now, original_url=URL,
        license_url='https://ssd-api.jpl.nasa.gov/doc/sentry.html', attribution='NASA/JPL CNEOS Sentry', checksum_sha256=sha,
        byte_size=len(raw), raw_file=f'{product_id}/assets/{sha}.json', coverage=coverage, cadence_seconds=86400,
        method_version=method, limitation=limitation, samples=samples or [], verification=verification)
    return publish(product, raw, '.json')


def fetch_sentry(now: datetime) -> str:
    # Sequential only: JPL explicitly disallows concurrent requests.
    raw, _ = download(URL, max_bytes=2_000_000, timeout=60)
    payload = json.loads(raw)
    samples = parse_sentry(payload)
    probe = samples[-1]
    check_url = URL + '?' + urlencode({'des': probe.id})
    check_raw, _ = download(check_url, max_bytes=2_000_000, timeout=60)
    original = json.loads(check_raw)
    require_signature(original)
    reference_text, reference = probability_token(original['summary']['ip'])
    if not math.isclose(probe.value, reference, rel_tol=1e-5, abs_tol=1e-12):
        raise ValueError('Sentry object detail disagrees with summary')
    summary_status = _product('d29-sentry', 'Sentry · objetos conocidos', 'cumulative_impact_probability', raw, payload, now,
        'Objetos detectados y evaluados por Sentry. No existe geometría de impacto terrestre en este resumen.', 'sentry-summary-v1',
        'No incluye objetos no descubiertos. Un acercamiento no es un impacto; las evaluaciones pueden retirarse o cambiar. No se inventa una fecha o lugar de desastre.',
        Verification(method=f'Probabilidad acumulada del objeto {probe.id} contrastada con endpoint de detalle, consultas secuenciales', original_url=check_url, checked_at=now, expected=reference_text, actual=str(probe.value), passed=True),
        samples)
    vi_raw, _ = download(URL + '?all=1', max_bytes=20_000_000, timeout=90)
    vi_payload = json.loads(vi_raw)
    scenarios = parse_impactors(vi_payload)
    vi_status = _product('d29-sentry-impactors', 'Sentry · escenarios virtuales', 'virtual_impactor_probability', vi_raw, vi_payload, now,
        'Escenarios de impacto virtual publicados para los objetos de la tabla vigente. No hay coordenadas terrestres.', 'sentry-impactors-v1',
        'Cada probabilidad pertenece a un escenario virtual. No se suman para reemplazar la probabilidad acumulada del objeto y no indican un lugar de impacto.',
        Verification(method='Conteo de escenarios virtuales contra el campo count de la misma respuesta', original_url=URL + '?all=1', checked_at=now, expected=str(vi_payload['count']), actual=str(len(scenarios)), passed=True))
    removed_raw, _ = download(URL + '?removed=1', max_bytes=2_000_000, timeout=60)
    removed_payload = json.loads(removed_raw)
    removed = parse_removed(removed_payload)
    removed_status = _product('d29-sentry-removed', 'Sentry · objetos retirados', 'removed_object', removed_raw, removed_payload, now,
        'Objetos retirados de la tabla vigente. La hora es la publicada por Sentry; no se inventa el motivo ni se interpreta como impacto ocurrido.', 'sentry-removed-v1',
        'Un objeto retirado ya no tiene impactos potenciales en la solución vigente, en general por nuevas observaciones. Earth Echo no asigna otro motivo.',
        Verification(method='Conteo de objetos retirados contra el campo count de la misma respuesta', original_url=URL + '?removed=1', checked_at=now, expected=str(removed_payload['count']), actual=str(len(removed)), passed=True))
    return 'unchanged' if summary_status == vi_status == removed_status == 'unchanged' else 'stored'
