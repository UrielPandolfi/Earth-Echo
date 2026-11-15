"""Scientific fixture + controlled time/transport tests for the complete adapter."""
import hashlib
import json
import math
import struct
from datetime import datetime, timezone, timedelta
from pathlib import Path
import h5py
import numpy as np
import pytest
from fastapi.testclient import TestClient
from earth_echo.paths import repo_root
from earth_echo.connectors.ranges import ArchivedRangeSource
from earth_echo.contracts.products import ScientificGrid, ScientificProduct, Verification
from earth_echo.contracts.operations import RefreshStatus,RefreshJob
from earth_echo.science.forecast_grid import locate,cell_at,components
from earth_echo.queries import predictions as q
from earth_echo.storage.products import publish

NOW=datetime(2026,11,15,15,tzinfo=timezone.utc)
EMPTY_OPS=RefreshStatus(enabled=True,recent_scan=True,jobs={},note='controlled')


@pytest.fixture(scope='module')
def native():
    folder=repo_root()/'data/samples/forecast-map'
    raw=(folder/'nmme-oct2026-ranges.json').read_bytes();evidence=json.loads((folder/'evidence.json').read_bytes())
    assert hashlib.sha256(raw).hexdigest()==evidence['sha256']
    source=ArchivedRangeSource(raw)
    with source.open() as stream,h5py.File(stream,'r') as ds:
        assert bytes(ds['start_time'].attrs['units']).decode()=='days since 2021-01-01 00:00:00'
        xs=[float(v) for v in ds['lon'][200:300]];ys=[float(v) for v in ds['lat'][100:180]][::-1]
        lons=[(v+180)%360-180 for v in xs];t=len(ds['start_time'])-1;data=ds['mhw_probability']
        grids=[]
        for li in range(1,4):
            a=data[li,100:180,200:300,t][::-1,:]
            values=[None if not math.isfinite(float(v)) else float(v) for v in a.flat]
            present=[v for v in values if v is not None]
            grids.append(ScientificGrid(width=100,height=80,west=lons[0]-.5,east=lons[-1]+.5,south=9.5,north=89.5,
                longitudes=lons,latitudes=ys,values=values,minimum=min(present),maximum=max(present),missing_cells=values.count(None),
                resolution='NMME1° nativo; fixture de un chunk',sampling='Centros nativos; inversión lat y normalización lon',quality_mask='NaN original'))
            # Independent unpack of original chunk bytes, without using h5py's
            # decoded probability. Never hardcode a different month's number.
            probe=evidence['probes'][li-1];r,c=probe['native_row'],probe['native_column']
            chunk=data.id.get_chunk_info_by_coord((li,r,c,t))
            offset=int(np.ravel_multi_index((li%data.chunks[0],r%data.chunks[1],c%data.chunks[2],0),data.chunks))*4
            expected=struct.unpack('<f',source.read_at(chunk.byte_offset+offset,4))[0]
            cell=locate(grids[-1],probe['longitude'],probe['latitude'])
            assert grids[-1].values[cell[0]*100+cell[1]]==expected==probe['value']
    return raw,evidence,grids


