"""The single place a new source gets wired in: one import, one dict entry.
Nothing else in the app changes.
"""

from __future__ import annotations

from collections.abc import Callable

from pipeline.sources.base import Source, SourceConfig
from pipeline.sources.weather import WeatherSource

SourceFactory = Callable[[SourceConfig], Source]

SOURCES: dict[str, tuple[SourceFactory, SourceConfig]] = {
    "weather": (
        WeatherSource,
        SourceConfig(
            source_id="weather",
            interval_seconds=900,
            extra={
                "locations": [
                    {"location_id": "new_york", "latitude": 40.7128, "longitude": -74.0060},
                    {"location_id": "london", "latitude": 51.5072, "longitude": -0.1276},
                    {"location_id": "tokyo", "latitude": 35.6762, "longitude": 139.6503},
                ]
            },
        ),
    ),
}
