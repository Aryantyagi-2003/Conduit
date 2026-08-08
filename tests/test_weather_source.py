from __future__ import annotations

import datetime as dt

import pytest
from pydantic import ValidationError

from pipeline.sources.base import SourceConfig
from pipeline.sources.weather import WeatherSource

RUN_SLOT = dt.datetime(2026, 8, 8, 19, 0, tzinfo=dt.UTC)

# Captured from a real Open-Meteo response (see scripts/demo_weather_extract.py).
SAMPLE_RESPONSE = {
    "location_id": "new_york",
    "response": {
        "latitude": 40.710335,
        "longitude": -73.99308,
        "current_units": {"time": "iso8601", "temperature_2m": "°C"},
        "current": {
            "time": "2026-08-08T18:30",
            "interval": 900,
            "temperature_2m": 30.3,
            "relative_humidity_2m": 71,
            "wind_speed_10m": 16.1,
        },
    },
}


def make_source() -> WeatherSource:
    return WeatherSource(
        SourceConfig(
            source_id="weather",
            interval_seconds=900,
            extra={
                "locations": [{"location_id": "new_york", "latitude": 40.71, "longitude": -74.0}]
            },
        )
    )


def test_parse_converts_km_h_to_m_s():
    record = make_source().parse(SAMPLE_RESPONSE, RUN_SLOT)
    assert record.wind_speed_ms == pytest.approx(16.1 / 3.6)


def test_parse_uses_the_apis_own_timestamp_not_run_slot():
    different_run_slot = RUN_SLOT + dt.timedelta(hours=3)
    record = make_source().parse(SAMPLE_RESPONSE, different_run_slot)
    assert record.observed_at == dt.datetime(2026, 8, 8, 18, 30, tzinfo=dt.UTC)


def test_parse_rejects_out_of_range_humidity():
    bad = {
        "location_id": "new_york",
        "response": {
            "current": {
                "time": "2026-08-08T18:30",
                "temperature_2m": 30.3,
                "relative_humidity_2m": 150,  # invalid: > 100
                "wind_speed_10m": 16.1,
            }
        },
    }
    with pytest.raises(ValidationError):
        make_source().parse(bad, RUN_SLOT)
