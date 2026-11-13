import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from earth_echo.catalog.capabilities import capability_matrix
from earth_echo.catalog.load import load_catalog
from earth_echo.connectors.public_feeds import FeedSchemaError, parse_planetary_kp, parse_usgs_events
from earth_echo.ingest import feeds
from earth_echo.paths import repo_root


def test_matrix_lists_every_phenomenon_without_a_connected_forecast() -> None:
    matrix = capability_matrix()
    catalog_ids = [item.id for item in load_catalog().modules]
    assert matrix.total == len(catalog_ids) == 31
    assert [item.id for item in matrix.phenomena] == catalog_ids
    by_id = {item.id: item for item in matrix.phenomena}
    rain = {item.kind: item.status for item in by_id["F01"].outputs}
    assert rain["observation"] == "blocked"
    assert rain["forecast"] != "connected"
    coral = {item.kind: item for item in by_id["F19"].outputs}
    assert coral["observation"].status == "partial"
    assert "blanqueamiento" in coral["observation"].detail
    assert by_id["F31"].outputs[3].status == "research"
    assert all(
        output.status != "connected"
        for item in matrix.phenomena
        for output in item.outputs
        if output.kind == "forecast"
    )


def test_public_samples_parse_without_inventing_values() -> None:
    root = repo_root()
    events = parse_usgs_events(json.loads((root / "data/samples/d21-usgs/recent-m5.geojson").read_text(encoding="utf-8")))
    assert events
    assert all(item["magnitude"] >= 5 for item in events)
    assert events[0]["id"]
    rows = parse_planetary_kp(json.loads((root / "data/samples/d28-swpc/planetary-k-index.json").read_text(encoding="utf-8")))
    assert rows[-1]["kp"] == 0.33
    with pytest.raises(FeedSchemaError):
        parse_usgs_events({"type": "FeatureCollection"})


def test_failed_refresh_keeps_the_previous_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(feeds, "feeds_dir", lambda: tmp_path)
    monkeypatch.setattr(feeds, "repo_root", lambda: repo_root())
    feeds.seed_archived_feeds(datetime(2026, 11, 13, tzinfo=timezone.utc))
    before = (tmp_path / "d21-events.json").read_text(encoding="utf-8")

    def explode() -> bytes:
        raise TimeoutError("red")

    monkeypatch.setattr(feeds, "_get", lambda _url: explode())
    moment = datetime(2026, 11, 13, 2, tzinfo=timezone.utc)
    results = feeds.run_due(moment, force=True)
    assert {item["error_class"] for item in results} == {"network"}
    assert (tmp_path / "d21-events.json").read_text(encoding="utf-8") == before
    stamp = moment.strftime("%Y-%m-%dT%H:%M:%SZ")
    (tmp_path / "jobs.json").write_text(
        json.dumps({"jobs": {"d21-events": {"finished_at": stamp}, "d28-kp": {"finished_at": stamp}}}),
        encoding="utf-8",
    )
    skipped = feeds.run_due(moment + timedelta(minutes=10), force=False)
    assert {item["status"] for item in skipped} == {"skipped"}
