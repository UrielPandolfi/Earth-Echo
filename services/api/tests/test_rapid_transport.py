from pathlib import Path
from datetime import datetime,timezone
import io
import h5py
import pytest
from earth_echo.connectors.rapid_transport import decode_transports,verify_published_mean

ROOT=Path(__file__).resolve().parents[3]/'data/samples/integrations'


def test_authentic_monthly_transport_units_time_and_published_summary():
    series,attrs=decode_transports((ROOT/'rapid-monthly.h5').read_bytes())
    assert attrs['Dataset_version']=='v2024-2'
    amoc=series['amoc_depth_1m']
    assert len(amoc)==248
    assert amoc[0].time==datetime(2004,4,15,tzinfo=timezone.utc)
    assert amoc[-1].time==datetime(2024,11,15,tzinfo=timezone.utc)
    assert amoc[0].value==pytest.approx(16.932971534083368)
    assert amoc[-1].value==pytest.approx(15.001998306111425)
    assert amoc[0].longitude is None and amoc[0].probability is None
    assert series['heat_trans_1m'][0].attributes['Units_nativo']=='PW'
    assert series['frwa_trans_1m'][0].value==pytest.approx(-1.4277079274153444)
    reference=(ROOT/'rapid-published-statistics.txt').read_bytes()
    expected,actual=verify_published_mean(amoc,reference)
    assert expected==(17.1,3.2) and actual[0]==pytest.approx(17.099724647003963)
    with pytest.raises(ValueError,match='mean/sample SD disagrees'):
        verify_published_mean(amoc,reference.replace(b'17.1',b'18.1'))


def test_native_fill_stays_missing_and_unit_changes_require_review():
    raw=io.BytesIO((ROOT/'rapid-monthly.h5').read_bytes())
    with h5py.File(raw,'r+') as f:f['amoc_depth_1m'][5]=float('nan')
    series,_=decode_transports(raw.getvalue())
    assert series['amoc_depth_1m'][5].value is None
    assert series['amoc_depth_1m'][4].value is not None
    with h5py.File(raw,'r+') as f:f['amoc_depth_1m'].attrs['Units']='m3/s'
    with pytest.raises(ValueError,match='units/dimensions'):
        decode_transports(raw.getvalue())
