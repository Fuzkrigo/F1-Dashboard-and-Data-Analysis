"""
ETL — Load Module.

[EN] Handles the loading step of the ETL pipeline. Inserts transformed
data into the database for all 12 entities. Uses in-memory lookup caches
for foreign key resolution (driver_ref→id, constructor_ref→id,
circuit_ref→id) to avoid repeated queries. All inserts are idempotent —
existing records are skipped based on natural keys.

[PT-BR] Realiza a etapa de carregamento do pipeline ETL. Insere dados
transformados no banco de dados para todas as 12 entidades. Usa caches
de lookup em memória para resolução de chaves estrangeiras
(driver_ref→id, constructor_ref→id, circuit_ref→id) para evitar
queries repetidas. Todas as inserções são idempotentes — registros
existentes são ignorados com base em chaves naturais.

Author: Bruno Krieger
"""

from sqlalchemy import select
from src.db.database import AsyncSessionLocal, Base, engine
from src.db.models import (
    Circuit,
    Constructor,
    ConstructorStanding,
    Driver,
    DriverStanding,
    LapTime,
    PitStop,
    QualifyingResult,
    Race,
    RaceResult,
    Season,
    SprintResult,
    Status,
)

# ─────────────────────────────────────────────────────────────────────────────
# Lookup Caches / Caches de Lookup
# ─────────────────────────────────────────────────────────────────────────────

# In-memory maps: ref_string → database ID
# Mapas em memória: ref_string → ID do banco de dados
_circuit_cache: dict[str, int] = {}
_driver_cache: dict[str, int] = {}
_constructor_cache: dict[str, int] = {}
_race_cache: dict[tuple[int, int], int] = {}  # (season, round) → race_id


async def _build_lookup_caches(session) -> None:
    """
    Build all FK lookup caches from existing database records.

    [EN] Queries the database once for all circuits, drivers, constructors,
    and races, populating in-memory dicts for fast FK resolution during
    load. This avoids N+1 query patterns.

    [PT-BR] Consulta o banco uma vez para todos os circuitos, pilotos,
    construtores e corridas, populando dicts em memória para resolução
    rápida de FK durante a carga. Isso evita padrões de query N+1.

    Args:
        session: Active SQLAlchemy async session.

    Author: Bruno Krieger
    """
    global _circuit_cache, _driver_cache, _constructor_cache, _race_cache

    # Circuits / Circuitos
    result = await session.execute(select(Circuit))
    for circuit in result.scalars().all():
        _circuit_cache[circuit.circuit_ref] = circuit.id

    # Drivers / Pilotos
    result = await session.execute(select(Driver))
    for driver in result.scalars().all():
        _driver_cache[driver.driver_ref] = driver.id

    # Constructors / Construtores
    result = await session.execute(select(Constructor))
    for constructor in result.scalars().all():
        _constructor_cache[constructor.constructor_ref] = constructor.id

    # Races / Corridas
    result = await session.execute(select(Race))
    for race in result.scalars().all():
        _race_cache[(race.season, race.round)] = race.id


# ─────────────────────────────────────────────────────────────────────────────
# Table Creation / Criação de Tabelas
# ─────────────────────────────────────────────────────────────────────────────


