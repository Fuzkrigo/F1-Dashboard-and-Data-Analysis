"""
Database Configuration Module.

[EN] Configures the async database engine and session for the F1 Insights
application. Supports both SQLite (for local development) and PostgreSQL
(for production/Docker). Provides the base class for ORM models and a
dependency-injection-ready session generator.

[PT-BR] Configura o engine e a sessão assíncrona do banco de dados para a
aplicação F1 Insights. Suporta tanto SQLite (para desenvolvimento local)
quanto PostgreSQL (para produção/Docker). Fornece a classe base para os
modelos ORM e um gerador de sessão pronto para injeção de dependência.

Author: Bruno Krieger
"""

import logging
import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

logger = logging.getLogger(__name__)

# Check if we should use SQLite (default for local non-docker execution)
USE_SQLITE = os.getenv("USE_SQLITE", "True").lower() == "true"

if USE_SQLITE:
    DATABASE_URL = "sqlite+aiosqlite:///./f1_insights.db"
    logger.info("Using SQLite database")
else:
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "f1_insights")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{DB_PORT}/{POSTGRES_DB}"
    logger.info(f"Using PostgreSQL database at {DB_HOST}:{DB_PORT}")

engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """
    Declarative base class for all ORM models.

    [EN] All database models must inherit from this class so that
    SQLAlchemy can track and manage their table metadata.

    [PT-BR] Todos os modelos do banco de dados devem herdar desta
    classe para que o SQLAlchemy possa rastrear e gerenciar seus
    metadados de tabela.

    Author: Bruno Krieger
    """

    pass


async def get_db():
    """
    Async generator that yields a database session.

    [EN] Creates an async database session and yields it for use in
    FastAPI dependency injection. The session is automatically closed
    when the request finishes.

    [PT-BR] Cria uma sessão assíncrona do banco de dados e a disponibiliza
    para uso na injeção de dependência do FastAPI. A sessão é automaticamente
    fechada quando a requisição termina.

    Yields:
        AsyncSession: An active async database session.
                      Uma sessão assíncrona ativa do banco de dados.

    Author: Bruno Krieger
    """
    async with AsyncSessionLocal() as session:
        yield session
