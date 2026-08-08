from __future__ import annotations

import datetime as dt

import pytest
from sqlalchemy import func, select

from pipeline.extract import run_job
from pipeline.models import JobRun, WeatherObservation
from pipeline.sources.base import SourceConfig
from tests.dummy_source import DummySource

RUN_SLOT = dt.datetime(2026, 8, 8, 19, 0, tzinfo=dt.UTC)


def raw(location_id: str, temperature_c: float) -> dict:
    return {
        "location_id": location_id,
        "observed_at": RUN_SLOT.isoformat(),
        "temperature_c": temperature_c,
        "humidity_pct": 50.0,
        "wind_speed_ms": 3.0,
        "raw": {"note": "test fixture"},
        "fetched_at": RUN_SLOT.isoformat(),
    }


async def row_count(session) -> int:
    result = await session.execute(select(func.count()).select_from(WeatherObservation))
    return result.scalar_one()


@pytest.mark.asyncio
async def test_rerunning_same_job_does_not_duplicate_rows(session):
    """The exact claim under test: running the same extraction+load twice
    must not change the row count. Not 'the upsert function exists' — an
    actual second run against the real table, with a real row-count assertion.
    """
    batch = [raw("new_york", 30.0), raw("london", 27.0)]
    source = DummySource(
        SourceConfig(source_id="dummy_weather", interval_seconds=900),
        batches=[batch, batch],  # identical payload both times
    )

    job1 = await run_job(session, source, RUN_SLOT)
    assert job1.status == "success"
    count_after_first_run = await row_count(session)
    assert count_after_first_run == 2

    job2 = await run_job(session, source, RUN_SLOT)
    assert job2.status == "success"
    count_after_second_run = await row_count(session)

    assert count_after_second_run == count_after_first_run
    assert source.extract_calls == 2


@pytest.mark.asyncio
async def test_rerun_with_changed_values_updates_in_place_not_duplicates(session):
    """Proves ON CONFLICT DO UPDATE actually updates (not a silent no-op):
    same natural key, different temperature on the second run -> row count
    stays at 1 but the stored value changes to the new one.
    """
    source = DummySource(
        SourceConfig(source_id="dummy_weather", interval_seconds=900),
        batches=[[raw("new_york", 30.0)], [raw("new_york", 99.0)]],
    )

    await run_job(session, source, RUN_SLOT)
    await run_job(session, source, RUN_SLOT)

    result = await session.execute(select(WeatherObservation))
    rows = result.scalars().all()
    assert len(rows) == 1
    assert float(rows[0].temperature_c) == 99.0


@pytest.mark.asyncio
async def test_job_runs_records_one_row_per_attempt_even_when_idempotent(session):
    """job_runs is an execution log, not deduped by run_slot -- every
    attempt gets its own row for observability, even though the data table
    doesn't grow.
    """
    batch = [raw("new_york", 30.0)]
    source = DummySource(
        SourceConfig(source_id="dummy_weather", interval_seconds=900), batches=[batch, batch]
    )

    await run_job(session, source, RUN_SLOT)
    await run_job(session, source, RUN_SLOT)

    result = await session.execute(
        select(func.count()).select_from(JobRun).where(JobRun.source_id == "dummy_weather")
    )
    assert result.scalar_one() == 2
