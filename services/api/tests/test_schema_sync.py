import json

from jsonschema.validators import Draft202012Validator

from earth_echo.connectors.usgs_comcat import load_usgs_observation
from earth_echo.contracts.schema_export import contracts_match, schema_path


def _validator(name: str) -> Draft202012Validator:
    schema = json.loads(schema_path().read_text(encoding="utf-8"))
    return Draft202012Validator(
        {
            "$schema": schema["$schema"],
            "$ref": f"#/$defs/{name}",
            "$defs": schema["$defs"],
        }
    )


def test_generated_contracts_match_the_models() -> None:
    assert contracts_match()


def test_json_schema_rejects_a_missing_value_stored_as_zero() -> None:
    observation = load_usgs_observation().model_dump(mode="json")
    validator = _validator("ObservationRecord")
    assert list(validator.iter_errors(observation)) == []
    broken = json.loads(json.dumps(observation))
    broken["measurement"] = {"status": "missing", "value": 0, "unit": "m"}
    assert list(validator.iter_errors(broken))
