import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from earth_echo.connectors.aftershocks import describe_oaf
from earth_echo.paths import repo_root
from earth_echo.queries.predictions import aftershock_csv, aftershock_forecasts
from earth_echo.storage.products import products_root, read_product

SAMPLE = repo_root() / "data/samples/integrations/usgs-oaf-us7000txrk.json"


def test_official_sample_keeps_probability_count_and_refuses_an_unlabeled_circle():
    payload = json.loads(SAMPLE.read_text(encoding="utf-8"))
    described = describe_oaf(payload, "us7000txrk", datetime(2026, 11, 13, tzinfo=timezone.utc))
    assert described["region_radius"] == 10
    assert described["magnitude"] == 4.5
    assert (described["longitude"], described["latitude"]) == (-129.6205, 44.4539)
    day = described["windows"][0]
    assert day["label"] == "1 Day"
    assert [item["magnitude"] for item in day["bins"]] == [3, 4, 5, 6, 7]
    assert day["bins"][0]["probability"] == pytest.approx(0.03126)
    assert day["bins"][0]["median_count"] == 0
    assert (day["bins"][0]["p95_minimum"], day["bins"][0]["p95_maximum"]) == (0, 1)
    later = describe_oaf(payload, "us7000txrk", datetime(2030, 1, 1, tzinfo=timezone.utc))
    assert all(window["temporal_state"] == "expired" for window in later["windows"])


def test_retained_event_matches_its_own_forecast_file():
    view = aftershock_forecasts(datetime.now(timezone.utc))
    assert view.status == "available"
    event = view.events[0]
    assert event.event_id == "us7000txrk"
    assert event.geometry == "epicenter_only"
    assert event.region_radius_unit is None
    assert event.depth_km is None and event.origin_time is None
    product = read_product("d22-oaf-recent")
    raw = json.loads((products_root() / product.raw_file).read_text(encoding="utf-8"))
    day = next(window for window in event.windows if window.label == "1 Day")
    source = next(window for window in raw["forecast"] if window["label"] == "1 Day")
    assert day.bins[0].probability == pytest.approx(source["bins"][0]["probability"])
    assert day.bins[0].median_count == pytest.approx(source["bins"][0]["median"])
    assert aftershock_forecasts(datetime.now(timezone.utc)).model_dump()["events"][0]["checksum_sha256"] == event.checksum_sha256
    assert "us7000txrk" in aftershock_csv(view)


def test_missing_forecast_does_not_invent_aftershocks(tmp_path):
    view = aftershock_forecasts(datetime(2026, 11, 15, tzinfo=timezone.utc), tmp_path, operations=None)
    assert view.status == "missing_input"
    assert view.events == []
    assert aftershock_csv(view).count("\n") == 1
