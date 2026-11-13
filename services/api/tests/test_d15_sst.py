from datetime import datetime, timezone
from pathlib import Path

import pytest

from earth_echo.connectors.crw_sst import CrwError, cell_value, decode_subset, ensure_netcdf
from earth_echo.ingest.d15_sst import ingest_file, sample_file
from earth_echo.science.sst import celsius_or_missing, mean_present
from earth_echo.storage.sst_store import SstStore


def test_known_cell_matches_the_provider_sample() -> None:
    decoded = decode_subset(sample_file())
    moment = datetime(2026, 11, 11, 12, tzinfo=timezone.utc)
    assert cell_value(decoded, moment, 16.525, -67.175) == 29.73


def test_fill_value_is_not_a_temperature() -> None:
    assert celsius_or_missing(-327.68, fill_value=-327.68, valid_min=-2, valid_max=50) is None
    assert celsius_or_missing(29.73, fill_value=-327.68, valid_min=-2, valid_max=50) == 29.73
    assert celsius_or_missing(297.3, fill_value=-327.68, valid_min=-2, valid_max=50, scale_factor=0.1) == pytest.approx(29.73)
    mean, valid, missing = mean_present([29.73, None, 29.71])
    assert mean == pytest.approx(29.72)
    assert (valid, missing) == (2, 1)


def test_html_response_is_rejected() -> None:
    with pytest.raises(CrwError):
        ensure_netcdf("text/html", b"<html>login</html>")


def test_ingest_is_idempotent_and_keeps_a_revision(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store = SstStore(tmp_path / "store")
    first = ingest_file(sample_file(), store, ingested_at=datetime(2026, 11, 13, tzinfo=timezone.utc))
    second = ingest_file(sample_file(), store, ingested_at=datetime(2026, 11, 13, tzinfo=timezone.utc))
    assert first["status"] == "stored"
    assert second == {"status": "unchanged", "revision": 1, "observations": 4}
    monkeypatch.setattr("earth_echo.ingest.d15_sst.file_sha256", lambda _path: "b" * 64)
    third = ingest_file(sample_file(), store, ingested_at=datetime(2026, 11, 13, 1, tzinfo=timezone.utc))
    assert third["status"] == "stored"
    assert third["revision"] == 2
    current = store.current_observations()
    assert len(current) == 4
    assert {item.id[-2:] for item in current} == {"r2"}
    assert store.asset("d15-coraltemp-v3.1-caribe-r1") is not None
    assert current[0].measurement.status == "present"
    assert current[0].measurement.value is not None
    assert 29 < current[0].measurement.value < 30
    assert current[0].data_mode == "real"
    assert current[0].phenomenon_id is None
