import json
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from earth_echo.api.app import create_app
from earth_echo.catalog.load import load_catalog
from earth_echo.queries.real_sst import freshness_for
from earth_echo.settings import get_settings


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.delenv("HOST", raising=False)
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.delenv("EARTH_ECHO_MAX_BODY_BYTES", raising=False)
    get_settings.cache_clear()
    return TestClient(create_app())


def test_health_is_only_the_process(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"] == ["process"]
    assert body["time"].endswith("Z")
    assert "providers" not in body
    assert "healthy" not in json.dumps(body).lower()


def test_providers_are_not_probed(client: TestClient) -> None:
    body = client.get("/providers").json()
    assert body["live_probe"] == "not_performed"
    assert {item["source_id"] for item in body["providers"]} == {"D01", "D02", "D15", "D21"}
    by_id = {item["source_id"]: item for item in body["providers"]}
    assert by_id["D01"]["integration_status"] == "credential_required"
    assert by_id["D02"]["integration_status"] == "credential_required"
    assert by_id["D15"]["integration_status"] == "connected"
    assert by_id["D21"]["integration_status"] == "sample_retrieved"
    assert all(item["live_status"] == "not_probed" for item in body["providers"])


def test_catalog_counts_come_from_the_file(client: TestClient) -> None:
    document = load_catalog()
    sources = client.get("/catalog/sources", params={"limit": 2})
    assert sources.status_code == 200
    body = sources.json()
    assert body["returned"] == 2
    assert body["total"] == len(document.sources)
    assert len(body["sources"]) == 2
    listed = client.get("/catalog/sources").json()["sources"]
    by_id = {item["id"]: item["integration_status"] for item in listed}
    assert by_id["D01"] == "credential_required"
    assert by_id["D02"] == "credential_required"
    assert by_id["D15"] == "connected"
    assert by_id["D21"] == "sample_retrieved"
    phenomena = client.get("/catalog/phenomena").json()
    assert phenomena["total"] == len(document.modules)
    assert all(item["capability_status"] == "specified" for item in phenomena["phenomena"])
    missing = client.get("/catalog/sources/D99")
    assert missing.status_code == 404


def test_signal_modes_stay_separate(client: TestClient) -> None:
    real = client.get("/signals", params={"phenomenon_id": "F11", "mode": "real"})
    demo = client.get("/signals", params={"phenomenon_id": "F11", "mode": "demo"})
    assert real.status_code == 200
    assert real.json()["status"] == "unavailable"
    assert real.json()["unavailable"]["reason_code"] == "credential_required"
    assert "-0.04" not in real.text
    assert demo.json()["signals"][0]["data_mode"] == "demo"
    assert client.get("/signals", params={"phenomenon_id": "F99", "mode": "real"}).status_code == 404
    assert client.get("/signals", params={"phenomenon_id": "lluvia", "mode": "real"}).status_code == 422


def test_real_sst_is_traceable_and_imer_stays_blocked(client: TestClient) -> None:
    blocked = client.get("/v1/sources/D01")
    assert blocked.status_code == 200
    assert blocked.json()["reason_code"] == "credential_required"
    assert blocked.json()["observations"] == []
    assert "29.7" not in blocked.text
    coral = client.get("/v1/sources/D15")
    assert coral.status_code == 200
    body = coral.json()
    assert body["status"] == "available"
    assert body["data_mode"] == "real"
    assert body["freshness"] == freshness_for(
        datetime(2026, 11, 11, 12, tzinfo=timezone.utc),
        datetime.now(timezone.utc),
    )
    assert body["observations"][3]["id"] == "d15-sst-20261111T120000Z-r1"
    assert body["checksum_sha256"] == "b190912a4f0a8f94ae0b4a5fa4e5254547fef88f93518559cae80b60954af231"
    field = client.get("/v1/sources/D15/observations/d15-sst-20261111T120000Z-r1/field")
    assert field.status_code == 200
    payload = field.json()
    assert payload["width"] * payload["height"] == len(payload["values"])
    assert 29.73 in payload["values"]
    assert payload["missing_cells"] == 0
    assert -327.68 not in payload["values"]
    asset = client.get(f"/v1/sources/D15/assets/{body['asset_id']}")
    assert asset.json()["checksum_sha256"] == body["checksum_sha256"]
    assert asset.json()["science_file_retrieved"] is True


def test_cors_and_body_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EARTH_ECHO_MAX_BODY_BYTES", "64")
    get_settings.cache_clear()
    client = TestClient(create_app())
    allowed = client.get("/health", headers={"Origin": "http://127.0.0.1:5173"})
    blocked = client.get("/health", headers={"Origin": "http://evil.example"})
    assert allowed.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"
    assert blocked.headers.get("access-control-allow-origin") is None
    too_big = client.post("/health", content=b"x" * 128)
    assert too_big.status_code == 413
    assert client.get("/openapi.json").json()["paths"]["/health"]
