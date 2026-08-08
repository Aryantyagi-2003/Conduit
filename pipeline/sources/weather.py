"""Open-Meteo weather source. No API key required.

Docs: https://open-meteo.com/en/docs

Shape: time-series, numeric. The API returns its own `current.time`
timestamp (rounded to a 15-minute interval), so unlike the GitHub source,
`observed_at` here comes from the upstream API, not the scheduler's
run_slot — retries naturally land on the same natural key because the API
itself is quantized to that interval.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, ClassVar, cast

import httpx
from pydantic import BaseModel, Field
from sqlalchemy import Table

from pipeline.models import WeatherObservation
from pipeline.retry import ExtractionError, RateLimited, with_backoff
from pipeline.sources.base import SourceConfig

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


class WeatherRecord(BaseModel):
    location_id: str
    observed_at: dt.datetime
    temperature_c: float
    humidity_pct: float = Field(ge=0, le=100)
    wind_speed_ms: float = Field(ge=0)
    raw: dict[str, Any]
    fetched_at: dt.datetime


class WeatherSource:
    source_id: ClassVar[str] = "weather"
    record_model: ClassVar[type[BaseModel]] = WeatherRecord
    table: ClassVar[Table] = cast(Table, WeatherObservation.__table__)
    natural_key: ClassVar[tuple[str, ...]] = ("location_id", "observed_at")

    def __init__(self, config: SourceConfig):
        self.config = config
        self.locations: list[dict[str, Any]] = config.extra["locations"]
        self._client = httpx.AsyncClient(timeout=10.0)

    @with_backoff(max_attempts=5, base_delay=1.0, max_delay=30.0)
    async def extract(self, run_slot: dt.datetime) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for loc in self.locations:
            resp = await self._client.get(
                OPEN_METEO_URL,
                params={
                    "latitude": loc["latitude"],
                    "longitude": loc["longitude"],
                    "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
                    "timezone": "UTC",
                },
            )
            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                raise RateLimited(
                    f"open-meteo rate limited for {loc['location_id']}",
                    retry_after=float(retry_after) if retry_after else None,
                )
            if resp.status_code >= 500:
                raise ExtractionError(f"open-meteo {resp.status_code} for {loc['location_id']}")
            resp.raise_for_status()
            body = resp.json()
            results.append({"location_id": loc["location_id"], "response": body})
        return results

    def parse(self, raw: dict[str, Any], run_slot: dt.datetime) -> WeatherRecord:
        current = raw["response"]["current"]
        return WeatherRecord(
            location_id=raw["location_id"],
            observed_at=dt.datetime.fromisoformat(current["time"]).replace(tzinfo=dt.UTC),
            temperature_c=current["temperature_2m"],
            humidity_pct=current["relative_humidity_2m"],
            wind_speed_ms=current["wind_speed_10m"] / 3.6,  # km/h -> m/s
            raw=raw["response"],
            fetched_at=dt.datetime.now(dt.UTC),
        )
