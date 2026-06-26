"""
Tests for the TelemetryCache ORM model.

[EN] Verifies the telemetry memoization table: it persists and round-trips a
JSON payload, auto-populates the timestamps, and enforces cache_key uniqueness.
Runs against an isolated in-memory SQLite database (no real DB is touched).

[PT-BR] Verifica a tabela de memoization da telemetria: persiste e recupera um
payload JSON, preenche os timestamps automaticamente e garante a unicidade do
cache_key. Roda contra um SQLite em memória isolado (nenhum banco real é tocado).

Author: Bruno Krieger
"""

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.db.database import Base
from src.db.models import TelemetryCache

# [EN] pytest injects fixtures by matching the parameter name to the fixture
# name, so the `session` test parameters intentionally shadow the fixture below.
# That is idiomatic pytest, not a real bug, so silence pylint's W0621.
# [PT-BR] O pytest injeta fixtures casando o nome do parâmetro com o da fixture,
# então o parâmetro `session` sombreia a fixture de propósito. É o padrão do
# pytest, não um bug, então silenciamos o W0621 do pylint.
# pylint: disable=redefined-outer-name


@pytest_asyncio.fixture
async def session():
    """In-memory SQLite session with all tables created."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


@pytest.mark.asyncio
async def test_persists_and_round_trips_payload(session):
    """A cached payload is stored and read back intact, with timestamps set."""
    payload = {"drivers": {"VER": {"lap_chart": {"lap_number": [1, 2, 3]}}}}
    session.add(
        TelemetryCache(cache_key="telemetry:2023:15:R:VER", payload=payload)
    )
    await session.commit()

    row = (
        await session.execute(
            select(TelemetryCache).where(
                TelemetryCache.cache_key == "telemetry:2023:15:R:VER"
            )
        )
    ).scalar_one()

    assert row.payload == payload
    assert row.created_at is not None
    assert row.last_accessed_at is not None


@pytest.mark.asyncio
async def test_cache_key_must_be_unique(session):
    """Inserting two rows with the same cache_key violates the unique index."""
    session.add(TelemetryCache(cache_key="dup", payload={}))
    await session.commit()

    session.add(TelemetryCache(cache_key="dup", payload={}))
    with pytest.raises(IntegrityError):
        await session.commit()
