from typing import Literal
from pydantic import Field
from earth_echo.contracts.types import ApiModel,UtcDateTime

class RefreshJob(ApiModel):
    status: Literal['running','stored','unchanged','failed']
    last_attempt_at: UtcDateTime
    next_attempt_at: UtcDateTime
    last_success_at: UtcDateTime | None = None
    last_change_at: UtcDateTime | None = None
    error: str | None = None
    kept_previous: bool = False

class RefreshStatus(ApiModel):
    enabled: bool
    recent_scan: bool
    last_scan_at: UtcDateTime | None = None
    worker_pid: int | None = None
    heartbeat_at: UtcDateTime | None = None
    jobs: dict[str,RefreshJob] = Field(default_factory=dict)
    note: str
