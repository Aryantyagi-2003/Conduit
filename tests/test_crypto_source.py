from __future__ import annotations

import datetime as dt
from unittest.mock import AsyncMock

import httpx
import pytest

from pipeline.retry import RateLimited
from pipeline.sources.base import SourceConfig
from pipeline.sources.crypto import CryptoSource

RUN_SLOT = dt.datetime(2026, 8, 8, 20, 0, tzinfo=dt.UTC)

# Captured from a real CoinGecko response (see scripts/demo_crypto_extract.py).
SAMPLE_RAW = {
    "coin_id": "bitcoin",
    "symbol": "BTC",
    "data": {
        "usd": 65029,
        "usd_market_cap": 1304976895065.25,
        "usd_24h_vol": 12428180617.20873,
        "last_updated_at": 1786219550,
    },
}


def make_source() -> CryptoSource:
    return CryptoSource(
        SourceConfig(source_id="crypto", interval_seconds=120, extra={"assets": {"bitcoin": "BTC"}})
    )


def test_parse_maps_coingecko_fields_to_record():
    record = make_source().parse(SAMPLE_RAW, RUN_SLOT)
    assert record.asset_symbol == "BTC"
    assert record.price_usd == 65029
    assert record.market_cap == pytest.approx(1304976895065.25)


def test_parse_uses_coingecko_last_updated_at_not_run_slot():
    different_run_slot = RUN_SLOT + dt.timedelta(hours=5)
    record = make_source().parse(SAMPLE_RAW, different_run_slot)
    assert record.observed_at == dt.datetime.fromtimestamp(1786219550, tz=dt.UTC)


@pytest.mark.asyncio
async def test_extract_raises_rate_limited_on_429_with_retry_after_header():
    """The rate-limit-awareness requirement, made concrete: a 429 must
    surface as RateLimited carrying the server's Retry-After value, not
    crash the job. @with_backoff (tested separately) is what actually
    sleeps and retries on this exception.
    """
    source = make_source()
    fake_response = httpx.Response(429, headers={"Retry-After": "12"}, request=httpx.Request("GET", "https://x"))
    source._client.get = AsyncMock(return_value=fake_response)  # type: ignore[method-assign]

    # bypass the @with_backoff wrapper on extract to observe the raw failure
    with pytest.raises(RateLimited) as exc_info:
        await source.extract.__wrapped__(source, RUN_SLOT)

    assert exc_info.value.retry_after == 12.0
