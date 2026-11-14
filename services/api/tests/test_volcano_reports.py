from pathlib import Path
from datetime import datetime,timezone
import pytest
from earth_echo.connectors.volcano_reports import decode_reports

ROOT=Path(__file__).resolve().parents[3]/'data/samples/integrations'


def test_authentic_report_issue_is_not_observation_or_forecast_time():
    rss=(ROOT/'gvp-weekly.xml').read_bytes();cap=(ROOT/'gvp-weekly-cap.xml').read_bytes()
    samples,sent,channel,periods,edition=decode_reports(rss,cap)
    assert len(samples)==2 and edition=='GVP-Weekly-20261015'
    assert periods==['8 October-14 October 2026']
    assert sent==datetime(2026,10,15,7,11,8,tzinfo=timezone.utc)
    assert (channel-sent).total_seconds()==3600
    assert samples[0].latitude==-6.1009 and samples[0].longitude==105.4233
    assert samples[0].category=='New Eruptive Activity'
    assert samples[0].value is None and samples[0].probability is None
    assert samples[0].attributes['CAP_urgency']=='Unknown'
    assert 'no fecha de erupción' in samples[0].attributes['fecha_registro']
    with pytest.raises(ValueError,match='point/location'):
        decode_reports(rss,cap.replace(b'-6.1009,105.4233',b'-6.1009,104.4233'))
    with pytest.raises(ValueError,match='period or volcano'):
        decode_reports(rss,cap.replace(b'8 October-14 October',b'9 October-14 October'))
