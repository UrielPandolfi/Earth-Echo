import json
from pathlib import Path
import pytest
import earth_echo.connectors.open_meteo as module


def test_weighted_rolling_limits_count_locations_retries_and_old_reservations():
    entries=[{'at':1000,'weight':180},{'at':1001,'weight':180}]
    assert module.rate_wait(entries,1002,180)==58
    assert module.rate_wait(entries,1060,180)==0
    assert module.rate_wait([{'at':1000+i,'weight':500} for i in range(9)],1600,180)==3000
    assert module.rate_wait([{'at':1000+i,'weight':500} for i in range(18)],5000,180)==82400
    with pytest.raises(ValueError,match='Split'):module.rate_wait([],1000,501)


def test_budget_is_persistent_before_io_and_released_by_time(tmp_path,monkeypatch):
    import earth_echo.paths
    monkeypatch.setattr(earth_echo.paths,'repo_root',lambda:tmp_path)
    clock=[1000.0];waits=[]
    monkeypatch.setattr(module.time,'time',lambda:clock[0])
    def sleep(seconds):waits.append(seconds);clock[0]+=seconds
    monkeypatch.setattr(module.time,'sleep',sleep)
    module.reserve_calls(locations=90,variables=4,hours=1)
    module.reserve_calls(locations=90,variables=4,hours=1)
    path=tmp_path/'data/real/refresh/open-meteo-budget.json'
    assert [e['weight'] for e in json.loads(path.read_bytes())['reservations']]==[180,180]
    # A second worker/process reads the same reservations, including failed I/O.
    module.reserve_calls(locations=90,variables=4,hours=1)
    assert waits==[60] and clock[0]==1060
    assert len(json.loads(path.read_bytes())['reservations'])==3
    path.write_text(json.dumps({'reservations':[{'at':clock[0]+120,'weight':1}]}))
    with pytest.raises(ValueError,match='Clock moved backwards'):
        module.reserve_calls(locations=1,variables=1,hours=1)
