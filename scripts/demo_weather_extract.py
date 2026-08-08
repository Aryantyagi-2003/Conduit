import asyncio
import datetime as dt
import json

from pipeline.sources.base import SourceConfig
from pipeline.sources.weather import WeatherSource


async def main() -> None:
    config = SourceConfig(
        source_id="weather",
        interval_seconds=900,
        extra={
            "locations": [
                {"location_id": "new_york", "latitude": 40.7128, "longitude": -74.0060},
                {"location_id": "london", "latitude": 51.5072, "longitude": -0.1276},
            ]
        },
    )
    source = WeatherSource(config)
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
