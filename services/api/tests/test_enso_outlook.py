from datetime import datetime,timezone
from pathlib import Path
from urllib.error import URLError
import io,json,zipfile
import pytest
import earth_echo.connectors.enso_outlook as module
from earth_echo.storage.products import publish,read_product

FIXTURE=Path(__file__).resolve().parents[3]/'data/samples/integrations/cpc-roni-outlook-202611.zip'
NOW=datetime(2026,11,14,tzinfo=timezone.utc)


@pytest.fixture(scope='module')
def files():
    with zipfile.ZipFile(FIXTURE) as z:
        return {n:z.read(n) for n in json.loads(z.read('manifest.json'))['assets']}


def test_real_cpc_roni_windows_probabilities_and_quantiles(files):
    products,raw=module.products_from_files(files,NOW)
    phase,strength,quantiles=products
    assert [len(p.samples) for p in products]==[27,81,63]
    assert all(p.kind=='forecast' and p.representation=='table' and p.calculation is None for p in products)
    assert all(p.issued_at is None and p.initialized_at is None and p.observed_at is None for p in products)
    assert phase.valid_from.isoformat()=='2026-10-01T00:00:00+00:00'
    assert phase.valid_to.isoformat()=='2027-09-01T00:00:00+00:00'
    assert {p.checksum_sha256 for p in products}=={phase.checksum_sha256}
    assert all(s.latitude is None and s.longitude is None for p in products for s in p.samples)
    fma=[s for s in phase.samples if s.attributes['season']=='FMA 2027']
    assert [s.value for s in fma]==[0,2,98] and [s.probability for s in fma]==[0,.02,.98]
    assert fma[2].time.isoformat()=='2027-02-01T00:00:00+00:00'
    assert fma[2].valid_to.isoformat()=='2027-05-01T00:00:00+00:00'
    assert '1991–2020' in fma[2].probability_definition and 'RONI' in fma[2].probability_definition
    assert any(s.attributes['season']=='NDJ 2026–2027' for s in phase.samples)
    djf=[s for s in strength.samples if s.attributes['season']=='DJF 2026–2027']
    assert djf[-1].value==79 and djf[-1].probability==.79
    assert [s.value for s in quantiles.samples[:7]]==[2.19,2.31,2.38,2.5,2.63,2.7,2.82]
    assert quantiles.samples[-4].value==-.25  # JJA median, no invented event probability.
    assert all(s.probability is None and s.probability_definition is None for s in quantiles.samples)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:assert all(z.read(n)==b for n,b in files.items())


def test_mixed_issues_inconsistent_totals_thresholds_and_quantiles_rejected(files):
    altered=dict(files);altered['strengths.html']=altered['strengths.html'].replace(b'Issued November 2026',b'Issued October 2026')
    with pytest.raises(ValueError,match='Mixed CPC'):module.products_from_files(altered,NOW)
    altered=dict(files);altered['probabilities.html']=altered['probabilities.html'].replace(b'<td>98</td>',b'<td>97</td>')
    with pytest.raises(ValueError,match='total100'):module.products_from_files(altered,NOW)
    altered=dict(files);altered['outlook.html']=altered['outlook.html'].replace(b'<td>2.19</td>',b'<td>3.19</td>')
    with pytest.raises(ValueError,match='monotonic'):module.products_from_files(altered,NOW)
    altered=dict(files);altered['definition.html']=altered['definition.html'].replace(b'ERSSTv6',b'ERSSTv7')
    with pytest.raises(ValueError,match='ERSST version'):module.products_from_files(altered,NOW)
    # Independent tables must agree even if a changed row still totals100.
    altered=dict(files);altered['probabilities.html']=altered['probabilities.html'].replace(b'<td>0</td><td>2</td><td>98</td>',b'<td>0</td><td>3</td><td>97</td>')
    with pytest.raises(ValueError,match='strength bins'):module.products_from_files(altered,NOW)


def test_authentic_ingestion_shared_asset_idempotence_outage_and_recovery(files,tmp_path,monkeypatch):
    offline=False
    def download(url,**kwargs):
        if offline:raise URLError('controlled outage')
        return files['definition.html' if url==module.BASE else url.rstrip('/').split('/')[-1]+'.html'],{}
    monkeypatch.setattr(module,'download',download)
    monkeypatch.setattr(module,'publish',lambda p,raw,suffix:publish(p,raw,suffix,tmp_path))
    assert module.fetch_enso_outlook(NOW)=='stored'
    before=[read_product('d48-roni-'+k,tmp_path) for k in ('probabilities','strengths','outlook','history')]
    assert module.fetch_enso_outlook(NOW)=='unchanged'
    assert len(list(tmp_path.glob('shared/*.zip')))==1 and len(list(tmp_path.glob('*/revisions/*.json')))==4
    offline=True
    with pytest.raises(URLError):module.fetch_enso_outlook(NOW)
    assert [read_product(p.id,tmp_path) for p in before]==before
    offline=False
    assert module.fetch_enso_outlook(NOW)=='unchanged'


def test_bounded_forecast_retention_keeps_24_revisions_without_removing_shared_asset(files,tmp_path):
    products,raw=module.products_from_files(files,NOW);phase,strength,_=products
    publish(strength,raw,'.zip',tmp_path)
    for i in range(26):
        publish(phase.model_copy(update={'product_version':phase.product_version+f' / retention exercise{i}'}),raw,'.zip',tmp_path)
    assert len(list((tmp_path/phase.id/'revisions').glob('*.json')))==24
    assert len(list((tmp_path/strength.id/'revisions').glob('*.json')))==1
    assert read_product(strength.id,tmp_path) is not None
    assert len(list(tmp_path.glob('shared/*.zip')))==1
