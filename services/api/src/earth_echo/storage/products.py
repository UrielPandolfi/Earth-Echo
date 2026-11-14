"""Atomic content-addressed products. Raw downloads and decoded revisions stay together."""
import json
import os
import uuid
from pathlib import Path
from earth_echo.contracts.products import ScientificProduct
from earth_echo.paths import repo_root

def products_root() -> Path:
    return repo_root() / 'data/real/products'

def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temp.write_text(json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(',', ':')) + '\n', encoding='utf-8')
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)

def read_product(key: str, root: Path | None = None) -> ScientificProduct | None:
    path = (root or products_root()) / key / 'current.json'
    if not path.is_file():
        return None
    product = ScientificProduct.model_validate_json(path.read_bytes())
    if not ((root or products_root()) / product.raw_file).is_file():
        return None
    return product

def all_products(root: Path | None = None) -> list[ScientificProduct]:
    active = root or products_root()
    return [p for path in sorted(active.glob('*/current.json')) if (p := read_product(path.parent.name, active)) is not None]

def publish(product: ScientificProduct, raw: bytes, suffix: str, root: Path | None = None) -> str:
    import hashlib
    if hashlib.sha256(raw).hexdigest() != product.checksum_sha256 or len(raw) != product.byte_size:
        raise ValueError('Raw checksum mismatch')
    active = root or products_root()
    current = read_product(product.id, active)
    def scientific_metadata(p):
        metadata=p.model_dump(mode='json',exclude={'retrieved_at','ingested_at','checksum_sha256','byte_size','raw_file','verification'})
        metadata['verification']=p.verification.model_dump(mode='json',exclude={'checked_at'})
        return metadata
    metadata=scientific_metadata(product)
    same_asset=current is not None and (current.checksum_sha256==product.checksum_sha256 or (
        product.scientific_checksum_sha256 is not None and current.scientific_checksum_sha256==product.scientific_checksum_sha256))
    if same_asset and scientific_metadata(current)==metadata:
        return 'unchanged'
    used = sum(p.stat().st_size for p in active.rglob('*') if p.is_file()) if active.exists() else 0
    projected = used + (0 if (active/product.raw_file).exists() else len(raw)) + 2*len(product.model_dump_json().encode())
    budget=int(os.getenv('EARTH_ECHO_PRODUCT_STORE_MAX_BYTES','512000000'))
    if not 32_000_000<=budget<=2_000_000_000: raise ValueError('Product store budget must be between 32 MB and 2 GB')
    if projected > budget:
        raise OSError(f'Scientific product store reached its {budget} byte budget; last valid products preserved')
    target = active / product.raw_file
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        temp = target.with_suffix('.tmp')
        temp.write_bytes(raw)
        os.replace(temp, target)
    metadata_hash=hashlib.sha256(json.dumps(metadata,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:12]
    revision = active / product.id / 'revisions' / (product.checksum_sha256 + '-' + metadata_hash + '.json')
    atomic_json(revision, product.model_dump(mode='json'))
    atomic_json(active / product.id / 'current.json', product.model_dump(mode='json'))
    # Keep four bounded snapshots per product. Historical experiment assets live elsewhere.
    revisions = sorted(revision.parent.glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in revisions[4:]:
        previous = ScientificProduct.model_validate_json(old.read_bytes())
        old.unlink()
        referenced = any(json.loads(p.read_bytes()).get('raw_file') == previous.raw_file for p in active.glob('*/revisions/*.json'))
        if not referenced:
            (active / previous.raw_file).unlink(missing_ok=True)
    return 'stored'

