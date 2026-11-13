"""Señales por fenómeno y modo. REAL nunca cae a DEMO."""

from datetime import datetime

from earth_echo.contracts.records import SignalQueryResult, UnavailableResult
from earth_echo.contracts.types import DataMode, PhenomenonId, UnavailableReason, VariableId
from earth_echo.demo.store import load_demo_signal


def _unavailable(
    phenomenon_id: PhenomenonId,
    mode: DataMode,
    as_of: datetime,
    *,
    reason_code: UnavailableReason,
    reason: str,
    source_ids: list[str],
    variable_id: VariableId | None = None,
) -> SignalQueryResult:
    return SignalQueryResult(
        schema_version="1.0",
        requested_data_mode=mode,
        phenomenon_id=phenomenon_id,
        status="unavailable",
        signals=[],
        forecasts=[],
        unavailable=UnavailableResult(
            schema_version="1.0",
            status="unavailable",
            requested_data_mode=mode,
            reason_code=reason_code,
            reason=reason,
            phenomenon_id=phenomenon_id,
            variable_id=variable_id,
            source_ids=source_ids,
            as_of=as_of,
        ),
    )


def query_signals(phenomenon_id: PhenomenonId, mode: DataMode, as_of: datetime) -> SignalQueryResult:
    if mode == "demo":
        signal = load_demo_signal()
        if signal.phenomenon_id != phenomenon_id:
            return _unavailable(
                phenomenon_id,
                mode,
                as_of,
                reason_code="no_demo_fixture",
                reason="No hay un fixture de demostración para este fenómeno.",
                source_ids=[],
            )
        return SignalQueryResult(
            schema_version="1.0",
            requested_data_mode="demo",
            phenomenon_id=phenomenon_id,
            status="available",
            signals=[signal],
            forecasts=[],
            unavailable=None,
        )
    if phenomenon_id == "F11":
        return _unavailable(
            phenomenon_id,
            mode,
            as_of,
            reason_code="credential_required",
            reason=(
                "F11 en modo real necesita el archivo científico de D02 (SMAP SPL3SMP_E). "
                "La muestra guardada es solo metadatos de CMR. Configurá EARTHDATA_USERNAME y "
                "EARTHDATA_PASSWORD en el entorno local. El modo DEMO no se usa como reemplazo."
            ),
            source_ids=["D02"],
            variable_id="V08",
        )
    return _unavailable(
        phenomenon_id,
        mode,
        as_of,
        reason_code="not_implemented",
        reason=(
            "Este fenómeno está especificado en el catálogo y todavía no tiene una consulta real. "
            "La ausencia de implementación no se rellena con datos simulados."
        ),
        source_ids=[],
    )
