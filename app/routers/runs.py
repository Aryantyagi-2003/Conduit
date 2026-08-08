from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_session
from app.schemas import JobRunOut
from pipeline.models import JobRun

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.get("", response_model=list[JobRunOut])
async def list_runs(
    source_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[JobRun]:
    stmt = select(JobRun)
    if source_id is not None:
        stmt = stmt.where(JobRun.source_id == source_id)
    if status is not None:
        stmt = stmt.where(JobRun.status == status)
    stmt = stmt.order_by(JobRun.started_at.desc()).limit(limit).offset(offset)

    result = await session.execute(stmt)
    return list(result.scalars().all())
