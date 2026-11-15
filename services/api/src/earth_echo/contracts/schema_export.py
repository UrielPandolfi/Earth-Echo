"""Exporta el esquema JSON y los tipos TypeScript desde los modelos Pydantic."""

import json
import sys
from typing import Any

from earth_echo.catalog.views import CatalogValidationReport, PhenomenonList, SourceList, VariableList
from earth_echo.contracts.api_models import HealthResponse, ProviderReport, ReadyResponse
from earth_echo.contracts.records import AssetRecord, ForecastRecord, ObservationRecord, SignalQueryResult
from earth_echo.contracts.typescript_emit import emit_typescript
from earth_echo.contracts.types import ApiModel
from earth_echo.contracts.products import ProductList
from earth_echo.contracts.operations import RefreshStatus
from earth_echo.contracts.analyses import SSTAnomalyView,AssociationView,TrendView
from earth_echo.paths import repo_root


class ContractBundle(ApiModel):
    sst_trend_analysis: TrendView
    associations: AssociationView
    sst_anomaly_analysis: SSTAnomalyView
    refresh: RefreshStatus
    scientific_products: ProductList
    health: HealthResponse
    ready: ReadyResponse
    providers: ProviderReport
    sources: SourceList
    phenomena: PhenomenonList
    variables: VariableList
    validation: CatalogValidationReport
    observation: ObservationRecord
    asset: AssetRecord
    signal_query: SignalQueryResult
    forecast: ForecastRecord


def build_schema() -> dict[str, Any]:
    schema = ContractBundle.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    return schema


def render_schema_text() -> str:
    return json.dumps(build_schema(), indent=2, ensure_ascii=False) + "\n"


def render_typescript_text() -> str:
    return emit_typescript(build_schema())


def schema_path():
    return repo_root() / "contracts" / "schemas" / "earth-echo.schema.json"


def typescript_path():
    return repo_root() / "apps" / "web" / "src" / "domain" / "generated.ts"


def write_contracts() -> None:
    schema = schema_path()
    typescript = typescript_path()
    schema.parent.mkdir(parents=True, exist_ok=True)
    typescript.parent.mkdir(parents=True, exist_ok=True)
    schema.write_text(render_schema_text(), encoding="utf-8", newline="\n")
    typescript.write_text(render_typescript_text(), encoding="utf-8", newline="\n")


def contracts_match() -> bool:
    expected_schema = render_schema_text()
    expected_typescript = render_typescript_text()
    actual_schema = schema_path().read_text(encoding="utf-8").replace("\r\n", "\n")
    actual_typescript = typescript_path().read_text(encoding="utf-8").replace("\r\n", "\n")
    return actual_schema == expected_schema and actual_typescript == expected_typescript


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--write" in args:
        write_contracts()
        print(schema_path())
        print(typescript_path())
        return 0
    if "--check" in args:
        if contracts_match():
            print("Los contratos generados coinciden.")
            return 0
        print("Los contratos generados difieren. Ejecutá el módulo con --write.", file=sys.stderr)
        return 1
    print("Usá --write o --check.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
