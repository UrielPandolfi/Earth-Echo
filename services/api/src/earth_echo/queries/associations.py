import hashlib
import csv
import io
from earth_echo.contracts.analyses import AssociationView
from earth_echo.ingest.associations import analysis_dir
from earth_echo.science.associations import METHOD
from earth_echo.storage.products import read_product
from earth_echo.ingest.d15_history import series_path


def association_view():
    try:view=AssociationView.model_validate_json((analysis_dir()/'current.json').read_bytes())
    except (OSError,ValueError):return AssociationView(status='unavailable',reason='No está disponible el análisis real de asociaciones; no se usa DEMO.',method_version=METHOD,execution_id='unavailable',computed_at=None,parameters={},references=[],verification='not_checked',pairs=[])
    stale=[]
    for pair in view.pairs:
        for source in pair.inputs:
            current=read_product(source.product_id)
            if current is None or current.checksum_sha256!=source.checksum_sha256:stale.append(source.product_id)
            if source.product_id=='d15-sst-seasonal-departures':
                try:changed=hashlib.sha256(series_path().read_bytes()).hexdigest()!=source.checksum_sha256
                except OSError:changed=True
                if changed:stale.append(source.product_id)
    return view.model_copy(update={'stale_inputs':sorted(set(stale)),'reason':'Entradas cambiadas/ausentes; se conserva el último análisis válido hasta recalcular.' if stale else view.reason})


def association_csv(key):
    view=association_view()
    pair=next((p for p in view.pairs if p.id==key),None)
    if pair is None:return None
    output=io.StringIO();writer=csv.writer(output)
    writer.writerow(['year','quarter','start_utc','end_exclusive_utc','x','y','residual_x','residual_y','x_name','x_unit','y_name','y_unit','method_version','execution_id'])
    for p in pair.points:
        writer.writerow([p.year,p.quarter,p.start.isoformat(),p.end.isoformat(),p.x,p.y,p.residual_x,p.residual_y,pair.x_name,pair.x_unit,pair.y_name,pair.y_unit,view.method_version,view.execution_id])
    return output.getvalue()
