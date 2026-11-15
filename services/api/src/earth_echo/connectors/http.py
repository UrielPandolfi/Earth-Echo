"""Bounded HTTPS downloads; two attempts for transient errors, never auth retries."""
import time
import ssl
import truststore
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

def download(url: str, *, max_bytes: int = 8_000_000, headers: dict[str, str] | None = None, timeout: int = 25) -> tuple[bytes, dict[str, str]]:
    for attempt in range(2):
        try:
            with urlopen(Request(url, headers={'User-Agent': 'EarthEcho/0.2 (scientific subset)', **(headers or {})}), timeout=timeout, context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)) as response:
                body = response.read(max_bytes + 1)
                if len(body) > max_bytes:
                    raise ValueError('Provider exceeded bounded download')
                return body, dict(response.headers)
        except (HTTPError, URLError, TimeoutError) as error:
            if attempt or (isinstance(error, HTTPError) and error.code not in {429, 500, 502, 503, 504}):
                raise
            time.sleep(1)
    raise RuntimeError('Download failed')
