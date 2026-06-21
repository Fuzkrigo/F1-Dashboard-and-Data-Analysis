"""
Tests for the database configuration module.

[EN] Verifies both database URL branches (SQLite default and PostgreSQL via
env vars) plus the get_db dependency-injection generator. Uses module
reload + monkeypatch to safely toggle USE_SQLITE without affecting other
tests. The original module state is always restored at the end of each
test via a fixture.

[PT-BR] Verifica os dois ramos de configuração de URL (SQLite padrão e
PostgreSQL via variáveis de ambiente) e o gerador get_db de injeção de
dependência. Usa reload de módulo + monkeypatch para alternar USE_SQLITE
de forma segura sem afetar outros testes. O estado original do módulo é
sempre restaurado ao final de cada teste via fixture.
"""

import importlib
from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession


@pytest.fixture
def restore_database_module():
    """
    Always reload `src.db.database` with the SQLite default after the test.

    [EN] Ensures that any monkeypatched env or mocked engine inside a test
    doesn't leak to subsequent tests that depend on the real SQLite engine.
    [PT-BR] Garante que qualquer monkeypatch de env ou engine mockado num
    teste não vaze para testes seguintes que dependem do engine SQLite real.
    """
    import os

    yield
    # Force-restore SQLite default state
    os.environ["USE_SQLITE"] = "True"
    import src.db.database as db_module

    importlib.reload(db_module)


def _capture_url_with_fake_engine(monkeypatch):
    """Patches create_async_engine to capture the URL and return a usable
    AsyncEngine mock that won't break async_sessionmaker validation."""
    captured = {}
    fake_engine = MagicMock(spec=AsyncEngine)

    def fake_create(url, **kwargs):
        captured["url"] = url
        return fake_engine

    monkeypatch.setattr(
        "sqlalchemy.ext.asyncio.create_async_engine", fake_create
    )
    return captured


# ─────────────────────────────────────────────────────────────────────────────
# Connection string assembly
# ─────────────────────────────────────────────────────────────────────────────


def test_sqlite_branch_default(monkeypatch, restore_database_module):
    """USE_SQLITE=True (default) yields the SQLite aiosqlite URL."""
    monkeypatch.setenv("USE_SQLITE", "True")
    captured = _capture_url_with_fake_engine(monkeypatch)

    import src.db.database as db_module

    importlib.reload(db_module)

    assert captured["url"].startswith("sqlite+aiosqlite:///")
    assert db_module.USE_SQLITE is True


def test_postgres_branch_with_env_vars(monkeypatch, restore_database_module):
    """USE_SQLITE=False composes the asyncpg PostgreSQL URL from env vars."""
    monkeypatch.setenv("USE_SQLITE", "False")
    monkeypatch.setenv("POSTGRES_USER", "test_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test_pass")
    monkeypatch.setenv("POSTGRES_DB", "test_db")
    monkeypatch.setenv("DB_HOST", "test-host")
    monkeypatch.setenv("DB_PORT", "5433")

    captured = _capture_url_with_fake_engine(monkeypatch)

    import src.db.database as db_module

    importlib.reload(db_module)

    assert captured["url"] == (
        "postgresql+asyncpg://test_user:test_pass@test-host:5433/test_db"
    )
    assert db_module.USE_SQLITE is False


def test_postgres_branch_uses_defaults_when_env_missing(
    monkeypatch, restore_database_module
):
    """USE_SQLITE=False without env vars falls back to documented defaults."""
    # Disable load_dotenv at its source so importlib.reload's `from dotenv
    # import load_dotenv` picks up the no-op version too.
    # Desabilita load_dotenv na origem para que o reload pegue o no-op.
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **kw: None)

    monkeypatch.setenv("USE_SQLITE", "False")
    monkeypatch.delenv("POSTGRES_USER", raising=False)
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
    monkeypatch.delenv("POSTGRES_DB", raising=False)
    monkeypatch.delenv("DB_HOST", raising=False)
    monkeypatch.delenv("DB_PORT", raising=False)

    captured = _capture_url_with_fake_engine(monkeypatch)

    import src.db.database as db_module

    importlib.reload(db_module)

    assert (
        captured["url"]
        == "postgresql+asyncpg://postgres:postgres@localhost:5432/f1_insights"
    )


# ─────────────────────────────────────────────────────────────────────────────
# get_db dependency-injection generator
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_db_yields_async_session():
    """get_db must yield an active AsyncSession that closes on exit."""
    from src.db.database import get_db

    gen = get_db()
    session = await gen.__anext__()
    try:
        assert isinstance(session, AsyncSession)
    finally:
        # Closing the generator triggers the `async with` teardown
        with pytest.raises(StopAsyncIteration):
            await gen.__anext__()
