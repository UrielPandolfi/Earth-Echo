"""Independent numeric HDF5 chunk decoding for qualified DEFLATE/shuffle data.

HDF5 supplies raw chunk bytes/coordinates; zlib and NumPy decode the actual
numeric representation without asking HDF5 to decode its scientific values.
"""
from itertools import product
import zlib
import numpy as np


def native_window(dataset, leading, row_start, row_stop, col_start, col_stop):
    chunks = dataset.chunks
    if chunks is None or dataset.ndim != len(leading) + 2 or dataset.dtype.kind not in 'fiu':
        raise ValueError('Qualified chunked numeric HDF5 layout required')
    if any(not 0 <= i < dataset.shape[j] for j, i in enumerate(leading)) or not 0 <= row_start < row_stop <= dataset.shape[-2] or not 0 <= col_start < col_stop <= dataset.shape[-1]:
        raise ValueError('HDF5 native window outside dimensions')
    expected = int(np.prod(chunks)) * dataset.dtype.itemsize
    if expected > 16_777_216:
        raise ValueError('Native HDF5 chunk exceeds measured16MiB decode budget')
    plist = dataset.id.get_create_plist()
    filters = [plist.get_filter(i) for i in range(plist.get_nfilters())]
    if any(f[0] not in (1, 2) for f in filters):
        raise ValueError('Unqualified HDF5 filter pipeline; no silent alternate decode')
    result = np.empty((row_stop - row_start, col_stop - col_start), dtype=dataset.dtype)
    for row, col in product(range(row_start // chunks[-2] * chunks[-2], row_stop, chunks[-2]),
                            range(col_start // chunks[-1] * chunks[-1], col_stop, chunks[-1])):
        origin = tuple(i // chunks[j] * chunks[j] for j, i in enumerate(leading)) + (row, col)
        mask, raw = dataset.id.read_direct_chunk(origin)
        decoded = raw
        for i in range(len(filters) - 1, -1, -1):
            if mask & (1 << i):
                continue
            filter_id, _, parameters, _ = filters[i]
            if filter_id == 1:
                decoder = zlib.decompressobj()
                decoded = decoder.decompress(decoded, expected + 1)
                if len(decoded) != expected or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
                    raise ValueError('HDF5 DEFLATE chunk length/budget disagrees')
            elif filter_id == 2:
                if tuple(parameters) != (dataset.dtype.itemsize,) or len(decoded) != expected:
                    raise ValueError('HDF5 shuffle element size/length changed')
                decoded = np.frombuffer(decoded, dtype='u1').reshape(dataset.dtype.itemsize, -1).T.copy().tobytes()
        if len(decoded) != expected:
            raise ValueError('HDF5 decoded chunk size disagrees')
        array = np.frombuffer(decoded, dtype=dataset.dtype).reshape(chunks)
        leading_index = tuple(i - origin[j] for j, i in enumerate(leading))
        a, b = max(row, row_start), min(row + chunks[-2], row_stop)
        c, d = max(col, col_start), min(col + chunks[-1], col_stop)
        result[a-row_start:b-row_start, c-col_start:d-col_start] = array[leading_index + (slice(a-row, b-row), slice(c-col, d-col))]
    return result
