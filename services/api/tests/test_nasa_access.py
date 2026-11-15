"""Authentic CMR fixtures; controlled transport without real credentials."""
import io
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from earth_echo.connectors import nasa_access as nasa
from earth_echo.connectors.ranges import ArchivedRangeSource
from earth_echo.tools import nasa_access as doctor


SAMPLES=Path(__file__).resolve().parents[3]/'data/samples/nasa-access'


def metadata(sid):
    return (SAMPLES/f'{sid}-cmr.json').read_bytes()


def science_url(sid='D02'):
    return nasa.decode_discovery(metadata(sid),sid)['science_url']


class Response:
    def __init__(self,status=200,headers=None,body=b''):
        self.status_code=status
        self.headers=headers or {}
        self.raw=io.BytesIO(body)
        self.closed=False

    def close(self):
        self.closed=True


class Session:
    def __init__(self,responses):
        self.responses=list(responses)
        self.calls=[]

    def request(self,method,url,**kwargs):
        self.calls.append((method,url,kwargs))
        response=self.responses.pop(0)
        if isinstance(response,Exception):
            raise response
        return response


def head(etag='"native-version"'):
    return Response(headers={'Content-Length':'12','Accept-Ranges':'bytes','ETag':etag})


def source(session):
    return nasa.EarthdataRangeSource('D02',science_url(),session=session,max_bytes=12,max_requests=1)


@pytest.fixture
def no_credentials(monkeypatch):
    for name in ('EARTHDATA_USERNAME','EARTHDATA_PASSWORD','EARTHDATA_TOKEN'):
        monkeypatch.delenv(name,raising=False)


def test_authentic_discovery_preserves_versions_and_granule_time_semantics():
    smap=nasa.decode_discovery(metadata('D02'),'D02')
    assert smap['dataset_version']=='006'
    assert smap['granule_id'].endswith('_001.h5')  # Not the collection version.
    assert smap['granule_metadata_start']=='2026-11-13T00:00:00+00:00'
    assert smap['granule_metadata_end']=='2026-11-13T23:59:59.999000+00:00'
    gldas=nasa.decode_discovery(metadata('D03'),'D03')
    assert gldas['dataset_version']=='2.1'
    assert gldas['granule_metadata_start']==gldas['granule_metadata_end']=='2026-07-31T21:00:00+00:00'
    for row in (smap,gldas):
        assert row['scientific_values_verified'] is False
        assert row['published_as_product'] is False


@pytest.mark.parametrize('replacement',[
    'https://attacker.example/file.h5',
    'http://data.nsidc.earthdatacloud.nasa.gov/nsidc-cumulus-prod-protected/SMAP/SPL3SMP_E/006/file.h5',
    'https://secret@data.nsidc.earthdatacloud.nasa.gov/nsidc-cumulus-prod-protected/SMAP/SPL3SMP_E/006/file.h5',
    'https://data.nsidc.earthdatacloud.nasa.gov/nsidc-cumulus-prod-protected/SMAP/SPL3SMP_E/005/file.h5',
    'https://data.nsidc.earthdatacloud.nasa.gov/nsidc-cumulus-prod-protected/SMAP/SPL3SMP_E/006/../file.h5',
    'https://data.nsidc.earthdatacloud.nasa.gov/nsidc-cumulus-prod-protected/SMAP/SPL3SMP_E/006/%66ile.h5',
])
def test_invalid_product_destination_rejected_before_auth(monkeypatch,replacement):
    monkeypatch.setattr(nasa,'authenticated_session',lambda:pytest.fail('Must validate before authentication'))
    with pytest.raises(ValueError,match='outside verified'):
        nasa.EarthdataRangeSource('D02',replacement)


def test_missing_credentials_refuses_sdk_or_netrc_fallback(no_credentials,monkeypatch):
    monkeypatch.setitem(sys.modules,'earthaccess',SimpleNamespace(login=lambda **kw:pytest.fail('No SDK login')))
    with pytest.raises(nasa.EarthdataCredentialsMissing,match='no interactive login or netrc'):
        nasa.authenticated_session()


def test_sdk_uses_only_environment_without_persistence_or_secret_output(no_credentials,monkeypatch,capsys):
    monkeypatch.setenv('EARTHDATA_TOKEN','sensitive-test-token')
    session=SimpleNamespace(auth=None)
    calls=[]
    def login(**kwargs):
        calls.append(kwargs)
        print('sensitive-test-token')
        print('sensitive-test-token',file=sys.stderr)
        return SimpleNamespace(authenticated=True)
    monkeypatch.setitem(sys.modules,'earthaccess',SimpleNamespace(login=login,get_requests_https_session=lambda:session))
    monkeypatch.setattr(nasa.truststore,'inject_into_ssl',lambda:None)
    assert nasa.authenticated_session() is session
    assert calls==[{'strategy':'environment','persist':False}]
    assert session.auth is not None  # Explicit auth prevents implicit requests/netrc.
    assert 'sensitive-test-token' not in str(capsys.readouterr())
    def fail(**kwargs):
        raise RuntimeError('sensitive-test-token https://private/?signed=secret')
    monkeypatch.setitem(sys.modules,'earthaccess',SimpleNamespace(login=fail))
    with pytest.raises(nasa.EarthdataAccessError) as error:
        nasa.authenticated_session()
    assert 'sensitive' not in str(error.value) and '?signed=' not in str(error.value)
    assert error.value.__suppress_context__ is True


