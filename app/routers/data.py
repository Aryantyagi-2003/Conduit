from __future__ import annotations

import csv
import datetime as dt
import io
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data_registry import get_table
from app.deps import get_session
from pipeline.registry import SOURCES

router = APIRouter(prefix="/api/data", tags=["data"])


def _require_source(source_id: str) -> None:
    if source_id not in SOURCES:
        raise HTTPException(status_code=404, detail=f"unknown source '{source_id}'")


async def _query_rows(
    session: AsyncSession,
    source_id: str,
    start: dt.datetime | None,
    end: dt.datetime | None,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    table = get_table(source_id)
    stmt = select(table)
    if start is not None:
        stmt = stmt.where(table.c.observed_at >= start)
    if end is not None:
        stmt = stmt.where(table.c.observed_at <= end)
    stmt = stmt.order_by(table.c.observed_at.desc()).limit(limit).offset(offset)

    result = await session.execute(stmt)
    return [
        {k: float(v) if isinstance(v, Decimal) else v for k, v in row._mapping.items()}
        for row in result
    ]


@router.get("/{source_id}")
async def get_data(
    source_id: str,
    start: dt.datetime | None = Query(default=None, description="ISO 8601, inclusive"),
    end: dt.datetime | None = Query(default=None, description="ISO 8601, inclusive"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    _require_source(source_id)
    return await _query_rows(session, source_id, start, end, limit, offset)


@router.get("/{source_id}/export.csv")
async def export_csv(
    source_id: str,
    start: dt.datetime | None = Query(default=None),
    end: dt.datetime | None = Query(default=None),
    limit: int = Query(default=5000, ge=1, le=50000),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    _require_source(source_id)
    rows = await _query_rows(session, source_id, start, end, limit, offset=0)

    buffer = io.StringIO()
    if rows:
        fieldnames = [k for k in rows[0] if k != "raw"]
        writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{source_id}.csv"'},
    )
