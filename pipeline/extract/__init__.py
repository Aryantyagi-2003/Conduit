"""Job runner: ties extract -> transform -> load together for one source,
one scheduled run_slot, recording a job_runs row for observability.
"""

from __future__ import annotations

import datetime as dt
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from pipeline.load import upsert
from pipeline.models import JobRun
from pipeline.retry import ExtractionError, RateLimited
from pipeline.sources.base import Source
from pipeline.transform import normalize

logger = logging.getLogger("conduit.job")


async def run_job(
    session: AsyncSession, source: Source, run_slot: dt.datetime, attempt: int = 1
) -> JobRun:
    started_at = dt.datetime.now(dt.UTC)
    job_run = JobRun(
        source_id=source.source_id,
        scheduled_for=run_slot,
        attempt=attempt,
        started_at=started_at,
        status="running",
    )
    session.add(job_run)
    await session.commit()

    try:
        raw_records = await source.extract(run_slot)
        records = normalize(source, raw_records, run_slot)
        rows_loaded = await upsert(session, source, records)

        job_run.finished_at = dt.datetime.now(dt.UTC)
        job_run.status = "success"
        job_run.rows_extracted = len(raw_records)
        job_run.rows_loaded = rows_loaded
        logger.info(
            "job_succeeded",
            extra={
                "source_id": source.source_id,
                "rows_extracted": len(raw_records),
                "rows_loaded": rows_loaded,
            },
        )
    except (RateLimited, ExtractionError) as exc:
        job_run.finished_at = dt.datetime.now(dt.UTC)
        job_run.status = "failed"
        job_run.error = str(exc)
        logger.error("job_failed", extra={"source_id": source.source_id, "error": str(exc)})
    except Exception as exc:  # unexpected — still record it, don't crash the scheduler
        job_run.finished_at = dt.datetime.now(dt.UTC)
        job_run.status = "failed"
        job_run.error = repr(exc)
        logger.exception("job_failed_unexpected", extra={"source_id": source.source_id})

    await session.commit()
    return job_run
