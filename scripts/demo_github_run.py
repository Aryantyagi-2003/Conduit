import asyncio
import datetime as dt

from sqlalchemy import func, select

from pipeline.db import SessionLocal
from pipeline.extract import run_job
from pipeline.models import GithubRepoStat
from pipeline.registry import SOURCES
from pipeline.time_utils import truncate_to_interval


async def row_count() -> int:
    async with SessionLocal() as session:
        result = await session.execute(select(func.count()).select_from(GithubRepoStat))
        return result.scalar_one()


async def main() -> None:
    source_cls, config = SOURCES["github"]
    source = source_cls(config)
    run_slot = truncate_to_interval(dt.datetime.now(dt.UTC), config.interval_seconds)

    print("=== RUN 1 ===")
    async with SessionLocal() as session:
        job1 = await run_job(session, source, run_slot)
    print(f"status={job1.status} rows_extracted={job1.rows_extracted} rows_loaded={job1.rows_loaded}")
    c1 = await row_count()
    print(f"github_repo_stats row count: {c1}")

    print("\n=== RUN 2 (re-run for the SAME run_slot, idempotency check) ===")
    async with SessionLocal() as session:
        job2 = await run_job(session, source, run_slot)
    print(f"status={job2.status} rows_extracted={job2.rows_extracted} rows_loaded={job2.rows_loaded}")
    c2 = await row_count()
    print(f"github_repo_stats row count: {c2}")
    print(f"row count unchanged: {c1 == c2}")

    async with SessionLocal() as session:
        result = await session.execute(select(GithubRepoStat).order_by(GithubRepoStat.repo_full_name))
        print("\n=== Loaded rows ===")
        for row in result.scalars():
            print(
                f"{row.repo_full_name:28s} observed_at={row.observed_at} "
                f"stars={row.stars} open_issues={row.open_issues} forks={row.forks} lang={row.language}"
            )


if __name__ == "__main__":
    asyncio.run(main())
