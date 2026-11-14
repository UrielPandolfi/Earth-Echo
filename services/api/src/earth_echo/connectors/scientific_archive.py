"""Deterministic container of exact provider bytes and a provenance manifest."""
import io
import json
import zipfile


def pack_files(files, manifest, *, compression=zipfile.ZIP_STORED):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, raw in sorted({**files, 'manifest.json': json.dumps(manifest, sort_keys=True).encode()}.items()):
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
            info.compress_type=compression
            archive.writestr(info, raw)
    return out.getvalue()
