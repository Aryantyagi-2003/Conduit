"""APScheduler wiring: one interval trigger per enabled source, each with
its own configured interval_seconds (not a single global interval).

Why APScheduler and not Prefect: see README ("Orchestration" section). In
short, Conduit's jobs are independent, single-step, source-scoped ETL runs
with no cross-source dependencies -- Prefect's DAG/server/UI machinery buys
nothing here that a lightweight in-process scheduler plus the job_runs
table (which we need for observability regardless) doesn't already cover.
"""

from __future__ import annotations

import datetime as dt
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from pipeline.db import SessionLocal
from pipeline.extract import run_job
from pipeline.registry import SOURCES
from pipeline.time_utils import truncate_to_interval

logger = logging.getLogger("conduit.scheduler")


async def _run_source_job(source_id: str) -> None:
    source_cls, config = SOURCES[source_id]
    source = source_cls(config)
    run_slot = truncate_to_interval(dt.datetime.now(dt.UTC), config.interval_seconds)
    async with SessionLocal() as session:
        await run_job(session, source, run_slot)


def build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=dt.UTC)
    for source_id, (_, config) in SOURCES.items():
        if not config.enabled:
            continue
        scheduler.add_job(
            _run_source_job,
            trigger=IntervalTrigger(seconds=config.interval_seconds),
            args=[source_id],
            id=source_id,
            next_run_time=dt.datetime.now(dt.UTC),
            max_instances=1,
            coalesce=True,
            misfire_grace_time=config.interval_seconds,
        )
        logger.info(
            "scheduled_source",
            extra={"source_id": source_id, "interval_seconds": config.interval_seconds},
        )
    return scheduler
