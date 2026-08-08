import asyncio
import datetime as dt
import json

from pipeline.sources.base import SourceConfig
from pipeline.sources.github import GithubSource
from pipeline.time_utils import truncate_to_interval


async def main() -> None:
    config = SourceConfig(
        source_id="github",
        interval_seconds=1800,
        extra={"repos": ["torvalds/linux", "python/cpython", "anthropics/claude-code"]},
    )
    source = GithubSource(config)
    run_slot = truncate_to_interval(dt.datetime.now(dt.UTC), config.interval_seconds)

    raw_records = await source.extract(run_slot)
    print("=== RAW (extract) ===")
    print(json.dumps(raw_records, indent=2, default=str)[:2000], "...(truncated)")

    print("\n=== PARSED (transform) ===")
    for raw in raw_records:
        record = source.parse(raw, run_slot)
        print(record.model_dump_json(indent=2, exclude={"raw"}))


if __name__ == "__main__":
    asyncio.run(main())
