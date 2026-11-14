"""Reproducible retained-asset/API consistency check, not predictive validation."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from urllib.request import urlopen
from urllib.parse import urlparse
from earth_echo.paths import repo_root
from earth_echo.storage.products import all_products, products_root, atomic_json
from earth_echo.contracts.products import ScientificProduct, ProductList
from earth_echo.ops.refresh import execution_lock, state_path


def verify(base):
    target=urlparse(base)
    if target.scheme!='http' or target.hostname not in {'127.0.0.1','localhost','::1'} or target.username or target.password:
        raise ValueError('Verification target must be the local API, without credentials')
    base=base.rstrip('/')
    def get(path,limit=64_000_000):
        with urlopen(base+path,timeout=30) as response:
            raw=response.read(limit+1)
            if len(raw)>limit:raise ValueError('Local API response exceeded verification budget')
            return raw
    with execution_lock(state_path().with_suffix('.lock')) as acquired:
        if not acquired:raise RuntimeError('Refresh is running; verify again after its bounded job completes')
        root=repo_root()
        integrity=json.loads((root/'data/operational/reference_integrity.json').read_bytes())
        for name,expected in integrity['files'].items():
            if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:raise ValueError(f'Original reference changed: {name}')
        products=all_products()
        listed_raw=get('/v1/products?summaries=true',1_000_000)
        listed=ProductList.model_validate_json(listed_raw)
        if {p.id for p in listed.products}!={p.id for p in products}:raise ValueError('API/local product coverage disagrees')
        if any(p.samples or p.grid or p.regions or p.tracks for p in listed.products):raise ValueError('Summary transferred scientific arrays')
        checked_assets={}; evidence=[]
        for p in products:
            asset=products_root()/p.raw_file
            if p.checksum_sha256 not in checked_assets:
                raw=asset.read_bytes()
                if len(raw)!=p.byte_size or hashlib.sha256(raw).hexdigest()!=p.checksum_sha256:raise ValueError(f'Invalid retained original: {p.id}')
                served=get(f'/v1/products/{p.id}/original',p.byte_size)
                if hashlib.sha256(served).hexdigest()!=p.checksum_sha256:raise ValueError(f'Original download disagrees: {p.id}')
                checked_assets[p.checksum_sha256]=len(raw)
            served=ScientificProduct.model_validate_json(get(f'/v1/products/{p.id}'))
            if served!=p:raise ValueError(f'API scientific metadata/values disagree: {p.id}')
            if p.grid:
                present=[v for v in p.grid.values if v is not None]
                if (min(present,default=None),max(present,default=None))!=(p.grid.minimum,p.grid.maximum):raise ValueError(f'Field legend disagrees: {p.id}')
            evidence.append({'id':p.id,'source_id':p.source_id,'sha256':p.checksum_sha256,'unit':p.unit,'representation':p.representation,
                'samples':len(p.samples),'field_cells':len(p.grid.values) if p.grid else 0,'masked_points':sum(not s.map_eligible for s in p.samples),
                'native_verification':p.verification.model_dump(mode='json'),'api_detail_matches':True,'original_download_sha256_matches':True})
        quakes=json.loads(get('/v1/layers/d21-events',1_000_000))
        kp=json.loads(get('/v1/layers/d28-kp',1_000_000))
        if quakes['count']!=len(quakes['features']) or kp['geometry_kind']!='global_index':raise ValueError('Point/planetary layer contract mismatch')
        expected_obs=quakes['count']+kp['count']+sum(len(p.samples) for p in products if p.kind=='observation')
        if listed.observation_records!=expected_obs:raise ValueError('Observation counter includes other record types')
        if listed.calculated_field_products!=sum(p.grid is not None and p.calculation is not None for p in products):raise ValueError('Calculated-field counter includes nonfields')
        if listed.calculated_indicator_products!=sum(p.kind=='indicator' and p.calculation is not None for p in products):raise ValueError('Calculated-analysis counter disagrees')
        if listed.imported_indicator_records!=sum(len(p.samples) for p in products if p.kind=='indicator' and p.calculation is None):raise ValueError('Imported-indicator counter includes own analysis')
        return {'checked_at':datetime.now(timezone.utc).isoformat(),'scope':'Consistency of originals, decoding, API and counts; not forecast skill or independent scientific validation of models',
            'original_references_unchanged':True,'products':len(products),'connected_source_ids':sorted({p.source_id for p in products}|{'D21','D28'}),
            'unique_original_assets':len(checked_assets),'unique_original_bytes':sum(checked_assets.values()),'summary_bytes':len(listed_raw),
            'counts':listed.model_dump(exclude={'products'}),'refresh':json.loads(get('/v1/operations/refresh',1_000_000)),
            'ready':json.loads(get('/ready',1_000_000)),'evidence':evidence}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--api-base',default='http://127.0.0.1:8000')
    args=parser.parse_args()
    report=verify(args.api_base)
    path=repo_root()/'data/operational/integration_evidence.json'
    atomic_json(path,report)
    print(json.dumps({k:report[k] for k in ['products','connected_source_ids','unique_original_assets','unique_original_bytes','summary_bytes','counts']},ensure_ascii=False))


if __name__=='__main__':main()
