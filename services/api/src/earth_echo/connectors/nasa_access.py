"""Bounded NASA access preparation. Discovery/headers never count as integration."""
from contextlib import redirect_stdout,redirect_stderr
from datetime import datetime,timezone
from io import StringIO
from pathlib import PurePosixPath
from urllib.parse import urlencode,urlparse,urljoin
import hashlib
import json
import logging
import os
import re
import time
import truststore
from earth_echo.connectors.http import download
from earth_echo.connectors.ranges import RangeSource

CMR='https://cmr.earthdata.nasa.gov/search/granules.json'
SOURCES={
    'D02':('SPL3SMP_E','006','data.nsidc.earthdatacloud.nasa.gov','/nsidc-cumulus-prod-protected/SMAP/SPL3SMP_E/006/','.h5','nsidc-cumulus-prod-protected'),
    'D03':('GLDAS_NOAH025_3H','2.1','data.gesdisc.earthdata.nasa.gov','/data/GLDAS/GLDAS_NOAH025_3H.2.1/','.nc4','gesdisc-cumulus-prod-protected'),
}


class EarthdataAccessError(RuntimeError):pass
class EarthdataCredentialsMissing(EarthdataAccessError):pass


def credentials_present():
    return bool(os.getenv('EARTHDATA_TOKEN','').strip() or (os.getenv('EARTHDATA_USERNAME','').strip() and os.getenv('EARTHDATA_PASSWORD','').strip()))


def validate_science_url(source_id,url):
    if source_id not in SOURCES:raise ValueError('Unsupported NASA product')
    _,_,host,prefix,extension,_=SOURCES[source_id]
    p=urlparse(url)
    if p.scheme!='https' or p.hostname!=host or p.port not in (None,443) or p.username or p.password or p.query or p.fragment or '%' in p.path or '\\' in p.path or '..' in PurePosixPath(p.path).parts or not p.path.startswith(prefix) or not p.path.endswith(extension):
        raise ValueError('NASA science URL outside verified product/version; no credentials sent')
    return url


def decode_discovery(raw,source_id):
    rows=json.loads(raw)['feed']['entry']
    if len(rows)!=1:raise ValueError('Expected one bounded NASA granule')
    row=rows[0]
    links=[item['href'] for item in row.get('links',[]) if not item.get('inherited') and item.get('rel','').endswith('/data#')]
    if len(links)!=1:raise ValueError('NASA granule science link is not unambiguous')
    science_url=validate_science_url(source_id,links[0])
    def stamp(key):
        value=datetime.fromisoformat(row[key])
        if value.utcoffset() is None:raise ValueError('NASA metadata time lacks UTC offset')
        return value.astimezone(timezone.utc).isoformat()
    return {'source_id':source_id,'short_name':SOURCES[source_id][0],'dataset_version':SOURCES[source_id][1],
        'granule_concept_id':row['id'],'collection_concept_id':row['collection_concept_id'],'dataset_title':row['dataset_id'],
        'granule_id':row['producer_granule_id'],'science_url':science_url,'granule_metadata_start':stamp('time_start'),'granule_metadata_end':stamp('time_end'),
        'metadata_sha256':hashlib.sha256(raw).hexdigest(),'scientific_values_verified':False,'published_as_product':False}


def discover(source_id):
    short,version,*_=SOURCES[source_id]
    url=CMR+'?'+urlencode({'short_name':short,'version':version,'page_size':1,'sort_key':'-start_date'})
    raw,_=download(url,max_bytes=200_000)
    return {**decode_discovery(raw,source_id),'metadata_url':url},raw


def authenticated_session():
    if not credentials_present():
        raise EarthdataCredentialsMissing('Configure EARTHDATA_USERNAME/EARTHDATA_PASSWORD or EARTHDATA_TOKEN locally; no interactive login or netrc fallback')
    # Native CA trust, still TLS verification. No password/token logging or
    # persistence; strategy explicitly excludes interactive/netrc fallbacks.
    truststore.inject_into_ssl()
    logger=logging.getLogger('earthaccess');level=logger.level;logger.setLevel(logging.CRITICAL)
    # earthaccess 0.19 treats even an empty token as the preferred token.
    # .env.example intentionally contains EARTHDATA_TOKEN=; let a configured
    # username/password pair work without changing the user's local file.
    blank_token=os.environ.get('EARTHDATA_TOKEN')
    restore_blank_token=blank_token is not None and not blank_token.strip()
    if restore_blank_token:os.environ.pop('EARTHDATA_TOKEN',None)
    try:
        with redirect_stdout(StringIO()),redirect_stderr(StringIO()):
            import earthaccess
            auth=earthaccess.login(strategy='environment',persist=False)
            if not auth.authenticated:raise EarthdataAccessError('Earthdata authentication rejected; check local credentials and DAAC authorization')
            session=earthaccess.get_requests_https_session()
    except Exception:
        raise EarthdataAccessError('Earthdata authentication unavailable/rejected; check local credentials and manual DAAC authorization') from None
    finally:
        logger.setLevel(level)
        if restore_blank_token:os.environ['EARTHDATA_TOKEN']=blank_token
    # Keep proxy/CA environment settings but prevent implicit netrc credentials.
    from requests.auth import AuthBase
    class HeaderOnlyAuth(AuthBase):
        def __call__(self,request):return request
    session.auth=HeaderOnlyAuth()
    return session


