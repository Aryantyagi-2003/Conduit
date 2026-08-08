"""The pluggable Source interface. Every data source implements this Protocol
and nothing else — transform and load stages are generic and operate purely
off the ClassVars declared here (record_model, table, natural_key), so
adding a new source never requires touching pipeline/transform or pipeline/load.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar, Protocol, runtime_checkable

from pydantic import BaseModel
from sqlalchemy import Table


class SourceConfig(BaseModel):
    source_id: str
    interval_seconds: int
    enabled: bool = True
    extra: dict[str, Any] = {}


@runtime_checkable
class Source(Protocol):
    source_id: ClassVar[str]
    record_model: ClassVar[type[BaseModel]]
    table: ClassVar[Table]
    natural_key: ClassVar[tuple[str, ...]]

    config: SourceConfig

    def __init__(self, config: SourceConfig) -> None: ...

    async def extract(self, run_slot: datetime) -> list[dict[str, Any]]:
        """Fetch raw records from the upstream API for this run.

        `run_slot` is the scheduler's logical trigger time for this job
        (truncated to the source's interval), not wall-clock now. Sources
        whose upstream API returns real historical timestamps should use
        those; sources that only expose a live snapshot (no history) must
        stamp `observed_at` with `run_slot` in parse() so retries of the
        same scheduled run overwrite rather than duplicate.

        Must raise pipeline.retry.RateLimited or ExtractionError on
        recoverable failures — callers wrap this in @with_backoff.
        """
        ...

    def parse(self, raw: dict[str, Any], run_slot: datetime) -> BaseModel:
        """Map one raw API record to `record_model`. Raises pydantic.ValidationError
        on malformed input; the transform stage catches and logs these per-record
        rather than failing the whole batch.
        """
        ...
