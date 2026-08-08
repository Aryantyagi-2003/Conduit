from __future__ import annotations

from pipeline.freshness import classify


def test_classify_fresh_within_interval():
    assert classify(staleness_seconds=100, interval_seconds=900) == "fresh"
    assert classify(staleness_seconds=900, interval_seconds=900) == "fresh"


def test_classify_stale_between_one_and_three_intervals():
    assert classify(staleness_seconds=901, interval_seconds=900) == "stale"
    assert classify(staleness_seconds=2700, interval_seconds=900) == "stale"


def test_classify_critical_beyond_three_intervals():
    assert classify(staleness_seconds=2701, interval_seconds=900) == "critical"


def test_classify_critical_when_never_succeeded():
    assert classify(staleness_seconds=None, interval_seconds=900) == "critical"
