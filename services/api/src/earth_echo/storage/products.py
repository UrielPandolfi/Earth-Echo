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
    if hashlib.sha256(raw).hexdigest() != product.checksum_sha256:
        raise ValueError('Raw checksum mismatch')
    active = root or products_root()
    current = read_product(product.id, active)
    if current is not None and current.checksum_sha256 == product.checksum_sha256:
        return 'unchanged'
    target = active / product.raw_file
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        temp = target.with_suffix('.tmp')
        temp.write_bytes(raw)
        os.replace(temp, target)
    revision = active / product.id / 'revisions' / (product.checksum_sha256 + '.json')
    atomic_json(revision, product.model_dump(mode='json'))
    atomic_json(active / product.id / 'current.json', product.model_dump(mode='json'))
    # Keep four bounded snapshots per product. Historical experiment assets live elsewhere.
    revisions = sorted(revision.parent.glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in revisions[4:]:
        previous = ScientificProduct.model_validate_json(old.read_bytes())
        (active / previous.raw_file).unlink(missing_ok=True)
        old.unlink()
    return 'stored'