class EarthdataRangeSource(RangeSource):
    def __init__(self,source_id,url,*,session=None,**limits):
        validate_science_url(source_id,url)
        self._source_id=source_id
        self._session=session if session is not None else authenticated_session()
        super().__init__(url,**limits)
        if not self.etag or self.etag.startswith('W/'):
            raise EarthdataAccessError('NASA streaming requires a strong version validator; no unversioned science ranges')

    def _redirect_allowed(self,url):
        p=urlparse(url);host=p.hostname or '';bucket=SOURCES[self._source_id][5]
        if p.scheme!='https' or p.port not in (None,443) or p.username or p.password:return False
        if host in {SOURCES[self._source_id][2],'urs.earthdata.nasa.gov'}:return True
        return bool(re.fullmatch(re.escape(bucket)+r'\.s3(?:[.-][a-z0-9-]+)?\.amazonaws\.com',host))

    def _request(self,method,url,headers=None):
        # Manual redirects validate destinations before a request is sent.
        # Bearer/header credentials never accompany presigned S3 requests.
        for attempt in range(2):
            current=url
            try:
                for _ in range(6):
                    h={'User-Agent':'EarthEcho/0.2 (bounded NASA access)','Accept-Encoding':'identity',**(headers or {})}
                    if (urlparse(current).hostname or '').endswith('.amazonaws.com'):h['Authorization']=None
                    response=self._session.request(method,current,headers=h,allow_redirects=False,timeout=25,stream=True,verify=True)
                    if response.status_code in {301,302,303,307,308}:
                        next_url=urljoin(current,response.headers.get('Location',''));response.close()
                        if not self._redirect_allowed(next_url):raise EarthdataAccessError('NASA redirect outside approved data/auth hosts; no follow-up request sent')
                        current=next_url;continue
                    if response.status_code in {429,500,502,503,504} and attempt==0:
                        response.close();break
                    if response.status_code not in {200,206}:
                        code=response.status_code;response.close()
                        raise EarthdataAccessError(f'NASA science access rejected (HTTP{code}); check manual DAAC permission/service status')
                    if 'text/html' in response.headers.get('Content-Type','').lower():
                        response.close();raise EarthdataAccessError('NASA returned a login/permission page, not a science file; authorize the DAAC manually')
                    return response
                else:raise EarthdataAccessError('NASA redirect limit exceeded')
            except EarthdataAccessError:raise
            except Exception:
                if attempt:raise EarthdataAccessError('NASA transport failed; details with credentials/signed URLs suppressed') from None
            if attempt==0:time.sleep(1)
        raise EarthdataAccessError('NASA transient transport failure; previous data retained')

    def _head(self,url):
        response=self._request('HEAD',url)
        try:return dict(response.headers)
        finally:response.close()

    def _fetch(self,url,*,max_bytes,headers):
        response=self._request('GET',url,headers)
        try:
            if response.status_code!=206:
                raise EarthdataAccessError('NASA ignored bounded science range; full granule was not downloaded')
            meta={key.lower():value for key,value in response.headers.items()}
            if meta.get('etag',self.etag)!=self.etag:
                raise EarthdataAccessError('NASA science object changed during range retrieval; retry discovery')
            if meta.get('content-encoding','identity').lower()!='identity':
                raise EarthdataAccessError('NASA range uses an unsupported transport encoding')
            raw=response.raw.read(max_bytes+1)
            if len(raw)>max_bytes:raise EarthdataAccessError('NASA ignored bounded science range; full granule was not downloaded')
            return raw,dict(response.headers)
        except EarthdataAccessError:raise
        except Exception:raise EarthdataAccessError('NASA bounded body read failed; private transport details suppressed') from None
        finally:response.close()
