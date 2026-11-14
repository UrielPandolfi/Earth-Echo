"""Read selected members of a public Figshare ZIP without downloading the collection."""
import base64
import json
import time
from urllib.error import HTTPError
from uuid import uuid4
from zipfile import ZipFile
from earth_echo.connectors.http import download
from earth_echo.connectors.ranges import RangeReader


class FigshareZipSubset:
    def __init__(self, file: dict):
        self.file = file
        self.size = file['size']
        self.ranges: dict[int, bytes] = {}
        self.requests = 0
        self.transferred = 0

    def read_at(self, offset, length):
        if offset < 0 or length < 0 or offset + length > self.size:
            raise ValueError('Invalid ZIP range')
        if not length:
            return b''
        for start, raw in self.ranges.items():
            if start <= offset and offset + length <= start + len(raw):
                return raw[offset-start:offset-start+length]
        # Coalesce the tiny ZIP headers/directory probes into 64 KiB blocks.
        requested_offset, requested_length = offset, length
        if length < 65536:
            offset = offset // 65536 * 65536
            length = min(self.size-offset, 131072)
        if self.requests >= 24 or self.transferred + length > 40_000_000:
            raise ValueError('HydroATLAS subset exceeds 24 requests / 40 MB; collection refused')
        # The public CDN can cache an expired signed redirect. A fresh public URL
        # obtains a current redirect; credentials are neither supplied nor stored.
        for attempt in range(2):
            url = f'https://ndownloader.figshare.com/files/{self.file["id"]}?download=1&cache={uuid4().hex}'
            self.requests += 1
            try:
                raw, headers = download(url, max_bytes=length, headers={
                    'Range': f'bytes={offset}-{offset+length-1}', 'Cache-Control': 'no-cache'})
                break
            except HTTPError as error:
                body = error.read(2048)
                # Only renew a demonstrably expired public redirect, once. An
                # authorization denial is never retried as if it were expiry.
                if attempt or error.code != 403 or b'<Code>ExpiredRequest</Code>' not in body:
                    raise ValueError(f'Public Figshare range failed: HTTP {error.code}; previous retained') from None
                time.sleep(1)
        meta = {k.lower(): v for k, v in headers.items()}
        if len(raw) != length or meta.get('content-range') != f'bytes {offset}-{offset+length-1}/{self.size}':
            raise ValueError('Figshare ignored or changed requested ZIP range')
        self.transferred += len(raw)
        self.ranges[offset] = raw
        return raw[requested_offset-offset:requested_offset-offset+requested_length]

    def members(self, names):
        with RangeReader(self) as stream, ZipFile(stream) as archive:
            infos = [archive.getinfo(name) for name in names]
            if sum(i.file_size for i in infos) > 60_000_000 or any(i.flag_bits & 1 for i in infos):
                raise ValueError('Expanded/encrypted archive exceeds scientific subset budget')
            # ZipFile verifies uncompressed size and CRC32 independently of transport.
            return {i.filename: archive.read(i) for i in infos}

    def archive(self, metadata):
        return json.dumps({'file': self.file, 'metadata': metadata,
            'ranges': {str(k): base64.b64encode(v).decode() for k, v in sorted(self.ranges.items())}},
            sort_keys=True, separators=(',', ':')).encode()


class ArchivedZipSubset(FigshareZipSubset):
    def __init__(self, raw):
        payload = json.loads(raw)
        super().__init__(payload['file'])
        self.ranges = {int(k): base64.b64decode(v) for k, v in payload['ranges'].items()}

    def read_at(self, offset, length):
        if not length:
            return b''
        for start, raw in self.ranges.items():
            if start <= offset and offset + length <= start + len(raw):
                return raw[offset-start:offset-start+length]
        raise ValueError('Requested bytes are absent from retained ZIP subset')
