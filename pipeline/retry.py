"""Shared retry/backoff decorator used by every Source's extract() call.

Kept separate from any one source so its behavior (delay sequence, jitter,
handling of 429 Retry-After) is independently testable with a fake clock and
a scripted failure sequence, rather than re-implemented per source.
"""

from __future__ import annotations

import asyncio
import functools
import logging
import random
from collections.abc import Awaitable, Callable, Coroutine
from typing import Any, ParamSpec, TypeVar

logger = logging.getLogger("conduit.retry")

P = ParamSpec("P")
T = TypeVar("T")


class RateLimited(Exception):
    """Raised by an extractor when the upstream API returns 429.

    retry_after: seconds the server told us to wait (from a Retry-After
    header), if provided. When absent, the decorator falls back to normal
    exponential backoff.
    """

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class ExtractionError(Exception):
    """Raised by an extractor for any other retryable failure (timeout, 5xx)."""


def compute_delay(
    attempt: int,
    base_delay: float,
    max_delay: float,
    retry_after: float | None = None,
    jitter: float = 0.0,
) -> float:
    """Pure function so backoff behavior is unit-testable without sleeping.

    attempt is 1-indexed (this is the delay before attempt number `attempt + 1`).
    """
    if retry_after is not None:
        return min(retry_after, max_delay)
    delay: float = min(base_delay * (2 ** (attempt - 1)), max_delay)
    if jitter:
        delay += random.uniform(0, jitter * delay)
    return delay


def with_backoff(
    max_attempts: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: float = 0.1,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> Callable[[Callable[P, Coroutine[Any, Any, T]]], Callable[P, Coroutine[Any, Any, T]]]:
    """Decorator: retry an async extractor with exponential backoff.

    `sleep` is injectable so tests can assert the delay sequence without
    real waiting (see tests/test_retry.py).
    """

    def decorator(fn: Callable[P, Coroutine[Any, Any, T]]) -> Callable[P, Coroutine[Any, Any, T]]:
        @functools.wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await fn(*args, **kwargs)
                except RateLimited as exc:
                    last_exc = exc
                    delay = compute_delay(
                        attempt, base_delay, max_delay, retry_after=exc.retry_after, jitter=jitter
                    )
                    logger.warning(
                        "rate_limited",
                        extra={"attempt": attempt, "delay": delay, "max_attempts": max_attempts},
                    )
                except ExtractionError as exc:
                    last_exc = exc
                    delay = compute_delay(attempt, base_delay, max_delay, jitter=jitter)
                    logger.warning(
                        "extraction_retry",
                        extra={
                            "attempt": attempt,
                            "delay": delay,
                            "max_attempts": max_attempts,
                            "error": str(exc),
                        },
                    )
                if attempt < max_attempts:
                    await sleep(delay)
            assert last_exc is not None
            raise last_exc

        return wrapper

    return decorator
