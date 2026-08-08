"""API-side view of pipeline.registry.SOURCES: the table/columns to query
per source_id. Reuses the same Source classes -- adding a new source to
pipeline/registry.py automatically makes it queryable here too, no
duplicate registration.
"""

from __future__ import annotations

from typing import Any, cast

from sqlalchemy import Table

from pipeline.registry import SOURCES


def get_table(source_id: str) -> Table:
    source_cls, _config = SOURCES[source_id]
    return cast(Table, cast(Any, source_cls).table)


def get_interval_seconds(source_id: str) -> int:
    _source_cls, config = SOURCES[source_id]
    return config.interval_seconds
