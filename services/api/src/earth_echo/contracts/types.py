"""Tipos de frontera: tiempo UTC, identificadores y estados."""

from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, WithJsonSchema
from pydantic.functional_validators import BeforeValidator

DataMode = Literal["real", "demo"]
CapabilityStatus = Literal[
    "specified",
    "source_connected",
    "historical_ready",
    "experimental",
    "validated_for_scope",
]
IntegrationStatus = Literal[
    "documented",
    "credential_required",
    "sample_retrieved",
    "connected",
    "blocked",
]
OutputClass = Literal[
    "observation",
    "diagnosis",
    "trend",
    "hazard",
    "risk",
    "nowcast",
    "forecast",
    "research_signal",
]
SpatialRole = Literal[
    "observation_location",
    "grid_cell",
    "gridded_product",
    "area",
    "track",
    "region_anchor",
]
RetrievalKind = Literal["viability_sample", "demo_fixture", "live"]
UnavailableReason = Literal[
    "insufficient_data",
    "source_unreachable",
    "not_implemented",
    "credential_required",
    "outside_coverage",
    "quality_rejected",
    "no_demo_fixture",
]

RecordId = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")]
CatalogSourceId = Annotated[str, Field(pattern=r"^D\d{2}$")]
VariableId = Annotated[str, Field(pattern=r"^V\d{2}$")]
PhenomenonId = Annotated[str, Field(pattern=r"^F\d{2}$")]
Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


def parse_utc(value: object) -> datetime:
    if isinstance(value, datetime):
        moment = value
    elif isinstance(value, str):
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise ValueError("La fecha debe ser texto ISO 8601 o datetime.")
    if moment.tzinfo is None or moment.tzinfo.utcoffset(moment) is None:
        raise ValueError("La fecha debe incluir zona horaria. El almacenamiento es UTC.")
    return moment.astimezone(timezone.utc)


def dump_utc(moment: datetime) -> str:
    text = moment.astimezone(timezone.utc).isoformat()
    if text.endswith("+00:00"):
        return text[:-6] + "Z"
    return text


UtcDateTime = Annotated[
    datetime,
    BeforeValidator(parse_utc),
    PlainSerializer(dump_utc, return_type=str, when_used="json"),
    WithJsonSchema({"type": "string", "format": "date-time"}),
]


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
