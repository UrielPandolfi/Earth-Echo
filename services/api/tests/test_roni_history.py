from datetime import datetime,timezone
from pathlib import Path
import zipfile
import pytest
from earth_echo.connectors.roni_history import decode_history,history_from_shared_archive,KEY
from earth_echo.connectors.enso_outlook import products_from_files
from earth_echo.storage.products import publish,read_product

FIXTURE=Path(__file__).resolve().parents[3]/'data/samples/integrations/cpc-roni-outlook-202611.zip'
NOW=datetime(2026,11,14,tzinfo=timezone.utc)


@pytest.fixture(scope='module')
def originals():
    with zipfile.ZipFile(FIXTURE) as z:return z.read('definition.html'),{n:z.read(n) for n in ('probabilities.html','strengths.html','outlook.html','definition.html')}


def test_authentic_visible_v6_last_year_implicit_row_close_and_missing(originals):
    raw,_=originals;samples,rows=decode_history(raw,NOW)
    assert len(samples)==924 and len(rows)==77
    assert samples[0].id=='1950-DJF' and samples[0].value==-1.2
    assert samples[0].time.isoformat()=='1949-12-01T00:00:00+00:00'
    assert samples[0].valid_to.isoformat()=='1950-03-01T00:00:00+00:00'
    assert samples[-4].id=='2026-ASO' and samples[-4].value==2.0
    assert [s.id for s in samples[-3:]]==['2026-SON','2026-OND','2026-NDJ']
    assert all(s.value is None for s in samples[-3:])
    assert sum(s.value is not None for s in samples)==921
    assert next(s for s in samples if s.id=='2026-MAM').value==0  # Published zero preserved.
    assert all(s.probability is None and s.longitude is None for s in samples)


def test_wrong_ersst_definition_year_sequence_or_future_values_rejected(originals):
    raw,_=originals
    with pytest.raises(ValueError,match='definition'):decode_history(raw.replace(b'ERSSTv6',b'ERSSTv7'),NOW)
    with pytest.raises(ValueError,match='years'):decode_history(raw.replace(b'<p>2025</p>',b'<p>2024</p>'),NOW)
    with pytest.raises(ValueError,match='future'):decode_history(raw,datetime(2026,10,1,tzinfo=timezone.utc))


def test_shared_asset_retained_without_another_scientific_download(originals,tmp_path):
    raw,files=originals;forecasts,archive=products_from_files(files,NOW)
    parent=forecasts[0];publish(parent,archive,'.zip',tmp_path)
    history=history_from_shared_archive(raw,parent,NOW)
    assert history.kind=='historical' and history.representation=='time_series'
    assert history.observed_at.isoformat()=='2026-08-01T00:00:00+00:00'
    assert history.observation_end.isoformat()=='2026-11-01T00:00:00+00:00'
    assert history.issued_at is None and history.valid_from is None and history.valid_to is None
    assert history.raw_file==parent.raw_file and history.checksum_sha256==parent.checksum_sha256
    assert history.scientific_checksum_sha256!=parent.scientific_checksum_sha256
    assert publish(history,archive,'.zip',tmp_path)=='stored'
    assert publish(history,archive,'.zip',tmp_path)=='unchanged'
    assert read_product(KEY,tmp_path).samples[-1].value is None
    assert len(list(tmp_path.glob('shared/*.zip')))==1
