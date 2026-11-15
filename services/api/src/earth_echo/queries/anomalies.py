import hashlib
from earth_echo.contracts.analyses import SSTAnomalyView
from earth_echo.ingest.d15_history import series_path
from earth_echo.ingest.sst_anomalies import PRODUCT_ID,METHOD
from earth_echo.storage.products import read_product


def anomaly_view():
    product=read_product(PRODUCT_ID)
    if product is None or product.method_version!=METHOD:
        return SSTAnomalyView(status='unavailable',reason='No está calculado el análisis real de anomalías; no se usó DEMO.')
    try:stale=hashlib.sha256(series_path().read_bytes()).hexdigest()!=product.checksum_sha256
    except OSError:stale=True
    assessed=sum(s.category in {'warm_departure','cold_departure','within_threshold'} for s in product.samples)
    warm=sum(s.category=='warm_departure' for s in product.samples)
    cold=sum(s.category=='cold_departure' for s in product.samples)
    return SSTAnomalyView(status='evaluated' if assessed else 'not_evaluable',reason='Entrada cambió o no está disponible: se conserva el último análisis válido hasta recalcular.' if stale else None,
        assessed_months=assessed,flagged_months=warm+cold,warm_months=warm,cold_months=cold,
        missing_months=sum(s.category in {'missing','not_evaluable'} for s in product.samples),stale_input=stale,product=product)
