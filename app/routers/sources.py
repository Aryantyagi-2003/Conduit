from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_session
from app.schemas import SourceOut
from pipeline.freshness import get_source_freshness
from pipeline.registry import SOURCES

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("", response_model=list[SourceOut])
async def list_sources(session: AsyncSession = Depends(get_session)) -> list[SourceOut]:
    out = []
    for source_id, (_source_cls, config) in SOURCES.items():
        fresh = await get_source_freshness(session, source_id, config.interval_seconds)
        out.append(
            SourceOut(
                source_id=source_id,
                interval_seconds=config.interval_seconds,
                enabled=config.enabled,
                freshness_status=fresh.status,
                last_success_at=fresh.last_success_at,
                staleness_seconds=fresh.staleness_seconds,
            )
        )
    return out
