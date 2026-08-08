import asyncio
import datetime as dt

from sqlalchemy import func, select

from pipeline.db import SessionLocal
from pipeline.extract import run_job
from pipeline.models import WeatherObservation
from pipeline.sources.base import SourceConfig
from pipeline.sources.weather import WeatherSource

CONFIG = SourceConfig(
    source_id="weather",
    interval_seconds=900,
    extra={
        "locations": [
            {"location_id": "new_york", "latitude": 40.7128, "longitude": -74.0060},
            {"location_id": "london", "latitude": 51.5072, "longitude": -0.1276},
        ]
    },
)


async def row_count() -> int:
    async with SessionLocal() as session:
        result = await session.execute(select(func.count()).select_from(WeatherObservation))
        return result.scalar_one()


async def main() -> None:
    source = WeatherSource(CONFIG)
    run_slot = dt.datetime.now(dt.UTC).replace(second=0, microsecond=0)

    print("=== RUN 1 (first extraction for this run_slot) ===")
    async with SessionLocal() as session:
        job1 = await run_job(session, source, run_slot)
    print(f"status={job1.status} rows_extracted={job1.rows_extracted} rows_loaded={job1.rows_loaded}")
    count_after_1 = await row_count()
    print(f"weather_observations row count: {count_after_1}")

    print("\n=== RUN 2 (re-run for the SAME run_slot — idempotency check) ===")
    async with SessionLocal() as session:
        job2 = await run_job(session, source, run_slot)
    print(f"status={job2.status} rows_extracted={job2.rows_extracted} rows_loaded={job2.rows_loaded}")
    count_after_2 = await row_count()
    print(f"weather_observations row count: {count_after_2}")
    print(f"\nrow count unchanged: {count_after_1 == count_after_2}")

    async with SessionLocal() as session:
        result = await session.execute(select(WeatherObservation).order_by(WeatherObservation.location_id))
        print("\n=== Loaded rows ===")
        for row in result.scalars():
            print(
                f"{row.location_id:10s} observed_at={row.observed_at} "
                f"temp_c={row.temperature_c} humidity_pct={row.humidity_pct} "
                f"wind_ms={float(row.wind_speed_ms):.2f} fetched_at={row.fetched_at}"
            )


if __name__ == "__main__":
    asyncio.run(main())
