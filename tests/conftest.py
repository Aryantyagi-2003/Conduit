"""Tests run against a real Postgres database (conduit_test), not sqlite or
mocks — ON CONFLICT DO UPDATE is Postgres-specific dialect syntax, so the
generic load stage has to be exercised against the real thing to mean
anything. Create the DB once with:

    createdb -h /tmp -p 5433 -U conduit conduit_test
"""

from __future__ import annotations

import os

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from pipeline.models import Base

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://conduit@localhost:5433/conduit_test"
)


@pytest_asyncio.fixture
async def engine():
    # Function-scoped (not session-scoped): asyncpg connections are bound to
    # the event loop they were created on, and pytest-asyncio spins up a new
    # loop per test by default, so a shared engine across tests raises
    # "another operation is in progress" from a stale loop binding.
    eng = create_async_engine(TEST_DATABASE_URL)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine):
    session_local = async_sessionmaker(engine, expire_on_commit=False)
    async with session_local() as s:
        yield s
