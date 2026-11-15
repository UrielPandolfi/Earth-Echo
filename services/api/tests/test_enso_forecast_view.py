import csv
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from earth_echo.connectors.enso_outlook import products_from_files
from earth_echo.connectors.roni_history import history_from_shared_archive
from earth_echo.queries.predictions import enso_csv, enso_outlook
from earth_echo.storage.products import publish

FIXTURE = Path(__file__).resolve().parents[3] / "data/samples/integrations/cpc-roni-outlook-202611.zip"
NOW = datetime(2026, 11, 14, tzinfo=timezone.utc)


def _files():
    with zipfile.ZipFile(FIXTURE) as archive:
        return {name: archive.read(name) for name in json.loads(archive.read("manifest.json"))["assets"]}


def _publish(tmp_path):
    files = _files()
    products, raw = products_from_files(files, NOW)
    products.append(history_from_shared_archive(files["definition.html"], products[0], NOW))
    for product in products:
        publish(product, raw, ".zip", tmp_path)
    return products


def test_fixture_probabilities_keep_official_order_and_year_boundary(tmp_path):
    _publish(tmp_path)
    view = enso_outlook(NOW, tmp_path, operations=None)
    assert view.status == "available"
    assert view.issued_at is None
    assert [phase.season for phase in view.phases] == [phase.season for phase in sorted(view.phases, key=lambda item: item.valid_from)]
    assert any(phase.season.startswith("NDJ") and phase.valid_to.year == phase.valid_from.year + 1 for phase in view.phases)
    fma = next(phase for phase in view.phases if phase.season == "FMA 2027")
    assert (fma.la_nina_percent, fma.neutral_percent, fma.el_nino_percent) == (0, 2, 98)
    assert fma.roni_p50_c is not None
    assert view.region.extent.west == -170 and view.region.extent.east == -120
    assert view.observation is not None
    assert "cinco temporadas" in view.observation.note
    again = enso_outlook(NOW, tmp_path, operations=None)
    assert again.model_dump() == view.model_dump()
    rows = list(csv.DictReader(io.StringIO(enso_csv(view))))
    assert rows[view.phases.index(fma)]["el_nino_percent"] == "98"
    assert rows[view.phases.index(fma)]["neutral_percent"] == "2"


def test_retained_publication_stays_complete_and_ordered():
    view = enso_outlook(datetime.now(timezone.utc))
    assert view.status == "available"
    assert view.phases
    assert [phase.valid_from for phase in view.phases] == sorted(phase.valid_from for phase in view.phases)
    assert all(phase.la_nina_percent + phase.neutral_percent + phase.el_nino_percent == 100 for phase in view.phases)
    if view.edition == "2026-11":
        fma = next(phase for phase in view.phases if phase.season == "FMA 2027")
        assert (fma.la_nina_percent, fma.neutral_percent, fma.el_nino_percent) == (0, 2, 98)


def test_missing_publication_does_not_invent_probabilities(tmp_path):
    view = enso_outlook(NOW, tmp_path, operations=None)
    assert view.status == "missing_input"
    assert view.phases == []
    assert "No se inventaron" in view.reason
    assert enso_csv(view).count("\n") == 1
