"""Typed summaries of calculated analyses, separate from event counts."""
from typing import Literal
from earth_echo.contracts.types import ApiModel
from earth_echo.contracts.products import ScientificProduct


class SSTAnomalyView(ApiModel):
    data_mode: Literal['real']='real'
    status: Literal['evaluated','not_evaluable','unavailable']
    reason: str | None=None
    assessment_period: str='2022–2025 · histórico'
    assessed_months: int=0
    flagged_months: int=0
    warm_months: int=0
    cold_months: int=0
    missing_months: int=0
    stale_input: bool=False
    product: ScientificProduct | None=None