async def create_tables() -> None:
    """
    Create all database tables if they don't exist.

    [EN] Uses SQLAlchemy metadata.create_all to create tables defined
    by the ORM models. Idempotent — safe to call multiple times.
    [PT-BR] Usa metadata.create_all do SQLAlchemy para criar tabelas
    definidas pelos modelos ORM. Idempotente — seguro para chamar
    múltiplas vezes.

    Author: Bruno Krieger
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("  [OK] Database tables created/verified.")


# ─────────────────────────────────────────────────────────────────────────────
# Load Functions / Funções de Carga
# ─────────────────────────────────────────────────────────────────────────────


async def load_seasons(seasons_data: list[dict]) -> int:
    """
    Load season records into the database.

    [EN] Inserts seasons that don't already exist (matched by year).
    [PT-BR] Insere temporadas que ainda não existem (verificado por ano).

    Returns:
        int: Number of new records inserted.

    Author: Bruno Krieger
    """
    count = 0
    async with AsyncSessionLocal() as session:
        for data in seasons_data:
            stmt = select(Season).where(Season.year == data["year"])
            result = await session.execute(stmt)
            if result.scalar_one_or_none() is None:
                session.add(Season(**data))
                count += 1
        await session.commit()
    print(f"  [OK] Seasons: {count} new, {len(seasons_data) - count} existing.")
    return count


async def load_statuses(statuses_data: list[dict]) -> int:
    """
    Load status records into the database.

    [EN] Inserts statuses that don't already exist (matched by id).
    [PT-BR] Insere status que ainda não existem (verificado por id).

    Returns:
        int: Number of new records inserted.

    Author: Bruno Krieger
    """
    count = 0
    async with AsyncSessionLocal() as session:
        for data in statuses_data:
            stmt = select(Status).where(Status.id == data["id"])
            result = await session.execute(stmt)
            if result.scalar_one_or_none() is None:
                session.add(Status(**data))
                count += 1
        await session.commit()
    print(f"  [OK] Statuses: {count} new, {len(statuses_data) - count} existing.")
    return count


async def load_circuits(circuits_data: list[dict]) -> int:
    """
    Load circuit records into the database.

    [EN] Inserts circuits that don't already exist (matched by circuit_ref).
    Updates the circuit lookup cache after insertion.
    [PT-BR] Insere circuitos que ainda não existem (verificado por circuit_ref).
    Atualiza o cache de lookup de circuitos após inserção.

    Returns:
        int: Number of new records inserted.

    Author: Bruno Krieger
    """
    count = 0
    async with AsyncSessionLocal() as session:
        for data in circuits_data:
            ref = data["circuit_ref"]
            if ref in _circuit_cache:
                continue
            stmt = select(Circuit).where(Circuit.circuit_ref == ref)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing is None:
                circuit = Circuit(**data)
                session.add(circuit)
                await session.flush()
                _circuit_cache[ref] = circuit.id
                count += 1
            else:
                _circuit_cache[ref] = existing.id
        await session.commit()
    print(f"  [OK] Circuits: {count} new, {len(circuits_data) - count} existing.")
    return count


async def load_drivers(drivers_data: list[dict]) -> int:
    """
    Load driver records into the database.

    [EN] Inserts drivers that don't already exist (matched by driver_ref).
    Updates the driver lookup cache after insertion.
    [PT-BR] Insere pilotos que ainda não existem (verificado por driver_ref).
    Atualiza o cache de lookup de pilotos após inserção.

    Returns:
        int: Number of new records inserted.

    Author: Bruno Krieger
    """
    count = 0
    async with AsyncSessionLocal() as session:
        for data in drivers_data:
            ref = data["driver_ref"]
            if ref in _driver_cache:
                continue
            stmt = select(Driver).where(Driver.driver_ref == ref)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing is None:
                driver = Driver(**data)
                session.add(driver)
                await session.flush()
                _driver_cache[ref] = driver.id
                count += 1
            else:
                _driver_cache[ref] = existing.id
        await session.commit()
    print(f"  [OK] Drivers: {count} new, {len(drivers_data) - count} existing.")
    return count


async def load_constructors(constructors_data: list[dict]) -> int:
    """
    Load constructor records into the database.

    [EN] Inserts constructors not already present (matched by constructor_ref).
    Updates the constructor lookup cache after insertion.
    [PT-BR] Insere construtores que ainda não existem (verificado por
    constructor_ref). Atualiza o cache de lookup após inserção.

    Returns:
        int: Number of new records inserted.

    Author: Bruno Krieger
    """
    count = 0
    async with AsyncSessionLocal() as session:
        for data in constructors_data:
            ref = data["constructor_ref"]
            if ref in _constructor_cache:
                continue
            stmt = select(Constructor).where(Constructor.constructor_ref == ref)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing is None:
                constructor = Constructor(**data)
                session.add(constructor)
                await session.flush()
                _constructor_cache[ref] = constructor.id
                count += 1
            else:
                _constructor_cache[ref] = existing.id
        await session.commit()
    print(
        f"  [OK] Constructors: {count} new, {len(constructors_data) - count} existing."
    )
    return count


async def load_races(races_data: list[dict]) -> int:
    """
    Load race records into the database.

    [EN] Inserts races not already present (matched by season + round).
    Resolves circuit_id FK via lookup cache. Updates the race cache.
    [PT-BR] Insere corridas que ainda não existem (verificado por season +
    round). Resolve FK circuit_id via cache de lookup. Atualiza o cache
    de corridas.

    Returns:
        int: Number of new records inserted.

    Author: Bruno Krieger
    """
    count = 0
    async with AsyncSessionLocal() as session:
        for data in races_data:
            key = (data["season"], data["round"])
            if key in _race_cache:
                continue

            stmt = select(Race).where(
                (Race.season == data["season"]) & (Race.round == data["round"])
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing is None:
                # Resolve circuit FK / Resolve FK do circuito
                circuit_ref = data.pop("circuit_ref", "")
                data["circuit_id"] = _circuit_cache.get(circuit_ref)

                race = Race(**data)
                session.add(race)
                await session.flush()
                _race_cache[key] = race.id
                count += 1
            else:
                _race_cache[key] = existing.id
        await session.commit()
    print(f"  [OK] Races: {count} new, {len(races_data) - count} existing.")
    return count


async def load_results(results_data: list[dict], season: int, round_num: int) -> int:
    """
    Load race result records for a specific race.

    [EN] Inserts race results not already present (matched by race_id +
    driver_id). Resolves driver_id and constructor_id via lookup caches.
    [PT-BR] Insere resultados que ainda não existem (verificado por
    race_id + driver_id). Resolve FKs via caches de lookup.

    Returns:
        int: Number of new records inserted.

    Author: Bruno Krieger
    """
    race_id = _race_cache.get((season, round_num))
    if race_id is None:
        return 0

    count = 0
    async with AsyncSessionLocal() as session:
        for data in results_data:
            driver_id = _driver_cache.get(data.pop("driver_ref", ""))
            constructor_id = _constructor_cache.get(data.pop("constructor_ref", ""))

            if driver_id is None:
                continue

            # Check for existing / Verificar existente
            stmt = select(RaceResult).where(
                (RaceResult.race_id == race_id) & (RaceResult.driver_id == driver_id)
            )
            result = await session.execute(stmt)
            if result.scalar_one_or_none() is None:
                data["race_id"] = race_id
                data["driver_id"] = driver_id
                data["constructor_id"] = constructor_id
                session.add(RaceResult(**data))
                count += 1
        await session.commit()
    return count


async def load_qualifying(
    qualifying_data: list[dict], season: int, round_num: int
) -> int:
    """
    Load qualifying result records for a specific race.

    [EN] Inserts qualifying results not already present.
    [PT-BR] Insere resultados de classificação que ainda não existem.

    Returns:
        int: Number of new records inserted.

    Author: Bruno Krieger
    """
    race_id = _race_cache.get((season, round_num))
    if race_id is None:
        return 0

    count = 0
    async with AsyncSessionLocal() as session:
        for data in qualifying_data:
            driver_id = _driver_cache.get(data.pop("driver_ref", ""))
            constructor_id = _constructor_cache.get(data.pop("constructor_ref", ""))

            if driver_id is None:
                continue

            stmt = select(QualifyingResult).where(
                (QualifyingResult.race_id == race_id)
                & (QualifyingResult.driver_id == driver_id)
            )
            result = await session.execute(stmt)
            if result.scalar_one_or_none() is None:
                data["race_id"] = race_id
                data["driver_id"] = driver_id
                data["constructor_id"] = constructor_id
                session.add(QualifyingResult(**data))
                count += 1
        await session.commit()
    return count


async def load_sprint(sprint_data: list[dict], season: int, round_num: int) -> int:
    """
    Load sprint result records for a specific race.

    [EN] Inserts sprint results not already present.
    [PT-BR] Insere resultados de sprint que ainda não existem.

    Returns:
        int: Number of new records inserted.

    Author: Bruno Krieger
    """
    race_id = _race_cache.get((season, round_num))
    if race_id is None:
        return 0

    count = 0
    async with AsyncSessionLocal() as session:
        for data in sprint_data:
            driver_id = _driver_cache.get(data.pop("driver_ref", ""))
            constructor_id = _constructor_cache.get(data.pop("constructor_ref", ""))

            if driver_id is None:
                continue

            stmt = select(SprintResult).where(
                (SprintResult.race_id == race_id)
                & (SprintResult.driver_id == driver_id)
            )
            result = await session.execute(stmt)
            if result.scalar_one_or_none() is None:
                data["race_id"] = race_id
                data["driver_id"] = driver_id
                data["constructor_id"] = constructor_id
                session.add(SprintResult(**data))
                count += 1
        await session.commit()
    return count


async def load_driver_standings(
    standings_data: list[dict], season: int, race_id_override: int | None = None
) -> int:
    """
    Load driver standing records for a season.

    [EN] Inserts driver standings not already present. The race_id is
    resolved to the last race of the season (final standings).
    [PT-BR] Insere classificações de piloto que ainda não existem.
    O race_id é resolvido para a última corrida da temporada
    (classificação final).

    Returns:
        int: Number of new records inserted.

    Author: Bruno Krieger
    """
    # Find the last race of the season for the standings
    # Encontrar a última corrida da temporada para as classificações
    race_id = race_id_override
    if race_id is None:
        max_round = 0
        for (s, r), rid in _race_cache.items():
            if s == season and r > max_round:
                max_round = r
                race_id = rid

    if race_id is None:
        return 0

    count = 0
    async with AsyncSessionLocal() as session:
        for data in standings_data:
            driver_id = _driver_cache.get(data.pop("driver_ref", ""))
            if driver_id is None:
                continue

            stmt = select(DriverStanding).where(
                (DriverStanding.race_id == race_id)
                & (DriverStanding.driver_id == driver_id)
            )
            result = await session.execute(stmt)
            if result.scalar_one_or_none() is None:
                data["race_id"] = race_id
                data["driver_id"] = driver_id
                session.add(DriverStanding(**data))
                count += 1
        await session.commit()
    print(f"  [OK] Driver Standings: {count} new.")
    return count


async def load_constructor_standings(
    standings_data: list[dict], season: int, race_id_override: int | None = None
) -> int:
    """
    Load constructor standing records for a season.

    [EN] Inserts constructor standings not already present.
    [PT-BR] Insere classificações de construtor que ainda não existem.

    Returns:
        int: Number of new records inserted.

    Author: Bruno Krieger
    """
    race_id = race_id_override
    if race_id is None:
        max_round = 0
        for (s, r), rid in _race_cache.items():
            if s == season and r > max_round:
                max_round = r
                race_id = rid

    if race_id is None:
        return 0

    count = 0
    async with AsyncSessionLocal() as session:
        for data in standings_data:
            constructor_id = _constructor_cache.get(data.pop("constructor_ref", ""))
            if constructor_id is None:
                continue

            stmt = select(ConstructorStanding).where(
                (ConstructorStanding.race_id == race_id)
                & (ConstructorStanding.constructor_id == constructor_id)
            )
            result = await session.execute(stmt)
            if result.scalar_one_or_none() is None:
                data["race_id"] = race_id
                data["constructor_id"] = constructor_id
                session.add(ConstructorStanding(**data))
                count += 1
        await session.commit()
    print(f"  [OK] Constructor Standings: {count} new.")
    return count


async def load_pit_stops(
    pit_stops_data: list[dict], season: int, round_num: int
) -> int:
    """
    Load pit stop records for a specific race.

    [EN] Inserts pit stops not already present (matched by race_id +
    driver_id + stop number).
    [PT-BR] Insere pit stops que ainda não existem (verificado por
    race_id + driver_id + número da parada).

    Returns:
        int: Number of new records inserted.

    Author: Bruno Krieger
    """
    race_id = _race_cache.get((season, round_num))
    if race_id is None:
        return 0

    count = 0
    async with AsyncSessionLocal() as session:
        for data in pit_stops_data:
            driver_id = _driver_cache.get(data.pop("driver_ref", ""))
            if driver_id is None:
                continue

            stmt = select(PitStop).where(
                (PitStop.race_id == race_id)
                & (PitStop.driver_id == driver_id)
                & (PitStop.stop == data["stop"])
            )
            result = await session.execute(stmt)
            if result.scalar_one_or_none() is None:
                data["race_id"] = race_id
                data["driver_id"] = driver_id
                session.add(PitStop(**data))
                count += 1
        await session.commit()
    return count


async def load_laps(laps_data: list[dict], season: int, round_num: int) -> int:
    """
    Load lap time records for a specific race.

    [EN] Inserts lap times not already present (matched by race_id +
    driver_id + lap number).
    [PT-BR] Insere tempos de volta que ainda não existem (verificado por
    race_id + driver_id + número da volta).

    Returns:
        int: Number of new records inserted.

    Author: Bruno Krieger
    """
    race_id = _race_cache.get((season, round_num))
    if race_id is None:
        return 0

    count = 0
    async with AsyncSessionLocal() as session:
        for data in laps_data:
            driver_id = _driver_cache.get(data.pop("driver_ref", ""))
            if driver_id is None:
                continue

            stmt = select(LapTime).where(
                (LapTime.race_id == race_id)
                & (LapTime.driver_id == driver_id)
                & (LapTime.lap == data["lap"])
            )
            result = await session.execute(stmt)
            if result.scalar_one_or_none() is None:
                data["race_id"] = race_id
                data["driver_id"] = driver_id
                session.add(LapTime(**data))
                count += 1
        await session.commit()
    return count
