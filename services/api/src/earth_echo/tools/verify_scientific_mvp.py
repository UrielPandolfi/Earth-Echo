"""Recompute native scientific checks and compare retained results with local API."""
import argparse
import csv
import io
import json
import math
import numpy as np
from datetime import datetime,timezone
from urllib.request import urlopen,Request

from earth_echo.ingest.associations import build_associations
from earth_echo.ingest.sst_anomalies import build_sst_anomalies
from earth_echo.paths import repo_root
from earth_echo.storage.products import atomic_json
from earth_echo.storage.products import read_product,products_root
from earth_echo.ingest.oisst_anomaly import anomaly_from_source


def get(path,payload=None):
    request=Request('http://127.0.0.1:8000'+path,data=None if payload is None else json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    with urlopen(request,timeout=20) as response:
        raw=response.read(2_000_001)
    if len(raw)>2_000_000:raise ValueError('MVP API response exceeded2MB')
    return raw


def verify():
    now=datetime.now(timezone.utc)
    expected,_=build_sst_anomalies(now)
    anomaly=json.loads(get('/v1/analyses/d15-anomalies'))
    if anomaly['data_mode']!='real' or anomaly['status']!='evaluated' or anomaly['stale_input']:raise ValueError('Anomaly analysis unavailable/stale')
    if anomaly['product']['samples']!=expected.model_dump(mode='json')['samples'] or anomaly['product']['extent']!=expected.extent.model_dump(mode='json'):raise ValueError('Anomaly API differs from checked native history')
    associations=json.loads(get('/v1/analyses/associations'))
    expected_associations=build_associations(now)
    if associations['execution_id']!=expected_associations.execution_id or associations['stale_inputs']:raise ValueError('Association API differs from native recomputation')
    exports=[]
    for pair in expected_associations.pairs:
        rows=list(csv.DictReader(io.StringIO(get(f'/v1/analyses/associations/{pair.id}.csv').decode())))
        if len(rows)!=len(pair.points) or any(row['execution_id']!=expected_associations.execution_id for row in rows):raise ValueError('Association CSV mismatch')
        for row,point in zip(rows,pair.points,strict=True):
            for key in ('x','y','residual_x','residual_y'):
                if (None if row[key]=='' else float(row[key]))!=getattr(point,key):raise ValueError('Association CSV scientific value differs')
        exports.append({'pair':pair.id,'rows':len(rows),'raw_r':pair.raw_r,'residual_r':pair.residual_r,'intervals':[p.model_dump() for p in pair.intervals]})
    trend=json.loads(get('/v1/analyses/d15-sst'))
    if trend['source_series_sha256']!=expected.checksum_sha256 or trend['method_version']!='2' or trend['status']!='evaluated':raise ValueError('Seasonal trend version/input mismatch')
    present=[p for p in trend['series'] if p['sst_c'] is not None]
    design=np.array([[float(p['month']==month) for month in range(1,13)]+[p['year']-2014+(p['month']-.5)/12] for p in present])
    independent=float(np.linalg.lstsq(design,[p['sst_c'] for p in present],rcond=None)[0][-1])
    if not math.isclose(trend['slope_c_per_year'],independent,abs_tol=1e-12,rel_tol=0):raise ValueError('Trend slope differs from independent SVD')
    trend_rows=list(csv.DictReader(io.StringIO(get('/v1/analyses/d15-sst.csv').decode())))
    if len(trend_rows)!=len(trend['series']):raise ValueError('Trend CSV length mismatch')
    for row,point in zip(trend_rows,trend['series'],strict=True):
        if row['execution_id']!=trend['execution_id'] or row['source_series_sha256']!=expected.checksum_sha256 or row['unit']!='°C':raise ValueError('Trend CSV provenance mismatch')
        for key in ('sst_c','anomaly_c'):
            if (None if row[key]=='' else float(row[key]))!=point[key]:raise ValueError('Trend CSV value mismatch')
    oisst=read_product('d13-oisst-global')
    if oisst is None:raise ValueError('Daily OISST unavailable')
    daily_expected=anomaly_from_source(oisst,(products_root()/oisst.raw_file).read_bytes(),now)
    daily=json.loads(get('/v1/products/d13-oisst-anomaly-global'))
    if daily['grid']!=daily_expected.grid.model_dump(mode='json') or daily['checksum_sha256']!=oisst.checksum_sha256:raise ValueError('Daily anomaly API differs from original/aggregation')
    assistant_tools=[]
    for question,tool in [('¿Qué anomalías SST hay?','sst_anomalies'),('¿Qué relación hay entre AMOC y SST?','associations'),('¿Cuál es la tendencia de AMOC?','amoc_trend')]:
        reply=json.loads(get('/v1/assistant/ask',{'question':question,'context':{'data_mode':'real'}}))
        if reply['answer_kind']!='tool_template' or not reply['tools'] or reply['tools'][0]['tool']!=tool:raise ValueError('Scientific assistant did not use the verified template/tool')
        assistant_tools.append(tool)
    replay=json.loads(get('/v1/assistant/ask',{'question':'¿Qué relación hay entre AMOC y SST?','context':{'data_mode':'real','replay_issue':'2022-01','replay_revealed':False}}))
    if replay['tools'] or 'corte temporal' not in replay['text']:raise ValueError('Full scientific analysis leaked into a replay')
    return {'checked_at':now.isoformat(),'scope':'Native inputs, calculation arithmetic, persisted API and CSV consistency; no causal/predictive validation',
        'anomalies':{'method':expected.method_version,'months':len(expected.samples),'assessed_months':anomaly['assessed_months'],'flagged_months':anomaly['flagged_months'],'input_sha256':expected.checksum_sha256,'native_coverage':expected.extent.model_dump(mode='json')},
        'associations':{'method':expected_associations.method_version,'execution_id':expected_associations.execution_id,'causal_attribution':expected_associations.causal_attribution,'predictive_validation':expected_associations.predictive_validation,'pairs':exports},
        'trend':{key:trend[key] for key in ('method_id','method_version','execution_id','source_series_sha256','present_months','missing_months','slope_c_per_year','interval_low_c_per_year','interval_high_c_per_year','sensitivity_low_c_per_year','sensitivity_high_c_per_year','residual_lag1_r')},
        'daily_anomaly':{'source_id':'D13','method_version':daily_expected.method_version,'data_at':daily_expected.observed_at.isoformat(),'reference_period':'1971–2000','shared_original_sha256':oisst.checksum_sha256,'valid_display_cells':len(daily_expected.grid.values)-daily_expected.grid.missing_cells,'missing_display_cells':daily_expected.grid.missing_cells,'minimum_c':daily_expected.grid.minimum,'maximum_c':daily_expected.grid.maximum,'color_center':daily_expected.grid.color_center},
        'assistant':{'verified_templates':assistant_tools,'full_analysis_withheld_during_replay':True},
        'api_and_csv_consistent':True,'native_checks_passed':True,'new_external_downloads':0}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--retain',action='store_true');args=parser.parse_args()
    report=verify()
    if args.retain:atomic_json(repo_root()/'data/operational/mvp_scientific_evidence.json',report)
    print(json.dumps(report,ensure_ascii=True))


if __name__=='__main__':main()
