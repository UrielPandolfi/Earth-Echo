import io
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from urllib.error import HTTPError
import pytest
from earth_echo.connectors.hydroatlas import BASE, decode_basins
from earth_echo.connectors.zip_subset import FigshareZipSubset, ArchivedZipSubset


def test_authentic_basin_area_topology_and_native_members():
    root=Path(__file__).resolve().parents[3]/'data/samples/integrations/hydroatlas'
    members={BASE+'.'+ext:(root/('basins.'+ext)).read_bytes() for ext in ('shp','shx','dbf','prj')}
    samples,regions,native,display=decode_basins(members)
    assert [(s.id,s.value) for s in samples]==[('6030040020',150.3),('6030016980',19412.8)]
    assert len(regions)==2 and native==1519 and display<native
    assert all(s.time is None and s.probability is None and s.longitude is None for s in samples)
    assert 'normalizada' in samples[1].quality
    assert regions[1].extent.west< -58 and regions[1].extent.north< -33
    assert samples[1].attributes['COAST']=='1'
    # Independent binary SHX/SHP comparison rejects a shifted native header.
    import struct
    damaged=bytearray(members[BASE+'.shp'])
    struct.pack_into('<d',damaged,112,-90)
    with pytest.raises(ValueError,match='SHP/SHX'):
        decode_basins({**members,BASE+'.shp':bytes(damaged)})


def test_bounded_zip_replays_and_only_renews_expired_public_redirect(monkeypatch):
    import earth_echo.connectors.zip_subset as module
    stream=io.BytesIO()
    with ZipFile(stream,'w',ZIP_DEFLATED) as z:
        z.writestr('selected.dbf',b'actual member bytes')
        z.writestr('not-selected.bin',b'not requested')
    content=stream.getvalue();calls=[]
    def download(url,*,max_bytes,headers):
        calls.append(url)
        if len(calls)==1:
            raise HTTPError(url,403,'expired',{},io.BytesIO(b'<Error><Code>ExpiredRequest</Code></Error>'))
        start,end=map(int,headers['Range'].removeprefix('bytes=').split('-'))
        return content[start:end+1],{'Content-Range':f'bytes {start}-{end}/{len(content)}'}
    monkeypatch.setattr(module,'download',download)
    monkeypatch.setattr(module.time,'sleep',lambda seconds:None)
    source=FigshareZipSubset({'id':20087237,'size':len(content)})
    expected=source.members(['selected.dbf'])
    assert expected=={'selected.dbf':b'actual member bytes'}
    assert len(calls)==2 and calls[0]!=calls[1]
    assert ArchivedZipSubset(source.archive({})).members(['selected.dbf'])==expected
    def denied(url,**kwargs):
        raise HTTPError(url,403,'denied',{},io.BytesIO(b'<Error><Code>AccessDenied</Code></Error>'))
    monkeypatch.setattr(module,'download',denied)
    with pytest.raises(ValueError,match='HTTP 403'):
        FigshareZipSubset({'id':20087237,'size':len(content)}).read_at(0,10)


def test_zip_range_mismatch_and_collection_read_refused(monkeypatch):
    import earth_echo.connectors.zip_subset as module
    source=FigshareZipSubset({'id':20087237,'size':4_276_492_333})
    with pytest.raises(ValueError,match='40 MB'):
        source.read_at(0,source.size)
    monkeypatch.setattr(module,'download',lambda *args,**kw:(b'wrong',{'Content-Range':'bytes 0-4/5'}))
    with pytest.raises(ValueError,match='changed requested'):
        source.read_at(0,5)
