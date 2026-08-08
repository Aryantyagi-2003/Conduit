"""GitHub public repo stats source. No token required for public read
endpoints (rate limit: 60 req/hour unauthenticated).

Docs: https://docs.github.com/en/rest/repos/repos

Shape: categorical + numeric snapshot -- deliberately NOT another
time-series-of-measurements source like weather/crypto. This is the source
that stress-tests the interface: GitHub's API has no history endpoint for
star/issue counts, it only ever returns the current live values. That
matters for idempotency: unlike weather/crypto, there is no upstream
timestamp to key on, so `observed_at` here is the scheduler's `run_slot`
(see pipeline/time_utils.truncate_to_interval), not anything from the
response body. A retry of the same scheduled run reuses the same run_slot
-> same natural key -> updates the row instead of duplicating it.

GitHub also signals rate limiting differently than weather/crypto: instead
of a 429, an exhausted unauthenticated quota comes back as 403 with
X-RateLimit-Remaining: 0 and an X-RateLimit-Reset unix-epoch header. Both
paths are normalized to the same RateLimited exception here.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, ClassVar, cast

import httpx
from pydantic import BaseModel
from sqlalchemy import Table

from pipeline.models import GithubRepoStat
from pipeline.retry import ExtractionError, RateLimited, with_backoff
from pipeline.sources.base import SourceConfig

GITHUB_API_URL = "https://api.github.com/repos/{full_name}"


class GithubRepoRecord(BaseModel):
    repo_full_name: str
    observed_at: dt.datetime
    stars: int
    open_issues: int
    forks: int
    language: str | None
    raw: dict[str, Any]
    fetched_at: dt.datetime


class GithubSource:
    source_id: ClassVar[str] = "github"
    record_model: ClassVar[type[BaseModel]] = GithubRepoRecord
    table: ClassVar[Table] = cast(Table, GithubRepoStat.__table__)
    natural_key: ClassVar[tuple[str, ...]] = ("repo_full_name", "observed_at")

    def __init__(self, config: SourceConfig):
        self.config = config
        self.repos: list[str] = config.extra["repos"]
        self._client = httpx.AsyncClient(
            timeout=10.0, headers={"Accept": "application/vnd.github+json"}
        )

    @with_backoff(max_attempts=5, base_delay=2.0, max_delay=60.0)
    async def extract(self, run_slot: dt.datetime) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for repo in self.repos:
            resp = await self._client.get(GITHUB_API_URL.format(full_name=repo))
            if resp.status_code == 429 or (
                resp.status_code == 403 and resp.headers.get("X-RateLimit-Remaining") == "0"
            ):
                reset_at = resp.headers.get("X-RateLimit-Reset")
                retry_after = (
                    float(reset_at) - dt.datetime.now(dt.UTC).timestamp() if reset_at else None
                )
                raise RateLimited(
                    f"github rate limited for {repo}",
                    retry_after=max(retry_after, 0) if retry_after is not None else None,
                )
            if resp.status_code >= 500:
                raise ExtractionError(f"github {resp.status_code} for {repo}")
            resp.raise_for_status()
            results.append({"repo": repo, "data": resp.json()})
        return results

    def parse(self, raw: dict[str, Any], run_slot: dt.datetime) -> GithubRepoRecord:
        data = raw["data"]
        return GithubRepoRecord(
            repo_full_name=data["full_name"],
            observed_at=run_slot,
            stars=data["stargazers_count"],
            open_issues=data["open_issues_count"],
            forks=data["forks_count"],
            language=data.get("language"),
            raw=data,
            fetched_at=dt.datetime.now(dt.UTC),
        )
