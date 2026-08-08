"""API tests use ASGITransport directly (no lifespan), so the scheduler
never starts and no real network calls happen -- only the DB dependency is
exercised, overridden to point at the test session fixture.
"""

from __future__ import annotations

import httpx
import pytest

from app.deps import get_session
from app.main import app


@pytest.fixture
def client(session):
    async def _override_session():
        yield session

    app.dependency_overrides[get_session] = _override_session
    yield httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_reports_database_ok(client):
    async with client as c:
        resp = await c.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "database": "ok"}


@pytest.mark.asyncio
async def test_data_endpoint_404s_for_unknown_source(client):
    async with client as c:
        resp = await c.get("/api/data/not_a_real_source")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_sources_endpoint_lists_all_registered_sources(client):
    async with client as c:
        resp = await c.get("/api/sources")
    assert resp.status_code == 200
    source_ids = {s["source_id"] for s in resp.json()}
    assert source_ids == {"weather", "crypto", "github"}
    # no job_runs in the empty test DB -> nothing has ever succeeded
    assert all(s["freshness_status"] == "critical" for s in resp.json())


@pytest.mark.asyncio
async def test_runs_endpoint_empty_on_fresh_db(client):
    async with client as c:
        resp = await c.get("/api/runs")
    assert resp.status_code == 200
    assert resp.json() == []
