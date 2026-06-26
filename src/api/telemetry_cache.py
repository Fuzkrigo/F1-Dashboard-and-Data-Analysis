"""
Telemetry response cache (memoization in Postgres/Supabase).

[EN] Stores the JSON response already computed from FastF1, keyed by a
deterministic cache_key, so repeat requests are served from the database
instead of re-downloading and re-processing telemetry (slow and memory-heavy).
All DB access is best-effort: any failure degrades to a cache miss / no-op so
the telemetry endpoints keep working even if the cache is down.

[PT-BR] Guarda a resposta JSON ja computada do FastF1, indexada por um
cache_key deterministico, para que requisicoes repetidas sejam servidas do
banco em vez de re-baixar e re-processar a telemetria (lento e pesado de
memoria). Todo acesso ao banco e best-effort: qualquer falha degrada para
cache miss / no-op, entao os endpoints seguem funcionando mesmo com o cache
fora do ar.

Author: Bruno Krieger
"""

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import TelemetryCache

logger = logging.getLogger(__name__)

# [EN] This module is a best-effort cache boundary: any DB/serialization error
# must degrade to a miss/no-op (the caller recomputes) instead of breaking
# telemetry, so the broad excepts below are intentional — and always logged.
# [PT-BR] Este módulo é uma fronteira de cache best-effort: qualquer erro de
# banco/serialização deve degradar para miss/no-op (o chamador recomputa) em vez
# de quebrar a telemetria, então os except amplos abaixo são intencionais — e
# sempre logados.
# pylint: disable=broad-exception-caught


def make_session_key(
    year: int, round_num: int, session_type: str, drivers: list[str]
) -> str:
    """
    Deterministic key for the multi-driver telemetry response.

    [PT-BR] Chave determinística para a resposta multi-piloto. Os códigos dos
    pilotos são normalizados (maiúsculas + ordenados) para que a ordem na
    requisição não gere chaves diferentes.
    """
    drivers_part = ",".join(sorted(d.upper() for d in drivers))
    return f"telemetry:{year}:{round_num}:{session_type}:{drivers_part}"


def make_lap_key(
    year: int, round_num: int, session_type: str, driver: str, lap_number: int
) -> str:
    """Deterministic key for the single-lap telemetry response."""
    return f"lap:{year}:{round_num}:{session_type}:{driver.upper()}:{lap_number}"


def _to_native(obj: Any) -> Any:
    """
    Recursively convert numpy scalars to native Python types.

    [EN] FastF1 payloads carry numpy scalars (np.int64, np.float64, np.bool_)
    that json.dumps (used by the DB JSON column) cannot serialize. This makes
    the payload JSON-safe before it is stored.
    [PT-BR] Payloads do FastF1 trazem escalares numpy que o json.dumps (usado
    pela coluna JSON do banco) não serializa. Isto torna o payload JSON-safe
    antes de gravar.
    """
    if isinstance(obj, dict):
        return {k: _to_native(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_native(v) for v in obj]
    # numpy scalars / 0-d arrays expose .item(); native str/bytes do not.
    if hasattr(obj, "item") and not isinstance(obj, (str, bytes)):
        try:
            return obj.item()
        except Exception:
            return obj
    return obj


async def get_cached(session: AsyncSession, cache_key: str) -> dict[str, Any] | None:
    """
    Return the cached payload for cache_key, or None on miss/error.

    [EN] On a hit, best-effort updates last_accessed_at (drives the TTL cleanup)
    without ever affecting the returned value.
    [PT-BR] No acerto, atualiza last_accessed_at (guia a limpeza por TTL) em
    best-effort, sem nunca afetar o valor retornado.
    """
    try:
        row = (
            await session.execute(
                select(TelemetryCache).where(TelemetryCache.cache_key == cache_key)
            )
        ).scalar_one_or_none()
    except Exception:
        logger.warning("Telemetry cache read failed (%s)", cache_key, exc_info=True)
        return None

    if row is None:
        return None

    payload = row.payload
    try:
        row.last_accessed_at = datetime.now(timezone.utc)
        await session.commit()
    except Exception:
        logger.warning("Telemetry cache touch failed (%s)", cache_key, exc_info=True)
        await session.rollback()
    return payload


async def set_cached(
    session: AsyncSession, cache_key: str, payload: dict[str, Any]
) -> None:
    """
    Store payload under cache_key. Best-effort: errors are logged, not raised
    (e.g. a duplicate key from a concurrent miss is harmless).
    """
    try:
        session.add(TelemetryCache(cache_key=cache_key, payload=_to_native(payload)))
        await session.commit()
    except Exception:
        logger.warning("Telemetry cache write failed (%s)", cache_key, exc_info=True)
        await session.rollback()
