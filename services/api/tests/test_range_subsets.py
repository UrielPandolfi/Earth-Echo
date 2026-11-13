import io
from datetime import datetime,timezone
import pytest
from earth_echo.connectors import ranges
from earth_echo.connectors.marine_heatwaves import month_window

class Head:
    headers={'Content-Length':'12','Accept-Ranges':'bytes','ETag':'W/"version"','Last-Modified':'Fri, 13 Nov 2026 00:00:00 GMT'}
    def __enter__(self): return self
    def __exit__(self,*args): pass

def test_weak_etag_uses_correct_http_condition_and_retained_bytes_replay(monkeypatch):
    monkeypatch.setattr(ranges,'urlopen',lambda *a,**kw:Head())
    calls=[]; original=b'abcdefghijkl'
    def get(url,max_bytes,headers):
        calls.append(headers)
        assert 'If-Match' not in headers
        assert headers['If-Unmodified-Since']==Head.headers['Last-Modified']
        start,end=[int(v) for v in headers['Range'][6:].split('-')]
        return original[start:end+1],{'Content-Range':f'bytes {start}-{end}/12'}
    monkeypatch.setattr(ranges,'download',get)
    source=ranges.RangeSource('https://example.org/data',max_bytes=8,max_requests=2)
    source.block_size=4
    with source.open() as f:
        f.seek(2); assert f.read(5)==b'cdefg'
        f.seek(2); assert f.read(5)==b'cdefg'
        assert len(calls)==2  # read cache, no duplicate download
        with pytest.raises(ValueError,match='budget'): f.read(5)
    replay=ranges.ArchivedRangeSource(source.archive({'scope':'test'}))
    assert replay.read_at(2,5)==b'cdefg'
    with pytest.raises(ValueError): replay.read_at(9,1) # never silently fetch an unretained block

def test_marine_monthly_horizon_includes_lead_definition_and_year_boundary():
    initial=datetime(2026,10,1,tzinfo=timezone.utc)
    start,end=month_window(initial,3.5)
    assert start==datetime(2027,1,1,tzinfo=timezone.utc)
    assert end==datetime(2027,2,1,tzinfo=timezone.utc)
    with pytest.raises(ValueError): month_window(initial,1.2)
