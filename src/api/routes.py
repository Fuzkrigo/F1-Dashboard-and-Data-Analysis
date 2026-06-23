"""
API Route Definitions Module.

[EN] Defines the FastAPI route handlers for the F1 Insights API.
Includes endpoints for all 12 data entities with filtering, pagination,
and detail views. All endpoints are read-only (GET).

[PT-BR] Define os handlers de rotas do FastAPI para a API do F1 Insights.
Inclui endpoints para todas as 12 entidades de dados com filtragem,
paginação e views de detalhe. Todos os endpoints são somente leitura (GET).

Author: Bruno Krieger
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.api import schemas
from src.db.database import get_db
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

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Health / Saúde
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    [EN] Returns a simple status message to confirm the API is operational.
    [PT-BR] Retorna uma mensagem de status para confirmar que a API está
    operacional.

    Author: Bruno Krieger
    """
    return {"status": "ok"}


# ─────────────────────────────────────────────────────────────────────────────
# Seasons / Temporadas
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/seasons/", response_model=list[schemas.Season], tags=["Seasons"])
async def list_seasons(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    populated_only: bool = Query(
        False, description="Filter for seasons with added race data"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    List all F1 seasons.

    [EN] Returns a paginated list of F1 seasons ordered by year.
    [PT-BR] Retorna uma lista paginada de temporadas de F1 ordenada por ano.

    Author: Bruno Krieger
    """
    stmt = select(Season)
    if populated_only:
        stmt = stmt.where(exists().where(Race.season == Season.year))

    stmt = stmt.order_by(Season.year.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


# ─────────────────────────────────────────────────────────────────────────────
# Circuits / Circuitos
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/circuits/", response_model=list[schemas.Circuit], tags=["Circuits"])
async def list_circuits(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    country: str | None = Query(None, description="Filter by country"),
    db: AsyncSession = Depends(get_db),
):
    """
    List F1 circuits with optional country filter.

    [EN] Returns a paginated list of circuits, optionally filtered by country.
    [PT-BR] Retorna uma lista paginada de circuitos, opcionalmente filtrada
    por país.

    Author: Bruno Krieger
    """
    stmt = select(Circuit).order_by(Circuit.circuit_name)
    if country:
        stmt = stmt.where(Circuit.country.ilike(f"%{country}%"))
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get(
    "/circuits/{circuit_id}",
    response_model=schemas.Circuit,
    tags=["Circuits"],
)
async def get_circuit(circuit_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a specific circuit by ID.

    [EN] Returns details for a single circuit.
    [PT-BR] Retorna detalhes de um único circuito.

    Author: Bruno Krieger
    """
    result = await db.execute(select(Circuit).where(Circuit.id == circuit_id))
    circuit = result.scalar_one_or_none()
    if circuit is None:
        raise HTTPException(status_code=404, detail="Circuit not found")
    return circuit


# ─────────────────────────────────────────────────────────────────────────────
# Drivers / Pilotos
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/drivers/", response_model=list[schemas.Driver], tags=["Drivers"])
async def list_drivers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    nationality: str | None = Query(None, description="Filter by nationality"),
    db: AsyncSession = Depends(get_db),
):
    """
    List F1 drivers with optional nationality filter.

    [EN] Returns a paginated list of drivers, optionally filtered by
    nationality.
    [PT-BR] Retorna uma lista paginada de pilotos, opcionalmente filtrada
    por nacionalidade.

    Author: Bruno Krieger
    """
    stmt = select(Driver).order_by(Driver.last_name)
    if nationality:
        stmt = stmt.where(Driver.nationality.ilike(f"%{nationality}%"))
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get(
    "/drivers/{driver_id}",
    response_model=schemas.Driver,
    tags=["Drivers"],
)
async def get_driver(driver_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a specific driver by ID.

    [EN] Returns details for a single driver.
    [PT-BR] Retorna detalhes de um único piloto.

    Author: Bruno Krieger
    """
    result = await db.execute(select(Driver).where(Driver.id == driver_id))
    driver = result.scalar_one_or_none()
    if driver is None:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


# ─────────────────────────────────────────────────────────────────────────────
# Constructors / Construtores
# ─────────────────────────────────────────────────────────────────────────────


@router.get(
    "/constructors/",
    response_model=list[schemas.Constructor],
    tags=["Constructors"],
)
async def list_constructors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    nationality: str | None = Query(None, description="Filter by nationality"),
    db: AsyncSession = Depends(get_db),
):
    """
    List F1 constructors with optional nationality filter.

    [EN] Returns a paginated list of constructors (teams).
    [PT-BR] Retorna uma lista paginada de construtores (equipes).

    Author: Bruno Krieger
    """
    stmt = select(Constructor).order_by(Constructor.constructor_name)
    if nationality:
        stmt = stmt.where(Constructor.nationality.ilike(f"%{nationality}%"))
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get(
    "/constructors/{constructor_id}",
    response_model=schemas.Constructor,
    tags=["Constructors"],
)
async def get_constructor(constructor_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a specific constructor by ID.

    [EN] Returns details for a single constructor.
    [PT-BR] Retorna detalhes de um único construtor.

    Author: Bruno Krieger
    """
    result = await db.execute(
        select(Constructor).where(Constructor.id == constructor_id)
    )
    constructor = result.scalar_one_or_none()
    if constructor is None:
        raise HTTPException(status_code=404, detail="Constructor not found")
    return constructor


# ─────────────────────────────────────────────────────────────────────────────
# Races / Corridas
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/races/", response_model=list[schemas.Race], tags=["Races"])
async def list_races(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    season: int | None = Query(None, description="Filter by season year"),
    db: AsyncSession = Depends(get_db),
):
    """
    List F1 races with optional season filter.

    [EN] Returns a paginated list of races, optionally filtered by season.
    [PT-BR] Retorna uma lista paginada de corridas, opcionalmente filtrada
    por temporada.

    Author: Bruno Krieger
    """
    stmt = select(Race).order_by(Race.season.desc(), Race.round)
    if season:
        stmt = stmt.where(Race.season == season)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get(
    "/races/{race_id}",
    response_model=schemas.Race,
    tags=["Races"],
)
async def get_race(race_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a specific race by ID.

    [EN] Returns details for a single race.
    [PT-BR] Retorna detalhes de uma única corrida.

    Author: Bruno Krieger
    """
    result = await db.execute(select(Race).where(Race.id == race_id))
    race = result.scalar_one_or_none()
    if race is None:
        raise HTTPException(status_code=404, detail="Race not found")
    return race


# ─────────────────────────────────────────────────────────────────────────────
# Race Results / Resultados
# ─────────────────────────────────────────────────────────────────────────────


@router.get(
    "/results/", response_model=list[schemas.RaceResultEnriched], tags=["Results"]
)
async def list_results(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    season: int | None = Query(None, description="Filter by season year"),
    race_id: int | None = Query(None, description="Filter by race ID"),
    driver_id: int | None = Query(None, description="Filter by driver ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    List race results (enriched) with optional filters.

    [EN] Returns a paginated list of race results already including driver name,
    code and constructor name (via JOIN), so the dashboard avoids one request per
    driver/constructor. Can be filtered by season, race, or driver.
    [PT-BR] Retorna uma lista paginada de resultados já incluindo nome e código
    do piloto e nome do construtor (via JOIN), evitando uma requisição por
    piloto/construtor. Pode ser filtrada por temporada, corrida ou piloto.

    Author: Bruno Krieger
    """
    stmt = (
        select(
            RaceResult,
            Driver.first_name,
            Driver.last_name,
            Driver.code,
            Constructor.constructor_name,
        )
        .join(Driver, RaceResult.driver_id == Driver.id)
        .outerjoin(Constructor, RaceResult.constructor_id == Constructor.id)
        .order_by(RaceResult.race_id, RaceResult.position)
    )
    if season:
        stmt = stmt.join(Race, RaceResult.race_id == Race.id).where(
            Race.season == season
        )
    if race_id:
        stmt = stmt.where(RaceResult.race_id == race_id)
    if driver_id:
        stmt = stmt.where(RaceResult.driver_id == driver_id)
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    results = []
    for race_result, first, last, code, team in result.all():
        item = schemas.RaceResult.model_validate(race_result).model_dump()
        item.update(
            {
                "driver_name": f"{first} {last}",
                "driver_code": code,
                "constructor_name": team,
            }
        )
        results.append(item)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Qualifying / Classificação
# ─────────────────────────────────────────────────────────────────────────────


@router.get(
    "/qualifying/",
    response_model=list[schemas.QualifyingResult],
    tags=["Qualifying"],
)
async def list_qualifying(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    season: int | None = Query(None, description="Filter by season year"),
    race_id: int | None = Query(None, description="Filter by race ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    List qualifying results with optional filters.

    [EN] Returns a paginated list of qualifying session results.
    [PT-BR] Retorna uma lista paginada de resultados de classificação.

    Author: Bruno Krieger
    """
    stmt = select(QualifyingResult).order_by(
        QualifyingResult.race_id, QualifyingResult.position
    )
    if season:
        stmt = stmt.join(Race).where(Race.season == season)
    if race_id:
        stmt = stmt.where(QualifyingResult.race_id == race_id)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


# ─────────────────────────────────────────────────────────────────────────────
# Sprint Results / Resultados Sprint
# ─────────────────────────────────────────────────────────────────────────────


@router.get(
    "/sprint/",
    response_model=list[schemas.SprintResult],
    tags=["Sprint"],
)
async def list_sprint_results(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    season: int | None = Query(None, description="Filter by season year"),
    race_id: int | None = Query(None, description="Filter by race ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    List sprint race results with optional filters.

    [EN] Returns a paginated list of sprint results (2021+).
    [PT-BR] Retorna uma lista paginada de resultados de sprint (2021+).

    Author: Bruno Krieger
    """
    stmt = select(SprintResult).order_by(SprintResult.race_id, SprintResult.position)
    if season:
        stmt = stmt.join(Race).where(Race.season == season)
    if race_id:
        stmt = stmt.where(SprintResult.race_id == race_id)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


# ─────────────────────────────────────────────────────────────────────────────
# Standings / Classificações de Campeonato
# ─────────────────────────────────────────────────────────────────────────────


@router.get(
    "/standings/drivers/",
    response_model=list[schemas.DriverStandingEnriched],
    tags=["Standings"],
)
async def list_driver_standings(
    season: int | None = Query(None, description="Filter by season year"),
    db: AsyncSession = Depends(get_db),
):
    """
    List driver championship standings (enriched).

    [EN] Returns driver standings already including the driver's name, code,
    number, nationality and team name (the constructor from the standing's race),
    so the dashboard does not need one extra request per driver.
    [PT-BR] Retorna a classificação de pilotos já incluindo nome, código, número,
    nacionalidade e nome da equipe (o construtor da corrida do standing), evitando
    uma requisição extra por piloto.

    Author: Bruno Krieger
    """
    stmt = (
        select(
            DriverStanding,
            Driver.first_name,
            Driver.last_name,
            Driver.code,
            Driver.permanent_number,
            Driver.nationality,
            Constructor.constructor_name,
        )
        .join(Driver, DriverStanding.driver_id == Driver.id)
        .outerjoin(
            RaceResult,
            (RaceResult.driver_id == DriverStanding.driver_id)
            & (RaceResult.race_id == DriverStanding.race_id),
        )
        .outerjoin(Constructor, RaceResult.constructor_id == Constructor.id)
        .order_by(DriverStanding.position)
    )
    if season:
        stmt = stmt.join(Race, DriverStanding.race_id == Race.id).where(
            Race.season == season
        )

    result = await db.execute(stmt)
    standings = []
    for standing, first, last, code, number, nationality, team in result.all():
        item = schemas.DriverStanding.model_validate(standing).model_dump()
        item.update(
            {
                "driver_name": f"{first} {last}",
                "driver_code": code,
                "permanent_number": number,
                "nationality": nationality,
                "constructor_name": team,
            }
        )
        standings.append(item)
    return standings


@router.get(
    "/standings/constructors/",
    response_model=list[schemas.ConstructorStandingEnriched],
    tags=["Standings"],
)
async def list_constructor_standings(
    season: int | None = Query(None, description="Filter by season year"),
    db: AsyncSession = Depends(get_db),
):
    """
    List constructor championship standings (enriched).

    [EN] Returns constructor standings already including the constructor name and
    nationality (via JOIN), so the dashboard avoids one request per constructor.
    [PT-BR] Retorna a classificação de construtores já incluindo o nome e a
    nacionalidade do construtor (via JOIN), evitando uma requisição por construtor.

    Author: Bruno Krieger
    """
    stmt = (
        select(
            ConstructorStanding,
            Constructor.constructor_name,
            Constructor.nationality,
        )
        .join(Constructor, ConstructorStanding.constructor_id == Constructor.id)
        .order_by(ConstructorStanding.position)
    )
    if season:
        stmt = stmt.join(Race, ConstructorStanding.race_id == Race.id).where(
            Race.season == season
        )

    result = await db.execute(stmt)
    standings = []
    for standing, name, nationality in result.all():
        item = schemas.ConstructorStanding.model_validate(standing).model_dump()
        item.update({"constructor_name": name, "nationality": nationality})
        standings.append(item)
    return standings


# ─────────────────────────────────────────────────────────────────────────────
# Pit Stops / Pit Stops
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/pitstops/", response_model=list[schemas.PitStop], tags=["Pit Stops"])
async def list_pit_stops(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    race_id: int | None = Query(None, description="Filter by race ID"),
    driver_id: int | None = Query(None, description="Filter by driver ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    List pit stops with optional filters.

    [EN] Returns a paginated list of pit stops.
    [PT-BR] Retorna uma lista paginada de pit stops.

    Author: Bruno Krieger
    """
    stmt = select(PitStop).order_by(PitStop.race_id, PitStop.lap, PitStop.stop)
    if race_id:
        stmt = stmt.where(PitStop.race_id == race_id)
    if driver_id:
        stmt = stmt.where(PitStop.driver_id == driver_id)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


# ─────────────────────────────────────────────────────────────────────────────
# Lap Times / Tempos de Volta
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/laps/", response_model=list[schemas.LapTime], tags=["Lap Times"])
async def list_lap_times(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    race_id: int | None = Query(None, description="Filter by race ID"),
    driver_id: int | None = Query(None, description="Filter by driver ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    List lap times with optional filters.

    [EN] Returns a paginated list of lap times. Filtering by race_id is
    strongly recommended due to large data volume.
    [PT-BR] Retorna uma lista paginada de tempos de volta. Filtrar por
    race_id é fortemente recomendado devido ao grande volume de dados.

    Author: Bruno Krieger
    """
    stmt = select(LapTime).order_by(LapTime.race_id, LapTime.lap, LapTime.position)
    if race_id:
        stmt = stmt.where(LapTime.race_id == race_id)
    if driver_id:
        stmt = stmt.where(LapTime.driver_id == driver_id)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


# ─────────────────────────────────────────────────────────────────────────────
# Statuses / Status de Finalização
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/statuses/", response_model=list[schemas.Status], tags=["Statuses"])
async def list_statuses(
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """
    List all race finishing statuses.

    [EN] Returns a paginated list of finishing statuses.
    [PT-BR] Retorna uma lista paginada de status de finalização.

    Author: Bruno Krieger
    """
    stmt = select(Status).order_by(Status.id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