def test_blank_example_token_does_not_override_configured_username_password(no_credentials,monkeypatch):
    monkeypatch.setenv('EARTHDATA_USERNAME','test-user')
    monkeypatch.setenv('EARTHDATA_PASSWORD','test-password')
    monkeypatch.setenv('EARTHDATA_TOKEN','')
    monkeypatch.setattr(nasa.truststore,'inject_into_ssl',lambda:None)
    def login(**kwargs):
        assert os.getenv('EARTHDATA_TOKEN') is None
        assert os.getenv('EARTHDATA_USERNAME')=='test-user'
        return SimpleNamespace(authenticated=True)
    monkeypatch.setitem(sys.modules,'earthaccess',SimpleNamespace(login=login,get_requests_https_session=lambda:SimpleNamespace()))
    nasa.authenticated_session()
    assert os.getenv('EARTHDATA_TOKEN')==''


def test_strong_versioned_ranges_cache_replay_and_archive_are_public():
    body=b'abcdefghijkl'
    session=Session([head(),Response(206,{'Content-Range':'bytes 0-11/12','ETag':'"native-version"','Set-Cookie':'private-cookie'},body)])
    src=source(session)
    assert src.read_at(2,5)==b'cdefg'
    assert src.read_at(2,5)==b'cdefg'
    assert len(session.calls)==2 and src.transferred==12
    method,url,options=session.calls[-1]
    assert method=='GET' and url==science_url()
    assert options['headers']['Range']=='bytes=0-11'
    assert options['headers']['If-Match']=='"native-version"'
    assert options['verify'] is True and options['stream'] is True
    assert options['allow_redirects'] is False and options['timeout']==25
    archive=src.archive({'scope':'controlled transport test'})
    assert b'private-cookie' not in archive
    assert ArchivedRangeSource(archive).read_at(2,5)==b'cdefg'


def test_private_redirects_are_rejected_and_presigned_storage_gets_no_bearer():
    session=Session([Response(302,{'Location':'https://attacker.example/?token=secret'})])
    with pytest.raises(nasa.EarthdataAccessError,match='outside approved'):
        source(session)
    assert len(session.calls)==1
    signed='https://nsidc-cumulus-prod-protected.s3.us-west-2.amazonaws.com/file.h5?X-Amz-Signature=private-signature'
    session=Session([Response(302,{'Location':signed}),head()])
    src=source(session)
    assert session.calls[-1][2]['headers']['Authorization'] is None
    assert b'private-signature' not in src.archive({})
    assert src.url==science_url()


@pytest.mark.parametrize('response',[
    Response(200,{},b'x'*100),
    Response(206,{'Content-Range':'bytes 0-11/12'},b'x'*13),
    Response(206,{'Content-Range':'bytes 1-12/12'},b'x'*12),
    Response(206,{'Content-Range':'bytes 0-11/12','ETag':'"changed"'},b'x'*12),
    Response(206,{'Content-Range':'bytes 0-11/12','Content-Encoding':'gzip'},b'x'*12),
])
def test_ignored_or_invalid_science_range_never_enters_cache(response):
    src=source(Session([head(),response]))
    with pytest.raises((ValueError,nasa.EarthdataAccessError)):
        src.read_at(0,8)
    assert src.cache=={} and src.transferred==0 and response.closed


def test_weak_validator_login_page_and_unauthorized_are_not_science():
    with pytest.raises(nasa.EarthdataAccessError,match='strong version'):
        source(Session([head('W/"weak"')]))
    session=Session([Response(401)])
    with pytest.raises(nasa.EarthdataAccessError,match='HTTP401'):
        source(session)
    assert len(session.calls)==1
    with pytest.raises(nasa.EarthdataAccessError,match='login/permission page'):
        source(Session([Response(200,{'Content-Type':'text/html'})]))


def test_transient_failure_is_bounded_and_transport_error_redacts_signed_urls(monkeypatch):
    waits=[]
    monkeypatch.setattr(nasa.time,'sleep',waits.append)
    session=Session([Response(503),head()])
    assert source(session).size==12
    assert len(session.calls)==2 and waits==[1]
    session=Session([RuntimeError('secret signed-url'),RuntimeError('secret signed-url')])
    with pytest.raises(nasa.EarthdataAccessError) as error:
        source(session)
    assert 'secret' not in str(error.value) and len(session.calls)==2


def test_doctor_without_credentials_retains_only_authentic_metadata(no_credentials,monkeypatch,tmp_path):
    def discover(sid):
        raw=metadata(sid)
        return nasa.decode_discovery(raw,sid),raw
    monkeypatch.setattr(doctor,'discover',discover)
    monkeypatch.setattr(doctor,'repo_root',lambda:tmp_path)
    monkeypatch.setattr(doctor,'authenticated_session',lambda:pytest.fail('No credentials'))
    report=doctor.probe(['D02','D03'],verify_header=True,retain=True)
    assert [r['status'] for r in report['records']]==['credentials_missing']*2
    assert all(r['scientific_values_verified'] is False and r['published_as_product'] is False for r in report['records'])
    folder=tmp_path/'data/samples/nasa-access'
    assert (folder/'D02-cmr.json').read_bytes()==metadata('D02')
    assert len(list(folder.iterdir()))==3  # Two metadata responses and one report.
    assert not (tmp_path/'data/real').exists()
