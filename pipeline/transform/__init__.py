"""Generic transform stage: shared by every source. Never touched when
adding a new source — all per-source logic lives in that source's parse().
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from pydantic import BaseModel, ValidationError

from pipeline.sources.base import Source

logger = logging.getLogger("conduit.transform")


def normalize(
    source: Source, raw_records: list[dict[str, Any]], run_slot: dt.datetime
) -> list[BaseModel]:
    """Parse raw records into source.record_model instances, dropping and
    logging any that fail validation, then dedupe by natural_key (last
    write wins) so a single batch never sends Postgres two rows sharing an
    ON CONFLICT target — that raises "ON CONFLICT DO UPDATE command cannot
    affect row a second time".
    """
    parsed: dict[tuple[Any, ...], BaseModel] = {}
    for raw in raw_records:
        try:
            record = source.parse(raw, run_slot)
        except ValidationError as exc:
            logger.warning(
                "record_validation_failed",
                extra={"source_id": source.source_id, "raw": raw, "error": str(exc)},
            )
            continue
        key = tuple(getattr(record, field) for field in source.natural_key)
        parsed[key] = record
    return list(parsed.values())
