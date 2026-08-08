import asyncio
import datetime as dt

from sqlalchemy import func, select

from pipeline.db import SessionLocal
from pipeline.extract import run_job
from pipeline.models import CryptoPrice
from pipeline.registry import SOURCES


async def row_count() -> int:
    async with SessionLocal() as session:
        result = await session.execute(select(func.count()).select_from(CryptoPrice))
        return result.scalar_one()


async def main() -> None:
    source_cls, config = SOURCES["crypto"]
    source = source_cls(config)
    run_slot = dt.datetime.now(dt.UTC)

    print("=== RUN 1 ===")
    async with SessionLocal() as session:
        job1 = await run_job(session, source, run_slot)
    print(f"status={job1.status} rows_extracted={job1.rows_extracted} rows_loaded={job1.rows_loaded}")
    c1 = await row_count()
    print(f"crypto_prices row count: {c1}")

    print("\n=== RUN 2 (re-run, idempotency check) ===")
    async with SessionLocal() as session:
        job2 = await run_job(session, source, run_slot)
    print(f"status={job2.status} rows_extracted={job2.rows_extracted} rows_loaded={job2.rows_loaded}")
    c2 = await row_count()
    print(f"crypto_prices row count: {c2}")
    print(f"row count unchanged: {c1 == c2}")

    async with SessionLocal() as session:
        result = await session.execute(select(CryptoPrice).order_by(CryptoPrice.asset_symbol))
        print("\n=== Loaded rows ===")
        for row in result.scalars():
            print(
                f"{row.asset_symbol:5s} observed_at={row.observed_at} "
                f"price_usd={row.price_usd} market_cap={row.market_cap} volume_24h={row.volume_24h}"
            )


if __name__ == "__main__":
    asyncio.run(main())
