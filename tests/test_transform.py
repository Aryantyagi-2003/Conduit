from __future__ import annotations

import datetime as dt

from pipeline.sources.base import SourceConfig
from pipeline.transform import normalize
from tests.dummy_source import DummySource

RUN_SLOT = dt.datetime(2026, 8, 8, 19, 0, tzinfo=dt.UTC)


def make_record(location_id="new_york", temperature_c=30.0, observed_at=RUN_SLOT):
    return {
        "location_id": location_id,
        "observed_at": observed_at.isoformat(),
        "temperature_c": temperature_c,
        "humidity_pct": 50.0,
        "wind_speed_ms": 3.0,
        "raw": {},
        "fetched_at": RUN_SLOT.isoformat(),
    }


def test_normalize_drops_records_that_fail_validation_but_keeps_valid_ones():
    valid = make_record()
    invalid = make_record(location_id="london")
    del invalid["temperature_c"]  # required field missing -> ValidationError

    source = DummySource(SourceConfig(source_id="dummy_weather", interval_seconds=900), batches=[])
    result = normalize(source, [valid, invalid], RUN_SLOT)

    assert len(result) == 1
    assert result[0].location_id == "new_york"


def test_normalize_dedupes_by_natural_key_last_write_wins():
    first = make_record(location_id="new_york", temperature_c=20.0)
    second = make_record(location_id="new_york", temperature_c=25.0)  # same natural key

    source = DummySource(SourceConfig(source_id="dummy_weather", interval_seconds=900), batches=[])
    result = normalize(source, [first, second], RUN_SLOT)

    assert len(result) == 1
    assert result[0].temperature_c == 25.0


def test_normalize_keeps_records_with_distinct_natural_keys():
    ny = make_record(location_id="new_york")
    london = make_record(location_id="london")

    source = DummySource(SourceConfig(source_id="dummy_weather", interval_seconds=900), batches=[])
    result = normalize(source, [ny, london], RUN_SLOT)

    assert {r.location_id for r in result} == {"new_york", "london"}
