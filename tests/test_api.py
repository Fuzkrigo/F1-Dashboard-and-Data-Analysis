"""
Tests for the FastAPI REST API endpoints.

[EN] All tests run against an isolated in-memory SQLite database that is
seeded with minimal fixture data for each test session. The FastAPI
`get_db` dependency is overridden via `app.dependency_overrides` so the
endpoints query the seeded fixture instead of the real local database.
This makes the suite fully self-contained and reproducible.

[PT-BR] Todos os testes rodam contra um banco SQLite em memória isolado
que é populado com dados mínimos por sessão de teste. A dependência
`get_db` do FastAPI é substituída via `app.dependency_overrides` para que
os endpoints consultem o fixture populado ao invés do banco local real.
Isso torna a suíte totalmente autocontida e reproduzível.
"""

from datetime import date

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.main import app
from src.db.database import Base, get_db
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
# Fixture: in-memory database seeded with minimal F1 data
# ─────────────────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def async_client():
    """
    Creates an isolated in-memory SQLite DB, seeds it, overrides the API's
    get_db dependency, and yields an httpx AsyncClient ready to query.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    test_session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)

    # Seed minimal data covering all entities the endpoints touch
    async with test_session_maker() as session:
        # Seasons
        session.add_all(
            [
                Season(year=2021, url="u/2021"),
                Season(year=2023, url="u/2023"),
            ]
        )

        # Circuits
        monaco = Circuit(
            circuit_ref="monaco",
            circuit_name="Circuit de Monaco",
            location="Monte Carlo",
            country="Monaco",
            latitude=43.7,
            longitude=7.4,
            url="u/monaco",
        )
        monza = Circuit(
            circuit_ref="monza",
            circuit_name="Autodromo Nazionale Monza",
            location="Monza",
            country="Italy",
            latitude=45.6,
            longitude=9.3,
            url="u/monza",
        )
        session.add_all([monaco, monza])

        # Drivers
        ver = Driver(
            driver_ref="max_verstappen",
            permanent_number=1,
            code="VER",
            first_name="Max",
            last_name="Verstappen",
            date_of_birth=date(1997, 9, 30),
            nationality="Dutch",
            url="u/ver",
        )
        ham = Driver(
            driver_ref="hamilton",
            permanent_number=44,
            code="HAM",
            first_name="Lewis",
            last_name="Hamilton",
            date_of_birth=date(1985, 1, 7),
            nationality="British",
            url="u/ham",
        )
        session.add_all([ver, ham])

        # Constructors
        red_bull = Constructor(
            constructor_ref="red_bull",
            constructor_name="Red Bull",
            nationality="Austrian",
            url="u/rb",
        )
        ferrari = Constructor(
            constructor_ref="ferrari",
            constructor_name="Ferrari",
            nationality="Italian",
            url="u/fer",
        )
        session.add_all([red_bull, ferrari])

        await session.flush()  # populate IDs for FKs

        # Races (FK to circuit)
        race1 = Race(
            season=2023,
            round=1,
            url="u/r1",
            race_name="Bahrain GP",
            circuit_id=monaco.id,
            circuit_name="Bahrain",
            date=date(2023, 3, 5),
        )
        race2 = Race(
            season=2021,
            round=1,
            url="u/r2-2021",
            race_name="Bahrain GP 2021",
            circuit_id=monaco.id,
            circuit_name="Bahrain",
            date=date(2021, 3, 28),
        )
        session.add_all([race1, race2])
        await session.flush()

        # Results / Qualifying / Sprint
        session.add_all(
            [
                RaceResult(
                    race_id=race1.id,
                    driver_id=ver.id,
                    constructor_id=red_bull.id,
                    grid=1,
                    position=1,
                    position_text="1",
                    points=25.0,
                    laps=57,
                    status="Finished",
                ),
                QualifyingResult(
                    race_id=race1.id,
                    driver_id=ver.id,
                    constructor_id=red_bull.id,
                    position=1,
                    q1="1:30",
                    q2="1:29",
                    q3="1:28",
                ),
                SprintResult(
                    race_id=race1.id,
                    driver_id=ver.id,
                    constructor_id=red_bull.id,
                    grid=1,
                    position=1,
                    position_text="1",
                    points=8.0,
                    laps=23,
                    status="Finished",
                ),
                DriverStanding(
                    race_id=race2.id,
                    driver_id=ham.id,
                    points=387.0,
                    position=1,
                    wins=8,
                ),
                ConstructorStanding(
                    race_id=race2.id,
                    constructor_id=red_bull.id,
                    points=585.0,
                    position=1,
                    wins=11,
                ),
                PitStop(
                    race_id=race1.id,
                    driver_id=ver.id,
                    stop=1,
                    lap=15,
                    duration="23.450",
                    duration_ms=23450,
                ),
                LapTime(
                    race_id=race1.id,
                    driver_id=ver.id,
                    lap=1,
                    position=1,
                    time="1:30.500",
                ),
                Status(id=1, status="Finished", count=1000),
                Status(id=2, status="Engine", count=50),
            ]
        )
        await session.commit()

    # Override FastAPI's get_db dependency to use our test session
    async def override_get_db():
        async with test_session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    # Cleanup
    app.dependency_overrides.clear()
    await engine.dispose()


# ─────────────────────────────────────────────────────────────────────────────
# Health & Root
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_root(async_client):
    response = await async_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to F1 Insights API"}


@pytest.mark.asyncio
async def test_health(async_client):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ─────────────────────────────────────────────────────────────────────────────
# Seasons / Circuits / Drivers / Constructors / Races
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_seasons(async_client):
    response = await async_client.get("/api/v1/seasons/?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {d["year"] for d in data} == {2021, 2023}


@pytest.mark.asyncio
async def test_seasons_populated_only_filter(async_client):
    """populated_only=true returns only seasons that have races."""
    response = await async_client.get("/api/v1/seasons/?populated_only=true")
    assert response.status_code == 200
    data = response.json()
    # Both 2021 and 2023 have races in the fixture
    assert len(data) == 2


@pytest.mark.asyncio
async def test_list_circuits(async_client):
    response = await async_client.get("/api/v1/circuits/?limit=5")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_list_circuits_country_filter(async_client):
    response = await async_client.get("/api/v1/circuits/?country=Italy")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["country"] == "Italy"


@pytest.mark.asyncio
async def test_list_drivers_pagination(async_client):
    response = await async_client.get("/api/v1/drivers/?limit=5&skip=0")
    assert response.status_code == 200
    assert len(response.json()) <= 5

    # Pydantic limit validates <= 500
    response_error = await async_client.get("/api/v1/drivers/?limit=600")
    assert response_error.status_code == 422


@pytest.mark.asyncio
async def test_drivers_nationality_filter(async_client):
    response = await async_client.get("/api/v1/drivers/?nationality=British")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["nationality"] == "British"


@pytest.mark.asyncio
async def test_list_constructors_and_nationality_filter(async_client):
    list_resp = await async_client.get("/api/v1/constructors/?limit=5")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 2

    filtered = await async_client.get("/api/v1/constructors/?nationality=Italian")
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1


@pytest.mark.asyncio
async def test_list_races_season_filter(async_client):
    response = await async_client.get("/api/v1/races/?season=2023&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert all(r["season"] == 2023 for r in data)


@pytest.mark.asyncio
async def test_standings(async_client):
    resp_drivers = await async_client.get("/api/v1/standings/drivers/?season=2021")
    assert resp_drivers.status_code == 200
    assert len(resp_drivers.json()) >= 1

    resp_constructors = await async_client.get(
        "/api/v1/standings/constructors/?season=2021"
    )
    assert resp_constructors.status_code == 200
    assert len(resp_constructors.json()) >= 1


# ─────────────────────────────────────────────────────────────────────────────
# Detail endpoints — get by ID (404 + 200)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_invalid_circuit(async_client):
    response = await async_client.get("/api/v1/circuits/9999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_invalid_driver(async_client):
    response = await async_client.get("/api/v1/drivers/9999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_invalid_constructor(async_client):
    response = await async_client.get("/api/v1/constructors/9999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_invalid_race(async_client):
    response = await async_client.get("/api/v1/races/9999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_circuit_by_id_when_exists(async_client):
    list_resp = await async_client.get("/api/v1/circuits/?limit=1")
    cid = list_resp.json()[0]["id"]
    detail = await async_client.get(f"/api/v1/circuits/{cid}")
    assert detail.status_code == 200
    assert detail.json()["id"] == cid


@pytest.mark.asyncio
async def test_get_driver_by_id_when_exists(async_client):
    list_resp = await async_client.get("/api/v1/drivers/?limit=1")
    did = list_resp.json()[0]["id"]
    detail = await async_client.get(f"/api/v1/drivers/{did}")
    assert detail.status_code == 200


@pytest.mark.asyncio
async def test_get_constructor_by_id_when_exists(async_client):
    list_resp = await async_client.get("/api/v1/constructors/?limit=1")
    cid = list_resp.json()[0]["id"]
    detail = await async_client.get(f"/api/v1/constructors/{cid}")
    assert detail.status_code == 200


@pytest.mark.asyncio
async def test_get_race_by_id_when_exists(async_client):
    list_resp = await async_client.get("/api/v1/races/?limit=1")
    rid = list_resp.json()[0]["id"]
    detail = await async_client.get(f"/api/v1/races/{rid}")
    assert detail.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# Results / Qualifying / Sprint
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_results_by_season(async_client):
    response = await async_client.get("/api/v1/results/?season=2023&limit=5")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_list_results_by_race_id(async_client):
    races = (await async_client.get("/api/v1/races/?season=2023")).json()
    race_id = races[0]["id"]
    response = await async_client.get(f"/api/v1/results/?race_id={race_id}&limit=5")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_list_results_by_driver_id(async_client):
    drivers = (await async_client.get("/api/v1/drivers/?limit=5")).json()
    ver = next(d for d in drivers if d["code"] == "VER")
    response = await async_client.get(f"/api/v1/results/?driver_id={ver['id']}&limit=5")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_qualifying(async_client):
    response = await async_client.get("/api/v1/qualifying/?season=2023&limit=5")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_list_qualifying_by_race(async_client):
    races = (await async_client.get("/api/v1/races/?season=2023")).json()
    race_id = races[0]["id"]
    response = await async_client.get(
        f"/api/v1/qualifying/?race_id={race_id}&limit=5"
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_sprint_by_season(async_client):
    response = await async_client.get("/api/v1/sprint/?season=2023&limit=5")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_list_sprint_by_race(async_client):
    races = (await async_client.get("/api/v1/races/?season=2023")).json()
    race_id = races[0]["id"]
    response = await async_client.get(f"/api/v1/sprint/?race_id={race_id}&limit=5")
    assert response.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# Pit Stops / Laps / Statuses
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_pit_stops_by_race(async_client):
    races = (await async_client.get("/api/v1/races/?season=2023")).json()
    race_id = races[0]["id"]
    response = await async_client.get(
        f"/api/v1/pitstops/?race_id={race_id}&limit=10"
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_list_pit_stops_by_driver(async_client):
    drivers = (await async_client.get("/api/v1/drivers/?limit=5")).json()
    ver = next(d for d in drivers if d["code"] == "VER")
    response = await async_client.get(
        f"/api/v1/pitstops/?driver_id={ver['id']}&limit=10"
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_lap_times_by_race(async_client):
    races = (await async_client.get("/api/v1/races/?season=2023")).json()
    race_id = races[0]["id"]
    response = await async_client.get(f"/api/v1/laps/?race_id={race_id}&limit=10")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_lap_times_by_driver(async_client):
    drivers = (await async_client.get("/api/v1/drivers/?limit=5")).json()
    ver = next(d for d in drivers if d["code"] == "VER")
    response = await async_client.get(
        f"/api/v1/laps/?driver_id={ver['id']}&limit=10"
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_statuses(async_client):
    response = await async_client.get("/api/v1/statuses/?limit=10")
    assert response.status_code == 200
    assert len(response.json()) == 2
