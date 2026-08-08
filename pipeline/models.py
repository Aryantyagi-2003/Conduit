"""SQLAlchemy 2.0 ORM models. Each data-source table plus job_runs.

raw jsonb is kept on every source table deliberately: it's the original,
unmodified API payload for that row, so a bad transform can be debugged or
replayed without re-hitting the upstream API. At larger scale you'd age raw
out to cold/object storage (S3 + a TTL) after N days instead of keeping it
in the hot table indefinitely, since it dominates row size and is rarely
read after the first debugging pass.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import BigInteger, DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, NUMERIC
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class WeatherObservation(Base):
    __tablename__ = "weather_observations"
    __table_args__ = (
        UniqueConstraint("location_id", "observed_at", name="uq_weather_natural_key"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    location_id: Mapped[str] = mapped_column(String, nullable=False)
    observed_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    temperature_c: Mapped[float | None] = mapped_column(NUMERIC)
    humidity_pct: Mapped[float | None] = mapped_column(NUMERIC)
    wind_speed_ms: Mapped[float | None] = mapped_column(NUMERIC)
    raw: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    fetched_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


Index("ix_weather_observations_observed_at", WeatherObservation.observed_at)


class CryptoPrice(Base):
    __tablename__ = "crypto_prices"
    __table_args__ = (
        UniqueConstraint("asset_symbol", "observed_at", name="uq_crypto_natural_key"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    asset_symbol: Mapped[str] = mapped_column(String, nullable=False)
    observed_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    price_usd: Mapped[float] = mapped_column(NUMERIC, nullable=False)
    volume_24h: Mapped[float | None] = mapped_column(NUMERIC)
    market_cap: Mapped[float | None] = mapped_column(NUMERIC)
    raw: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    fetched_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


Index("ix_crypto_prices_observed_at", CryptoPrice.observed_at)


class GithubRepoStat(Base):
    __tablename__ = "github_repo_stats"
    __table_args__ = (
        UniqueConstraint("repo_full_name", "observed_at", name="uq_github_natural_key"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    repo_full_name: Mapped[str] = mapped_column(String, nullable=False)
    observed_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    stars: Mapped[int | None] = mapped_column(Integer)
    open_issues: Mapped[int | None] = mapped_column(Integer)
    forks: Mapped[int | None] = mapped_column(Integer)
    language: Mapped[str | None] = mapped_column(String)
    raw: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    fetched_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)


Index("ix_github_repo_stats_observed_at", GithubRepoStat.observed_at)


class JobRun(Base):
    __tablename__ = "job_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(String, nullable=False)
    scheduled_for: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    started_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String, nullable=False)  # running|success|failed|partial
    rows_extracted: Mapped[int | None] = mapped_column(Integer)
    rows_loaded: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)


Index("ix_job_runs_source_started", JobRun.source_id, JobRun.started_at.desc())
