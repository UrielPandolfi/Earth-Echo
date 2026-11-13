from earth_echo.catalog.load import file_sha256, load_catalog
from earth_echo.catalog.models import (
    CatalogDocument,
    CatalogModule,
    CatalogSource,
    CatalogVariable,
    OutputContractExample,
)
from earth_echo.catalog.validate import catalog_issues, descriptive_remainder, validate_catalog
from earth_echo.paths import repo_root


def _source(source_id: str) -> CatalogSource:
    return CatalogSource(
        id=source_id,
        name=source_id,
        url="https://example.test/source",
        variables="",
        coverage="",
        cadence="",
        access="",
        limits="",
        verification="",
    )


def _document() -> CatalogDocument:
    return CatalogDocument(
        project="prueba",
        version="0",
        reviewed_on="2026-11-13",
        language="es",
        purpose="prueba",
        all_modules_implemented=False,
        all_sources_ingestion_verified=False,
        evidence_levels=[],
        sources=[_source("D01"), _source("D02")],
        variables=[
            CatalogVariable(
                id="V01",
                name="lluvia",
                units="mm",
                source_ids=["D09"],
                source_notes="D01 y registros locales",
                processing_notes="",
            )
        ],
        modules=[
            CatalogModule(
                id="F01",
                name="lluvia",
                family="Atmósfera",
                global_scope="",
                output_type="",
                required_inputs="",
                proposed_method="",
                horizon="",
                missing_or_local_data="",
                validation="",
                source_ids=["D01"],
                implementation_priority="P1",
                implementation_status="Especificado sin implementar",
            )
        ],
        http_sample_checks=[],
        output_contract_example=OutputContractExample(
            phenomenon_id="F01",
            output_type="ejemplo",
            model_version=None,
            run_id=None,
            issued_at=None,
            valid_from=None,
            valid_to=None,
            source_asset_ids=[],
            probability=None,
            probability_definition=None,
            uncertainty=None,
            validation_reference=None,
            operational_state="specified",
        ),
    )


def test_cross_check_finds_a_dangling_reference_and_prose() -> None:
    issues = catalog_issues(_document())
    assert issues["duplicate_ids"] == []
    assert issues["unreferenced_source_ids"] == ["D02"]
    dangling = issues["dangling_references"]
    assert len(dangling) == 1
    assert dangling[0].owner_id == "V01"
    assert dangling[0].source_id == "D09"
    assert descriptive_remainder("D01 y registros locales") == "y registros locales"


def test_reference_catalog_stays_intact_and_consistent() -> None:
    path = repo_root() / "Earth_Echo_Catalogo.json"
    before = file_sha256(path)
    document = load_catalog()
    report = validate_catalog()
    after = file_sha256(path)
    assert before == after
    assert report.reference_integrity == "match"
    assert report.specification_integrity == "match"
    assert report.image_integrity == "match"
    assert ":" not in report.reference_path
    assert report.source_count == len(document.sources) == 48
    assert report.variable_count == len(document.variables) == 26
    assert report.phenomenon_count == len(document.modules) == 31
    assert report.duplicate_ids == []
    assert report.dangling_references == []
    assert report.unreferenced_source_ids == ["D36", "D37", "D38", "D39", "D40"]
    assert {note.variable_id for note in report.descriptive_source_notes} == {
        "V14",
        "V18",
        "V21",
        "V22",
    }
    assert report.capability_counts[0].status == "specified"
    assert report.capability_counts[0].count == 31
    assert report.recorded_http_checks
    assert all(item.reexecuted is False for item in report.recorded_http_checks)
    assert "no volvió a llamar" in report.recorded_http_checks_note
