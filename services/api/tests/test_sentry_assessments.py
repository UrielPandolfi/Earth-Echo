import json
from datetime import datetime, timezone
from urllib.error import URLError
import pytest
from earth_echo.connectors.cneos import fetch_sentry, impact_instant, parse_impactors, parse_removed, parse_sentry, probability_token
from earth_echo.queries.predictions import sentry_assessments, sentry_csv, sentry_object
from earth_echo.connectors import cneos


def summary_payload():
    return {'signature': {'version': '2.0', 'source': 'NASA/JPL Sentry Data API'}, 'count': 2, 'data': [
        {'des': '2011 TO', 'fullname': '(2011 TO)', 'id': 'bK11T00O', 'ip': '2.937e-06', 'ps_cum': '-6.15', 'ps_max': '-6.15', 'ts_max': '0', 'diameter': '0.018', 'h': '26.32', 'v_inf': '8.55', 'n_imp': 1, 'range': '2064-2064', 'last_obs': '2013-01-12'},
        {'des': 'SMALL', 'fullname': '(SMALL)', 'id': 'bSMALL', 'ip': '1.0e-04', 'ps_cum': '-5', 'ps_max': '-5', 'ts_max': '0', 'diameter': '0.01', 'h': '28', 'v_inf': '7', 'n_imp': 2, 'range': '2100-2101', 'last_obs': '2020-01-01'},
    ]}


def vi_payload():
    return {'signature': {'version': '2.0', 'source': 'NASA/JPL Sentry Data API'}, 'count': 3, 'data': [
        {'des': '2011 TO', 'fullname': '(2011 TO)', 'id': 'bK11T00O', 'date': '2064-09-27.39', 'ip': '2.937e-06', 'ps': '-6.15', 'ts': '0', 'energy': '1.983e-01', 'method': 'IOBS', 'sigma_vi': '2.7919'},
        {'des': 'SMALL', 'fullname': '(SMALL)', 'id': 'bSMALL', 'date': '2100-01-01.00', 'ip': '1.0e-05', 'ps': '-6', 'ts': '0', 'energy': '1e-03', 'method': 'IOBS', 'sigma_vi': '1'},
        {'des': 'SMALL', 'fullname': '(SMALL)', 'id': 'bSMALL', 'date': '2101-01-01.50', 'ip': '2.0e-05', 'ps': '-6', 'ts': '0', 'energy': '1e-03', 'method': 'IOBS', 'sigma_vi': '1'},
    ]}


def removed_payload():
    return {'signature': {'version': '2.0', 'source': 'NASA/JPL Sentry Data API'}, 'count': 2, 'data': [
        {'des': '2011 TO', 'removed': '2020-01-01 00:00:00'},
        {'des': 'GONE', 'removed': '2026-11-11 15:44:45'},
    ]}


def detail_for(designation):
    row = next(item for item in summary_payload()['data'] if item['des'] == designation)
    return json.dumps({'signature': summary_payload()['signature'], 'summary': row, 'data': [item for item in vi_payload()['data'] if item['des'] == designation]}).encode()


def test_scientific_notation_and_fractional_impact_date_stay_exact():
    text, value = probability_token('2.937e-06')
    assert text == '2.937e-06' and value == pytest.approx(2.937e-6) and value != 0
    instant = impact_instant('2064-09-27.39')
    assert instant == datetime(2064, 9, 27, 9, 21, 36, tzinfo=timezone.utc)
    with pytest.raises(ValueError):
        probability_token('1.1')
    from earth_echo.connectors.cneos import optional_number
    assert optional_number('NaN') is None
    broken = summary_payload(); broken['signature']['version'] = '1.0'
    with pytest.raises(ValueError):
        parse_sentry(broken)


def test_cumulative_probability_is_not_replaced_by_a_scenario_sum(tmp_path, monkeypatch):
    monkeypatch.setattr('earth_echo.storage.products.products_root', lambda: tmp_path)
    now = datetime(2026, 11, 15, tzinfo=timezone.utc)
    bodies = {
        'summary': json.dumps(summary_payload()).encode(),
        'detail': detail_for('SMALL'),
        'vi': json.dumps(vi_payload()).encode(),
        'removed': json.dumps(removed_payload()).encode(),
    }

    def fake_download(url, **kwargs):
        assert kwargs['timeout'] >= 60
        if 'all=1' in url: return bodies['vi'], {}
        if 'removed=1' in url: return bodies['removed'], {}
        if 'des=' in url: return bodies['detail'], {}
        return bodies['summary'], {}

    monkeypatch.setattr(cneos, 'download', fake_download)
    assert fetch_sentry(now) == 'stored'
    assert fetch_sentry(now) == 'unchanged'
    # The second call consumes no network because the first already returned unchanged only if download is not called.
    view = sentry_assessments(root=tmp_path)
    small = next(item for item in view.objects if item.designation == 'SMALL')
    detail = sentry_object('SMALL', root=tmp_path)
    assert small.cumulative_probability_text == '1.0e-04'
    assert small.cumulative_probability == pytest.approx(1e-4)
    assert [item.probability_text for item in detail.scenarios] == ['2.0e-05', '1.0e-05']
    assert abs(sum(item.probability for item in detail.scenarios) - small.cumulative_probability) > 1e-6
    assert 'GONE' in {item.designation for item in view.removed}
    assert all(item.designation != '2011 TO' for item in view.removed)
    assert sentry_object('2011 TO', root=tmp_path).scenarios[0].date_text == '2064-09-27.39'
    assert sentry_object('MISSING', root=tmp_path).status == 'not_listed'
    csv = sentry_csv(view, detail)
    assert '2.0e-05' in csv and '2101-01-01.50' in csv
    assert '2.937e-06' in sentry_csv(view)


def test_failed_download_does_not_publish(monkeypatch):
    def boom(*args, **kwargs):
        raise URLError('sentry down')
    monkeypatch.setattr(cneos, 'download', boom)
    with pytest.raises(URLError):
        fetch_sentry(datetime.now(timezone.utc))


def test_duplicate_and_removed_rows_are_rejected():
    duplicated = summary_payload(); duplicated['data'][1]['des'] = '2011 TO'; duplicated['count'] = 2
    with pytest.raises(ValueError):
        parse_sentry(duplicated)
    with pytest.raises(ValueError):
        parse_removed({'signature': removed_payload()['signature'], 'count': 1, 'data': [{'des': 'X'}]})
    assert parse_impactors(vi_payload())[0]['probability_text'] == '2.937e-06'


def test_retained_sentry_matches_two_official_object_details():
    view = sentry_assessments()
    if view.status != 'available':
        pytest.skip('No retained Sentry summary')
    impactors = sentry_object('2010 RF12')
    older = sentry_object('2011 TO')
    removed = next(item for item in view.removed if item.designation == '2026 OA3')
    assert impactors.cumulative_probability_text == '0.102637259069'
    assert impactors.scenarios_status == 'available'
    assert len(impactors.scenarios) == 70
    assert any(item.date_text == '2122-09-06.46' and item.probability_text == '4.112e-07' for item in impactors.scenarios)
    assert older.cumulative_probability_text == '2.937e-06'
    assert [(item.date_text, item.probability_text) for item in older.scenarios] == [('2064-09-27.39', '2.937e-06')]
    assert removed.removed_at == '2026-11-11 15:44:45' and removed.cumulative_probability is None
    assert '0.102637259069' in sentry_csv(view)
