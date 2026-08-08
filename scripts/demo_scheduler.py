"""Runs the real APScheduler wiring against a short interval so multiple
trigger cycles are observable in a short demo window, using the real
WeatherSource against the real Open-Meteo API and the real local Postgres.
"""

import asyncio
import datetime as dt

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from pipeline.db import SessionLocal
from pipeline.extract import run_job
from pipeline.models import JobRun
from pipeline.sources.base import SourceConfig
from pipeline.sources.weather import WeatherSource
from pipeline.time_utils import truncate_to_interval

DEMO_INTERVAL_SECONDS = 5
CONFIG = SourceConfig(
    source_id="weather",
    interval_seconds=DEMO_INTERVAL_SECONDS,
    extra={"locations": [{"location_id": "new_york", "latitude": 40.7128, "longitude": -74.0060}]},
)


async def _tick() -> None:
    source = WeatherSource(CONFIG)
    run_slot = truncate_to_interval(dt.datetime.now(dt.UTC), DEMO_INTERVAL_SECONDS)
    async with SessionLocal() as session:
        job = await run_job(session, source, run_slot)
        print(f"[scheduler tick] run_slot={run_slot} status={job.status} rows_loaded={job.rows_loaded}")


async def main() -> None:
    scheduler = AsyncIOScheduler(timezone=dt.UTC)
    scheduler.add_job(
        _tick,
        trigger=IntervalTrigger(seconds=DEMO_INTERVAL_SECONDS),
        id="weather-demo",
        next_run_time=dt.datetime.now(dt.UTC),
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()

    await asyncio.sleep(22)  # let it fire ~4-5 times
    scheduler.shutdown(wait=False)

    async with SessionLocal() as session:
        result = await session.execute(
            select(JobRun)
            .where(JobRun.source_id == "weather")
            .order_by(JobRun.id.desc())
            .limit(6)
        )
        print("\n=== Recent job_runs (scheduler-triggered) ===")
        for run in reversed(result.scalars().all()):
            print(
                f"id={run.id} scheduled_for={run.scheduled_for} status={run.status} "
                f"rows_loaded={run.rows_loaded} started_at={run.started_at}"
            )


if __name__ == "__main__":
    asyncio.run(main())
