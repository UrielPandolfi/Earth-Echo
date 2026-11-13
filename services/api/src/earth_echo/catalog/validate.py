"""Comprueba identificadores y referencias del catálogo sin modificar los archivos."""

import re
from collections import Counter

from earth_echo.catalog.load import (
    REFERENCE_FILES,
    catalog_path,
    file_sha256,
    load_catalog,
    load_integrity_pin,
)
from earth_echo.catalog.views import (
    CatalogValidationReport,
    DescriptiveNote,
    RecordedHttpCheck,
    ReferenceMention,
    StatusCount,
)
from earth_echo.contracts.types import CapabilityStatus
from earth_echo.paths import relative_to_repo, repo_root

_SOURCE_ID = re.compile(r"\bD\d{2}\b")
_STATUS_MAP: dict[str, CapabilityStatus] = {
    "Especificado sin implementar": "specified",
}


def normalize_capability(raw_status: str) -> CapabilityStatus:
    try:
        return _STATUS_MAP[raw_status]
    except KeyError as exc:
        raise ValueError(f"Estado de catálogo no reconocido: {raw_status}") from exc


def descriptive_remainder(note: str) -> str:
    text = _SOURCE_ID.sub(" ", note)
    return re.sub(r"\s+", " ", text).strip(" \t,;.:")


def _integrity(pin: dict[str, str] | None, filename: str) -> tuple[str | None, str]:
    digest = file_sha256(repo_root() / filename)
    if pin is None or filename not in pin:
        return None, "pin_missing"
    if pin[filename] == digest:
        return pin[filename], "match"
    return pin[filename], "mismatch"


def catalog_issues(document) -> dict[str, object]:
    source_ids = [item.id for item in document.sources]
    variable_ids = [item.id for item in document.variables]
    module_ids = [item.id for item in document.modules]
    duplicate_ids = [
        item_id
        for collection in (source_ids, variable_ids, module_ids)
        for item_id, count in Counter(collection).items()
        if count > 1
    ]
    known_sources = set(source_ids)
    dangling: list[ReferenceMention] = []
    referenced: set[str] = set()
    for variable in document.variables:
        for source_id in variable.source_ids:
            referenced.add(source_id)
            if source_id not in known_sources:
                dangling.append(
                    ReferenceMention(
                        owner_type="variable",
                        owner_id=variable.id,
                        source_id=source_id,
                    )
                )
    for module in document.modules:
        for source_id in module.source_ids:
            referenced.add(source_id)
            if source_id not in known_sources:
                dangling.append(
                    ReferenceMention(
                        owner_type="module",
                        owner_id=module.id,
                        source_id=source_id,
                    )
                )
    notes = [
        DescriptiveNote(variable_id=variable.id, remainder=remainder)
        for variable in document.variables
        if (remainder := descriptive_remainder(variable.source_notes))
    ]
    capability_counter: Counter[str] = Counter(
        normalize_capability(module.implementation_status) for module in document.modules
    )
    return {
        "duplicate_ids": duplicate_ids,
        "dangling_references": dangling,
        "unreferenced_source_ids": sorted(known_sources - referenced),
        "descriptive_source_notes": notes,
        "capability_counts": [
            StatusCount(status=status, count=count)
            for status, count in sorted(capability_counter.items())
        ],
    }


def validate_catalog() -> CatalogValidationReport:
    path = catalog_path()
    document = load_catalog()
    pin = load_integrity_pin()
    issues = catalog_issues(document)
    catalog_pin, catalog_state = _integrity(pin, "Earth_Echo_Catalogo.json")
    _, specification_state = _integrity(pin, "Earth_Echo_Especificacion.md")
    _, image_state = _integrity(pin, "Earth Echo Global Environmental Observatory.png")
    return CatalogValidationReport(
        schema_version="1.0",
        reference_path=relative_to_repo(path) if path.is_relative_to(repo_root()) else path.name,
        reference_sha256=file_sha256(path),
        pinned_sha256=catalog_pin,
        reference_integrity=catalog_state,  # type: ignore[arg-type]
        specification_integrity=specification_state,  # type: ignore[arg-type]
        image_integrity=image_state,  # type: ignore[arg-type]
        source_count=len(document.sources),
        variable_count=len(document.variables),
        phenomenon_count=len(document.modules),
        duplicate_ids=issues["duplicate_ids"],  # type: ignore[arg-type]
        dangling_references=issues["dangling_references"],  # type: ignore[arg-type]
        unreferenced_source_ids=issues["unreferenced_source_ids"],  # type: ignore[arg-type]
        descriptive_source_notes=issues["descriptive_source_notes"],  # type: ignore[arg-type]
        capability_counts=issues["capability_counts"],  # type: ignore[arg-type]
        recorded_http_checks=[
            RecordedHttpCheck(
                source=item.source,
                url=item.url,
                status=item.status,
                byte_count=item.byte_count,
                json_keys=item.json_keys,
                tested=item.tested,
                reexecuted=False,
            )
            for item in document.http_sample_checks
        ],
        recorded_http_checks_note=(
            "Estas comprobaciones HTTP están copiadas del catálogo del 12 de noviembre de 2026. "
            "Esta respuesta no volvió a llamar a los proveedores."
        ),
    )


def reference_files_present() -> bool:
    root = repo_root()
    return all((root / name).is_file() for name in REFERENCE_FILES)
