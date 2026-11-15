import json
import pytest
from earth_echo.assistant.reply import AssistantContext,ask


class ForbiddenProvider:
    provider_id='mock'
    model_name='forbidden-science-model'
    def complete(self,*args):pytest.fail('Scientific summaries must not call a text model')


def test_anomaly_summary_distinguishes_historical_candidates_and_daily_field():
    reply=ask('¿Qué anomalías SST están disponibles?',AssistantContext(data_mode='real'),ForbiddenProvider())
    assert reply.provider=='not_used' and reply.answer_kind=='tool_template'
    assert reply.tools[0]['flagged_months']==9 and reply.tools[0]['assessed_months']==48
    assert 'No son alertas actuales' in reply.text and '1971–2000' in reply.text
    assert '2014–2021' in reply.text and reply.tools[0]['probability'] is None
    assert reply.actions[0].section=='tendencias'


def test_associations_keep_uncertainty_and_never_become_causal_model_text():
    reply=ask('¿Cuál es la relación entre AMOC y SST?',AssistantContext(data_mode='real'),ForbiddenProvider())
    assert reply.provider=='not_used' and reply.tools[0]['tool']=='associations'
    assert '0.190' in reply.text and '0.244' in reply.text
    assert 'No demuestran causalidad ni habilidad predictiva' in reply.text
    assert all(i['low']<0<i['high'] for p in reply.tools[0]['pairs'] for i in p['intervals'])
    assert reply.tools[0]['causal_attribution']=='not_identified'


@pytest.mark.parametrize('question',['¿Qué anomalías hay?','¿Qué conexión hay entre AMOC y SST?'])
def test_replay_never_receives_full_historical_analysis_or_calls_a_model(question):
    reply=ask(question,AssistantContext(data_mode='real',replay_issue='2022-01',replay_revealed=False),ForbiddenProvider())
    assert reply.provider=='not_used' and reply.tools==[]
    assert 'corte temporal' in reply.text and 'posteriores' in reply.text
    assert '2025' not in json.dumps(reply.tools)


def test_amoc_trend_uses_transport_units_and_does_not_predict_collapse():
    reply=ask('¿Cuál es la tendencia de AMOC?',AssistantContext(data_mode='real'),ForbiddenProvider())
    assert reply.tools[0]['tool']=='amoc_trend' and 'Sv/década' in reply.text
    assert '-0.842' in reply.text and '26,5N' in reply.text
    future=ask('¿Cuándo será el colapso de AMOC?',AssistantContext(data_mode='real'),ForbiddenProvider())
    assert 'No hay fecha o probabilidad operativa' in future.text
    assert future.provider=='not_used'


def test_quake_summary_uses_real_query_scope_and_missing_is_not_zero(monkeypatch):
    from earth_echo.assistant import tools
    base={'tool':'quakes','count':3,'available':True,'query_note':'Consulta real M≥4,5, últimos7días, límite500.','latest':'2026-11-15T00:00:00Z','forecast':'absent'}
    monkeypatch.setattr(tools,'quake_summary',lambda:base)
    reply=ask('¿Cuántos sismos hay?',AssistantContext(data_mode='real'),None)
    assert 'M≥4,5' in reply.text and 'magnitud 5 o más' not in reply.text
    monkeypatch.setattr(tools,'quake_summary',lambda:{**base,'available':False,'count':0})
    reply=ask('¿Cuántos sismos hay?',AssistantContext(data_mode='real'),None)
    assert 'No hay una instantánea' in reply.text and 'Hay 0' not in reply.text