@pytest.fixture
def store(tmp_path,monkeypatch,native):
    raw,evidence,grids=native
    sha=hashlib.sha256(raw).hexdigest();root=tmp_path/'products'
    for slot,g in enumerate(grids,1):
        year,month=(2026,10+slot) if slot<3 else (2027,1)
        start=datetime(year,month,1,tzinfo=timezone.utc)
        end=datetime(year+month//12,month%12+1,1,tzinfo=timezone.utc)
        p=ScientificProduct(id=f'd16-mhw-month-{slot}',source_id='D16',title='NOAA fixture',collection_id='NOAA PSL NMME_prob90_latest (with trend)',
            product_version='cycle=2026-10',variable='mhw_probability',unit='1 (probabilidad definida)',native_unit='fracción [0,1]',kind='forecast',representation='field',
            initialized_at=datetime(2026,10,1,tzinfo=timezone.utc),issued_at=None,valid_from=start,valid_to=end,retrieved_at=NOW-timedelta(hours=1),ingested_at=NOW,
            original_url=evidence['source_url'],license_url='https://psl.noaa.gov/marine-heatwaves/',attribution='NOAA PSL / NMME',checksum_sha256=sha,byte_size=len(raw),raw_file=f'shared/{sha}.json',
            coverage='Native scientific fixture chunk, not global',cadence_seconds=86400,method_version='psl-nmme-range-cycle-v1',limitation='Research only',grid=g,
            verification=Verification(method='h5py/struct original bytes',original_url=evidence['source_url'],checked_at=NOW,expected='match',actual='match',passed=True))
        assert publish(p,raw,'.json',root)=='stored'
        assert publish(p.model_copy(update={'ingested_at':NOW+timedelta(minutes=1)}),raw,'.json',root)=='unchanged'
    monkeypatch.setattr(q,'products_root',lambda:root)
    monkeypatch.setattr(q,'clock',lambda:NOW)
    monkeypatch.setattr(q,'_operations',lambda:EMPTY_OPS)
    return root


def test_scientific_fixture_point_mask_probability_and_dates(store,native):
    c=q.forecast_catalog(root=store,operations=EMPTY_OPS)
    f=next(e for e in c.forecasts if e.id==c.default_d16_id)
    assert f.valid_from==datetime(2026,12,1,tzinfo=timezone.utc)
    assert f.issued_at is None and f.first_seen_at==NOW and f.retrieved_at<NOW
    assert f.phenomenon_id=='F18' and f.reference_period=='1991–2020' and f.trend_treatment=='retained'
    point=q.forecast_point(f.id,-67,17,operations=EMPTY_OPS)
    assert point.probability==native[1]['probes'][1]['value'] and point.value is None and point.unit=='1'
    assert point.cell.longitude==-67 and point.cell.latitude==17
    assert point.cell.extent.west==-67.5 and point.cell.extent.south==16.5
    land=q.forecast_point(f.id,-75,10,operations=EMPTY_OPS)
    assert land.status=='no_coverage' and land.probability is None
    assert q.forecast_point(f.id,0,0,operations=EMPTY_OPS).status=='no_coverage'
    text=q.point_csv(point)
    assert str(point.probability) in text and 'None' not in text
    january=next(e for e in c.forecasts if e.valid_from.month==1)
    assert january.valid_to==datetime(2027,2,1,tzinfo=timezone.utc)


def test_actual_zero_vs_mask_and_deterministic_value(store,native):
    versions=q.retained(store);p=next(iter(versions.values()))
    g=p.grid
    index=next(i for i,v in enumerate(g.values) if v==0)
    f=q.forecast_field(q.identity(p),operations=EMPTY_OPS)
    point=q.point_from_field(f,g.longitudes[index%g.width],g.latitudes[index//g.width])
    assert point.probability==0 and point.status=='available'
    deterministic=f.model_copy(update={'forecast':f.forecast.model_copy(update={'result_type':'imported_value','unit':'mm'})})
    value=q.point_from_field(deterministic,point.requested_longitude,point.requested_latitude)
    assert value.value==0 and value.probability is None and value.unit=='mm'


def test_temporal_boundaries_with_controlled_clock(store):
    c=q.forecast_catalog(operations=EMPTY_OPS)
    november=next(f for f in c.forecasts if f.valid_from.month==11)
    assert november.temporal_state=='in_progress'
    dec=datetime(2026,12,1,tzinfo=timezone.utc)
    assert q.forecast_field(november.id,dec,operations=EMPTY_OPS).status=='expired'
    assert q.forecast_point(november.id,-67,17,dec,operations=EMPTY_OPS).probability is not None
    no_future=q.forecast_catalog(datetime(2027,3,1,tzinfo=timezone.utc),operations=EMPTY_OPS)
    assert no_future.future_fields==0 and no_future.archived_fields==3
    assert q.temporal_state(NOW,None,NOW)=='in_progress'
    assert q.temporal_state(NOW,None,NOW+timedelta(microseconds=1))=='expired'
    assert q.temporal_state(None,None,NOW)=='unknown'


def test_version_is_stable_across_slot_and_restart_and_keeps_error(store):
    versions=q.retained(store);key,p=next(iter(versions.items()))
    assert q.identity(p.model_copy(update={'id':'d16-mhw-month-9','retrieved_at':NOW+timedelta(hours=2)}))==key
    q._read.cache_clear()  # a restarted process, no in-memory scientific state
    assert q.retained(store)[key].ingested_at==p.ingested_at
    failed=EMPTY_OPS.model_copy(update={'jobs':{'d16-mhw-monthly':RefreshJob(status='failed',last_attempt_at=NOW,next_attempt_at=NOW+timedelta(minutes=15),last_success_at=NOW-timedelta(days=1),error='network controlled',kept_previous=True)}})
    field=q.forecast_field(key,operations=failed)
    assert field.grid==p.grid and field.forecast.update.error and field.forecast.issued_at is None
    assert q.forecast_field('a'*64,operations=EMPTY_OPS).status=='missing_input'
    (store/p.raw_file).unlink()
    assert q.forecast_field(key,operations=EMPTY_OPS).status=='missing_input'


def global_grid(values):
    return ScientificGrid(width=4,height=2,west=-180,east=180,south=-90,north=90,longitudes=[-180,-90,0,90],latitudes=[45,-45],values=values,
        minimum=min(v for v in values if v is not None),maximum=max(v for v in values if v is not None),missing_cells=values.count(None),resolution='controlled90°',sampling='test',quality_mask='null')


def test_edges_conventions_antimeridian_and_split_geometry():
    g=global_grid([.8,None,None,.9,0,None,None,None])
    assert locate(g,-180,45)==locate(g,180,45)==locate(g,540,45)==(0,0)
    assert locate(g,-135,0)==(0,1)  # tie east/north, masked: no fallback
    assert locate(g,0,90)==(0,2) and locate(g,0,-90)==(1,2)
    c=cell_at(g,0,0)
    assert c.extent.crosses_antimeridian and len(c.geometry.coordinates)==2
    for poly in c.geometry.coordinates:
        assert all(abs(a[0]-b[0])<=180 for a,b in zip(poly[0],poly[0][1:]))
    count,areas=components(g,.7)
    assert count==2 and len(areas)==1 and areas[0][0]==3 and areas[0][1]==2
    # A diagonal or a missing cell never connects components.
    g=global_grid([.8,None,None,None,None,.9,None,None])
    assert len(components(g,.7)[1])==2
    g=global_grid([float(np.float32(.7)),.7,None,None,None,None,None,None])
    assert components(g,.7)[0]==1  # no threshold rounding to Float32


def test_native_polar_centres_have_clipped_half_cell_support():
    g=global_grid([.1,.2,.3,.4,.5,.6,.7,.8]).model_copy(update={'height':3,'latitudes':[90,0,-90],'values':[.1,.2,.3,.4,.5,.6,.7,.8,None,None,None,None],'missing_cells':4})
    assert locate(g,0,89.75)==(0,2)
    assert locate(g,0,-89.75)==(2,2)
    north=cell_at(g,0,2);south=cell_at(g,2,2)
    assert (north.extent.south,north.extent.north)==(45,90)
    assert (south.extent.south,south.extent.north)==(-90,-45)


def test_highlights_same_grid_point_order_and_no_match_vs_no_data(store):
    key=q.forecast_catalog(operations=EMPTY_OPS).default_d16_id
    h=q.forecast_highlights(key,.7,3,operations=EMPTY_OPS)
    assert h.total_areas>=h.returned_areas and h.returned_areas<=3
    for a in h.areas:
        p=a.representative
        assert p.probability>=.7
        assert p==q.forecast_point(key,p.cell.longitude,p.cell.latitude,operations=EMPTY_OPS)
    assert [a.probability_max for a in h.areas]==sorted([a.probability_max for a in h.areas],reverse=True)
    # Max1 can be a genuine hit. A controlled all-zero field distinguishes no
    # match from an entirely masked input without changing any provider values.
    f=q.forecast_field(key,operations=EMPTY_OPS)
    zero=f.grid.model_copy(update={'values':[0.0]*len(f.grid.values),'missing_cells':0,'minimum':0.0,'maximum':0.0})
    from unittest.mock import patch
    with patch.object(q,'forecast_field',return_value=f.model_copy(update={'grid':zero})):
        empty=q.forecast_highlights(key,.7)
        assert empty.status=='available' and empty.total_areas==0 and 'filtro' in empty.reason
    masked=zero.model_copy(update={'values':[None]*len(zero.values),'missing_cells':len(zero.values),'minimum':None,'maximum':None})
    with patch.object(q,'forecast_field',return_value=f.model_copy(update={'grid':masked})):
        assert q.forecast_highlights(key,.7).status=='no_coverage'


def test_http_uses_the_same_version_and_input_validation(store,monkeypatch):
    from earth_echo.api.app import create_app
    client=TestClient(create_app())
    catalog=client.get('/v1/forecasts/catalog').json();key=catalog['default_d16_id']
    f=client.get(f'/v1/forecasts/fields/{key}').json()
    p=client.get(f'/v1/forecasts/fields/{key}/point?longitude=-67&latitude=17').json()
    row,col=p['cell']['row'],p['cell']['column']
    assert f['grid']['values'][row*f['grid']['width']+col]==p['probability']
    assert p['forecast']['id']==key and p['forecast']['issued_at'] is None
    assert client.get(f'/v1/forecasts/fields/{key}/point?longitude=0&latitude=91').status_code==422
    assert client.get(f'/v1/forecasts/fields/{key}/highlights?probability_filter=70').status_code==422
    assert client.get('/v1/forecasts/fields/'+'a'*64).json()['status']=='missing_input'


def test_swpc_running_predicted_window_and_unknown_issuance():
    from earth_echo.connectors.swpc_forecast import parse_predicted_kp
    rows=[{'observed':'predicted','time_tag':'2026-11-15T12:00:00','kp':0},
          {'observed':'observed','time_tag':'2026-11-15T15:00:00','kp':8},
          {'observed':'predicted','time_tag':'2026-11-15T15:00:00','kp':3}]
    at=NOW-timedelta(hours=1)
    parsed=parse_predicted_kp(rows,at)
    assert len(parsed)==2 and parsed[0]['kp']==0
    assert parsed[0]['retrieval_lead_hours']==-2 and parsed[0]['lead_time_hours'] is None
    ended=parse_predicted_kp(rows,NOW)
    assert len(ended)==1 and ended[0]['kp']==3
