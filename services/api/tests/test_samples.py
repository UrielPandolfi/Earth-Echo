import copy
import json
from datetime import datetime, timedelta, timezone

from earth_echo.connectors.smap_metadata import load_smap_asset, sample_paths as smap_paths
from earth_echo.connectors.usgs_comcat import build_usgs_records, load_usgs_records, sample_paths
from earth_echo.demo.store import load_demo_signal
from earth_echo.queries.signals import query_signals


AS_OF = datetime(2026, 11, 13, 6, tzinfo=timezone.utc)


def test_usgs_sample_keeps_longitude_time_and_does_not_invent_probability() -> None:
    event_path, retrieval_path = sample_paths()
    raw = json.loads(event_path.read_text(encoding="utf-8"))
    feature = raw["features"][0]
    asset, observation = load_usgs_records()
    longitude, latitude, depth = feature["geometry"]["coordinates"]
    assert longitude == 155.5297
    assert abs(longitude) > 90
    assert observation.spatial.geometry is not None
    assert observation.spatial.geometry.type == "Point"
    assert observation.spatial.geometry.coordinates[0] == longitude
    assert observation.spatial.geometry.coordinates[1] == latitude
    assert observation.spatial.vertical is not None
    assert observation.spatial.vertical.value == depth
    assert observation.spatial.vertical.unit == "km"
    assert observation.observed.kind == "instant"
    assert observation.observed.start == datetime.fromtimestamp(
        feature["properties"]["time"] / 1000,
        tz=timezone.utc,
    )
    assert observation.measurement.status == "present"
    assert observation.measurement.value == feature["properties"]["mag"]
    assert observation.measurement.unit == feature["properties"]["magType"]
    assert observation.availability.status == "unknown"
    assert observation.data_mode == "real"
    assert observation.phenomenon_id is None
    assert "probability" not in observation.model_dump()
    assert asset.science_file_retrieved is True
    assert asset.checksum_sha256 == json.loads(retrieval_path.read_text(encoding="utf-8"))["sha256"]
    assert asset.byte_size == event_path.stat().st_size


def test_null_magnitude_stays_missing() -> None:
    event_path, retrieval_path = sample_paths()
    raw = json.loads(event_path.read_text(encoding="utf-8"))
    feature = copy.deepcopy(raw["features"][0])
    feature["properties"]["mag"] = None
    retrieval = json.loads(retrieval_path.read_text(encoding="utf-8"))
    _, observation = build_usgs_records(
        feature,
        product_version="test",
        ingested_at=datetime.fromisoformat(retrieval["retrieved_at"].replace("Z", "+00:00")),
        checksum=retrieval["sha256"],
        byte_size=1,
    )
    assert observation.measurement.status == "missing"
    assert observation.measurement.value is None


def test_smap_metadata_is_not_a_soil_moisture_value() -> None:
    granule_path, _retrieval = smap_paths()
    entry = json.loads(granule_path.read_text(encoding="utf-8"))["feed"]["entry"][0]
    asset = load_smap_asset()
    start = datetime.fromisoformat(entry["time_start"].replace("Z", "+00:00"))
    assert asset.science_file_retrieved is False
    assert asset.native_unit is None
    assert asset.data_mode == "real"
    assert asset.variable_id == "V08"
    assert asset.observed.kind == "interval"
    assert asset.observed.start == start
    assert asset.observed.end == start.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    assert asset.observed.end != datetime.fromisoformat(entry["time_end"].replace("Z", "+00:00"))
    dumped = asset.model_dump(mode="json")
    assert "value" not in dumped
    assert asset.byte_size == granule_path.stat().st_size
    assert asset.byte_size < 100_000
    assert float(entry["granule_size"]) > 100
    assert asset.spatial.role == "gridded_product"
    assert asset.spatial.extent is not None
    assert asset.spatial.extent.west == -180
    assert asset.spatial.extent.east == 180


def test_real_mode_does_not_return_the_demo_signal() -> None:
    demo = load_demo_signal()
    real = query_signals("F11", "real", AS_OF)
    other = query_signals("F01", "demo", AS_OF)
    shown = query_signals("F11", "demo", AS_OF)
    assert demo.measurement.value == -0.04
    assert demo.probability.state == "absent"
    assert real.status == "unavailable"
    assert real.unavailable is not None
    assert real.unavailable.reason_code == "credential_required"
    assert real.signals == []
    assert "-0.04" not in real.model_dump_json()
    assert other.status == "unavailable"
    assert other.unavailable is not None
    assert other.unavailable.reason_code == "no_demo_fixture"
    assert shown.status == "available"
    assert shown.signals[0].data_mode == "demo"
    assert shown.forecasts == []
