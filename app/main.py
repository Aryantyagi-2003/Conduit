from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import data, health, runs, sources
from pipeline.scheduler import build_scheduler

logging.basicConfig(level=logging.INFO)

# In docker-compose, the scheduler runs in the dedicated `worker` service
# (see pipeline/worker.py) so jobs aren't triggered twice. This flag lets
# `uvicorn app.main:app` still be self-contained for local development
# without needing a second process running.
RUN_SCHEDULER_IN_APP = os.environ.get("CONDUIT_RUN_SCHEDULER", "true").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    if RUN_SCHEDULER_IN_APP:
        scheduler = build_scheduler()
        scheduler.start()
        app.state.scheduler = scheduler
    yield
    if RUN_SCHEDULER_IN_APP:
        app.state.scheduler.shutdown()


app = FastAPI(title="Conduit", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(sources.router)
app.include_router(data.router)
app.include_router(runs.router)
