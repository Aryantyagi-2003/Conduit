"""CoinGecko crypto source. No API key required (public /simple/price endpoint).

Docs: https://docs.coingecko.com/reference/simple-price

Shape: time-series, numeric, like weather -- but different units (USD price
vs. degrees C) and a different upstream schema (flat dict keyed by coin id,
not a nested "current" block). CoinGecko's free tier is also genuinely
rate-limited in practice (roughly 10-30 req/min), which makes it the
natural source to exercise the 429-handling path for real rather than only
in a unit test.

`observed_at` uses CoinGecko's own `last_updated_at` (a real upstream unix
timestamp), same reasoning as weather: the API supplies real history, so
retries land on the same natural key without needing run_slot.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, ClassVar, cast

import httpx
from pydantic import BaseModel, Field
from sqlalchemy import Table

from pipeline.models import CryptoPrice
from pipeline.retry import ExtractionError, RateLimited, with_backoff
from pipeline.sources.base import SourceConfig

COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"


class CryptoRecord(BaseModel):
    asset_symbol: str
    observed_at: dt.datetime
    price_usd: float = Field(ge=0)
    volume_24h: float | None = Field(default=None, ge=0)
    market_cap: float | None = Field(default=None, ge=0)
    raw: dict[str, Any]
    fetched_at: dt.datetime


class CryptoSource:
    source_id: ClassVar[str] = "crypto"
    record_model: ClassVar[type[BaseModel]] = CryptoRecord
    table: ClassVar[Table] = cast(Table, CryptoPrice.__table__)
    natural_key: ClassVar[tuple[str, ...]] = ("asset_symbol", "observed_at")

    def __init__(self, config: SourceConfig):
        self.config = config
        # maps CoinGecko's coin id (used in the API call) to our display symbol
        self.assets: dict[str, str] = config.extra["assets"]
        self._client = httpx.AsyncClient(timeout=10.0)

    @with_backoff(max_attempts=5, base_delay=2.0, max_delay=60.0)
    async def extract(self, run_slot: dt.datetime) -> list[dict[str, Any]]:
        resp = await self._client.get(
            COINGECKO_URL,
            params={
                "ids": ",".join(self.assets.keys()),
                "vs_currencies": "usd",
                "include_market_cap": "true",
                "include_24hr_vol": "true",
                "include_last_updated_at": "true",
            },
        )
        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After")
            raise RateLimited(
                "coingecko rate limited", retry_after=float(retry_after) if retry_after else None
            )
        if resp.status_code >= 500:
            raise ExtractionError(f"coingecko {resp.status_code}")
        resp.raise_for_status()
        body = resp.json()
        return [
            {"coin_id": coin_id, "symbol": symbol, "data": body[coin_id]}
            for coin_id, symbol in self.assets.items()
            if coin_id in body
        ]

    def parse(self, raw: dict[str, Any], run_slot: dt.datetime) -> CryptoRecord:
        data = raw["data"]
        return CryptoRecord(
            asset_symbol=raw["symbol"],
            observed_at=dt.datetime.fromtimestamp(data["last_updated_at"], tz=dt.UTC),
            price_usd=data["usd"],
            volume_24h=data.get("usd_24h_vol"),
            market_cap=data.get("usd_market_cap"),
            raw=data,
            fetched_at=dt.datetime.now(dt.UTC),
        )
