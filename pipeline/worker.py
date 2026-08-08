"""Standalone worker entrypoint: runs the scheduler with no HTTP server.

In docker-compose this is the `worker` service; the `app` service runs only
`uvicorn app.main:app` with CONDUIT_RUN_SCHEDULER=false so jobs are
triggered exactly once. Run directly with `python -m pipeline.worker`.
"""

from __future__ import annotations

import asyncio
import logging
import signal

from pipeline.scheduler import build_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("conduit.worker")


async def main() -> None:
    scheduler = build_scheduler()
    scheduler.start()
    logger.info("worker_started")

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)

    await stop.wait()
    logger.info("worker_shutting_down")
    scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
