from __future__ import annotations

import pytest

from pipeline.retry import ExtractionError, RateLimited, compute_delay, with_backoff


def test_compute_delay_exponential_growth():
    delays = [compute_delay(attempt, base_delay=1.0, max_delay=60.0) for attempt in range(1, 6)]
    assert delays == [1.0, 2.0, 4.0, 8.0, 16.0]


def test_compute_delay_caps_at_max_delay():
    assert compute_delay(10, base_delay=1.0, max_delay=5.0) == 5.0


def test_compute_delay_honors_retry_after_header():
    assert compute_delay(1, base_delay=1.0, max_delay=60.0, retry_after=17.0) == 17.0


def test_compute_delay_retry_after_still_capped_at_max_delay():
    assert compute_delay(1, base_delay=1.0, max_delay=10.0, retry_after=999.0) == 10.0


@pytest.mark.asyncio
async def test_with_backoff_retries_then_succeeds_and_records_delay_sequence():
    recorded_sleeps: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        recorded_sleeps.append(seconds)

    call_count = 0

    @with_backoff(max_attempts=4, base_delay=1.0, max_delay=60.0, jitter=0.0, sleep=fake_sleep)
    async def flaky() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ExtractionError("transient failure")
        return "ok"

    result = await flaky()

    assert result == "ok"
    assert call_count == 3
    # two failures before success -> two backoff sleeps, exponential: 1s, 2s
    assert recorded_sleeps == [1.0, 2.0]


@pytest.mark.asyncio
async def test_with_backoff_exhausts_attempts_and_raises_last_error():
    async def fake_sleep(seconds: float) -> None:
        return None

    @with_backoff(max_attempts=3, base_delay=1.0, max_delay=60.0, jitter=0.0, sleep=fake_sleep)
    async def always_fails() -> None:
        raise ExtractionError("permanent failure")

    with pytest.raises(ExtractionError, match="permanent failure"):
        await always_fails()


@pytest.mark.asyncio
async def test_with_backoff_honors_rate_limited_retry_after():
    recorded_sleeps: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        recorded_sleeps.append(seconds)

    call_count = 0

    @with_backoff(max_attempts=2, base_delay=1.0, max_delay=60.0, jitter=0.0, sleep=fake_sleep)
    async def rate_limited_once() -> str:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RateLimited("429", retry_after=5.0)
        return "ok"

    result = await rate_limited_once()

    assert result == "ok"
    assert recorded_sleeps == [5.0]
