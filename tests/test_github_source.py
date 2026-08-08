from __future__ import annotations

import datetime as dt

from pipeline.sources.base import SourceConfig
from pipeline.sources.github import GithubSource

RUN_SLOT = dt.datetime(2026, 8, 8, 20, 0, tzinfo=dt.UTC)

# Captured from a real GitHub API response (see scripts/demo_github_extract.py).
SAMPLE_RAW = {
    "repo": "torvalds/linux",
    "data": {
        "full_name": "torvalds/linux",
        "stargazers_count": 242211,
        "open_issues_count": 3,
        "forks_count": 63822,
        "language": "C",
    },
}


def make_source() -> GithubSource:
    return GithubSource(
        SourceConfig(source_id="github", interval_seconds=1800, extra={"repos": ["torvalds/linux"]})
    )


def test_parse_maps_github_fields_to_record():
    record = make_source().parse(SAMPLE_RAW, RUN_SLOT)
    assert record.repo_full_name == "torvalds/linux"
    assert record.stars == 242211
    assert record.language == "C"


def test_parse_uses_run_slot_not_a_response_timestamp():
    """The key divergence from weather/crypto: GitHub's API has no history,
    so observed_at MUST come from the scheduler's run_slot, not the payload
    (there is no usable timestamp in the payload at all) -- otherwise a
    retry within the same scheduled run would insert a duplicate row
    instead of updating the existing one.
    """
    record = make_source().parse(SAMPLE_RAW, RUN_SLOT)
    assert record.observed_at == RUN_SLOT

    later_slot = RUN_SLOT + dt.timedelta(minutes=30)
    record_later = make_source().parse(SAMPLE_RAW, later_slot)
    assert record_later.observed_at == later_slot


def test_parse_allows_missing_language():
    raw = {**SAMPLE_RAW, "data": {**SAMPLE_RAW["data"], "language": None}}
    record = make_source().parse(raw, RUN_SLOT)
    assert record.language is None
