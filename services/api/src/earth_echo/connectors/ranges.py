"""Seekable, strictly bounded scientific HTTP Range access, with replayable raw blocks."""
import base64
import io
import json
import ssl
import time
from urllib.request import Request,urlopen
import truststore
from earth_echo.connectors.http import download

class RangeSource:
    def __init__(self,url: str,*,max_bytes=8_000_000,max_requests=48,deadline_seconds=120):
        if not 30<=deadline_seconds<=420:raise ValueError('Scientific range deadline must be30…420seconds')
        self.url=url; self.max_bytes=max_bytes; self.max_requests=max_requests
        with urlopen(Request(url,method='HEAD',headers={'User-Agent':'EarthEcho/0.2'}),timeout=25,context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)) as response:
            self.size=int(response.headers['Content-Length'])
            self.etag=response.headers.get('ETag')
            self.modified=response.headers.get('Last-Modified')
            if response.headers.get('Accept-Ranges')!='bytes': raise ValueError('Provider does not advertise byte ranges')
        self.block_size=131072; self.cache={}; self.requests=0; self.transferred=0
        self.deadline_seconds=deadline_seconds
        self.deadline=time.monotonic()+deadline_seconds

    def open(self): return RangeReader(self)

    def read_at(self,offset,length):
        if offset<0 or length<0: raise ValueError('Invalid range')
        length=min(length,max(0,self.size-offset))
        if length>self.max_bytes: raise ValueError('Unbounded read refused')
        out=[]
        while length:
            block=offset//self.block_size*self.block_size
            if block not in self.cache:
                if time.monotonic()>=self.deadline: raise TimeoutError(f'Scientific subset exceeded {self.deadline_seconds} seconds; previous retained')
                end=min(block+self.block_size,self.size)-1
                if self.requests>=self.max_requests or self.transferred+(end-block+1)>self.max_bytes:
                    raise ValueError('Scientific subset exceeds byte/request budget; full collection was not downloaded')
                headers={'Range':f'bytes={block}-{end}'}
                # HTTP If-Match requires strong validators; a weak ETag never matches it.
                if self.etag and not self.etag.startswith('W/'): headers['If-Match']=self.etag
                elif self.modified: headers['If-Unmodified-Since']=self.modified
                raw,meta=download(self.url,max_bytes=end-block+1,headers=headers)
                lowered={k.lower():v for k,v in meta.items()}
                if lowered.get('content-range')!=f'bytes {block}-{end}/{self.size}' or len(raw)!=end-block+1:
                    raise ValueError('Range response does not match requested offsets/version')
                self.cache[block]=raw; self.requests+=1; self.transferred+=len(raw)
            raw=self.cache[block]; take=min(length,len(raw)-(offset-block))
            out.append(raw[offset-block:offset-block+take]); offset+=take; length-=take
        return b''.join(out)

    def archive(self,metadata: dict) -> bytes:
        return json.dumps({'url':self.url,'size':self.size,'etag':self.etag,'last_modified':self.modified,'block_size':self.block_size,
            'metadata':metadata,'blocks':{str(k):base64.b64encode(v).decode() for k,v in sorted(self.cache.items())}},sort_keys=True,separators=(',',':')).encode()

class RangeReader(io.RawIOBase):
    def __init__(self,source): super().__init__(); self.source=source; self.position=0
    def readable(self): return True
    def seekable(self): return True
    def writable(self): return False
    def tell(self): return self.position
    def seek(self,offset,whence=0):
        position=offset+(self.position if whence==1 else self.source.size if whence==2 else 0)
        if position<0: raise ValueError('Negative seek')
        self.position=position; return position
    def read(self,size=-1):
        if size<0: size=self.source.size-self.position
        raw=self.source.read_at(self.position,size); self.position+=len(raw); return raw
    def readinto(self,buffer):
        raw=self.read(len(buffer)); buffer[:len(raw)]=raw; return len(raw)

class ArchivedRangeSource(RangeSource):
    def __init__(self,raw: bytes):
        payload=json.loads(raw)
        self.url=payload['url']; self.size=payload['size']; self.etag=payload['etag']; self.modified=payload['last_modified']
        self.block_size=payload['block_size']; self.cache={int(k):base64.b64decode(v) for k,v in payload['blocks'].items()}
        self.max_bytes=sum(len(v) for v in self.cache.values()); self.max_requests=0; self.requests=0; self.transferred=0
        self.deadline=float('inf')
