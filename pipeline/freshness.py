"""Freshness classification: how stale is a source's data right now
relative to its configured interval. Computed live from job_runs on every
call rather than stored, so it's always consistent with the actual
execution history.

Thresholds (multiples of the source's own interval_seconds):
  fresh    -- last success within 1x interval
  stale    -- last success within 1x-3x interval
  critical -- last success beyond 3x interval, or no success ever
"""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pipeline.models import JobRun

FreshnessStatus = Literal["fresh", "stale", "critical"]

STALE_MULTIPLIER = 1.0
CRITICAL_MULTIPLIER = 3.0


class SourceFreshness(BaseModel):
    source_id: str
    status: FreshnessStatus
    interval_seconds: int
    last_success_at: dt.datetime | None
    staleness_seconds: float | None


def classify(staleness_seconds: float | None, interval_seconds: int) -> FreshnessStatus:
    if staleness_seconds is None:
        return "critical"
    if staleness_seconds <= interval_seconds * STALE_MULTIPLIER:
        return "fresh"
    if staleness_seconds <= interval_seconds * CRITICAL_MULTIPLIER:
        return "stale"
    return "critical"


async def get_source_freshness(
    session: AsyncSession, source_id: str, interval_seconds: int
) -> SourceFreshness:
    result = await session.execute(
        select(JobRun.finished_at)
        .where(JobRun.source_id == source_id, JobRun.status == "success")
        .order_by(JobRun.finished_at.desc())
        .limit(1)
    )
    last_success_at = result.scalar_one_or_none()

    staleness_seconds: float | None = None
    if last_success_at is not None:
        staleness_seconds = (dt.datetime.now(dt.UTC) - last_success_at).total_seconds()

    return SourceFreshness(
        source_id=source_id,
        status=classify(staleness_seconds, interval_seconds),
        interval_seconds=interval_seconds,
        last_success_at=last_success_at,
        staleness_seconds=staleness_seconds,
    )
