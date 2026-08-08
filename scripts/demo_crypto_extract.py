import asyncio
import datetime as dt
import json

from pipeline.sources.base import SourceConfig
from pipeline.sources.crypto import CryptoSource


async def main() -> None:
    config = SourceConfig(
        source_id="crypto",
        interval_seconds=60,
        extra={"assets": {"bitcoin": "BTC", "ethereum": "ETH", "solana": "SOL"}},
    )
    source = CryptoSource(config)
    run_slot = dt.datetime.now(dt.UTC)

    raw_records = await source.extract(run_slot)
    print("=== RAW (extract) ===")
    print(json.dumps(raw_records, indent=2, default=str))

    print("\n=== PARSED (transform) ===")
    for raw in raw_records:
        record = source.parse(raw, run_slot)
        print(record.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
