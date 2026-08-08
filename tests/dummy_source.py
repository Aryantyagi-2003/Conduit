"""A Source test double: no network, deterministic, controllable per-call
payloads. Used to exercise the *generic* transform/load/job-runner pipeline
in isolation from any real API's flakiness. Real per-source parsing logic
(e.g. WeatherSource.parse) is covered separately in test_weather_source.py.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, ClassVar

from pydantic import BaseModel

from pipeline.models import WeatherObservation
from pipeline.sources.base import SourceConfig


class DummyRecord(BaseModel):
    location_id: str
    observed_at: dt.datetime
    temperature_c: float
    humidity_pct: float
    wind_speed_ms: float
    raw: dict[str, Any]
    fetched_at: dt.datetime


class DummySource:
    source_id: ClassVar[str] = "dummy_weather"
    record_model: ClassVar[type[BaseModel]] = DummyRecord
    table = WeatherObservation.__table__
    natural_key: ClassVar[tuple[str, ...]] = ("location_id", "observed_at")

    def __init__(self, config: SourceConfig, batches: list[list[dict[str, Any]]]):
        self.config = config
        self._batches = iter(batches)
        self.extract_calls = 0

    async def extract(self, run_slot: dt.datetime) -> list[dict[str, Any]]:
        self.extract_calls += 1
        return next(self._batches)

    def parse(self, raw: dict[str, Any], run_slot: dt.datetime) -> DummyRecord:
        return DummyRecord(**raw)
