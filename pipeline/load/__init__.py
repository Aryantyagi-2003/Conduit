"""Generic load stage: builds a Postgres ON CONFLICT upsert from whatever
table/natural_key a source declares. Never touched when adding a new source.
"""

from __future__ import annotations

from typing import Any, cast

from pydantic import BaseModel
from sqlalchemy import CursorResult
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from pipeline.sources.base import Source


async def upsert(session: AsyncSession, source: Source, records: list[BaseModel]) -> int:
    """Idempotent load: INSERT ... ON CONFLICT (natural_key) DO UPDATE.

    Re-running this with the same records is a no-op change (rows are
    overwritten with identical values, not duplicated) — that's what the
    idempotency tests assert on row counts for.
    """
    if not records:
        return 0

    rows = [record.model_dump() for record in records]
    stmt = insert(source.table).values(rows)
    update_columns = {
        col.name: getattr(stmt.excluded, col.name)
        for col in source.table.columns
        if col.name not in source.natural_key and col.name != "id"
    }
    stmt = stmt.on_conflict_do_update(
        index_elements=list(source.natural_key),
        set_=update_columns,
    )
    result = cast(CursorResult[Any], await session.execute(stmt))
    await session.commit()
    return result.rowcount
