from __future__ import annotations

import datetime as dt

from pydantic import BaseModel


class JobRunOut(BaseModel):
    id: int
    source_id: str
    scheduled_for: dt.datetime
    attempt: int
    started_at: dt.datetime
    finished_at: dt.datetime | None
    status: str
    rows_extracted: int | None
    rows_loaded: int | None
    error: str | None

    model_config = {"from_attributes": True}


class SourceOut(BaseModel):
    source_id: str
    interval_seconds: int
    enabled: bool
    freshness_status: str
    last_success_at: dt.datetime | None
    staleness_seconds: float | None
