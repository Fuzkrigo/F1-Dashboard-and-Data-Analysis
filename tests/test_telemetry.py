"""
Tests for the FastF1 telemetry endpoints.

[EN] Mocks the entire FastF1 dependency (sessions, laps, telemetry frames)
to validate the API contract without needing real network calls or large
cache downloads. Verifies happy paths, missing-driver fallbacks, and
multi-driver responses.

[PT-BR] Mocka completamente a dependência do FastF1 (sessões, voltas,
quadros de telemetria) para validar o contrato da API sem precisar de
chamadas reais à rede ou downloads grandes de cache. Verifica caminhos
felizes, fallback para piloto ausente e respostas multi-piloto.
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from httpx import ASGITransport, AsyncClient

from src.api.main import app


@pytest.fixture
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


# ─────────────────────────────────────────────────────────────────────────────
# Fixture builders / Construtores de fixture
# ─────────────────────────────────────────────────────────────────────────────


def _build_telemetry_frame():
    """Returns a fake DataFrame mimicking FastF1 .get_telemetry() output."""
    return pd.DataFrame(
        {
            "Distance": [0.0, 100.0, 200.0],
            "Speed": [200, 250, 280],
            "nGear": [4, 5, 6],
            "RPM": [10000, 11000, 12000],
            "Throttle": [50, 80, 100],
            "Brake": [False, False, False],
            "DRS": [0, 1, 1],
            "X": [1.0, 2.0, 3.0],
            "Y": [10.0, 20.0, 30.0],
        }
    )


def _build_fastest_lap(driver_code="VER", team="Red Bull"):
    """Returns a Mock Series mimicking a FastF1 fastest lap row."""
    fastest = MagicMock()
    fastest.__getitem__.side_effect = lambda key: {
        "LapTime": pd.Timedelta(seconds=90.5),
        "Compound": "MEDIUM",
        "Team": team,
        "LapNumber": 15,
    }[key]
    fastest.get_telemetry.return_value = _build_telemetry_frame()
    return fastest


def _build_drv_laps(driver_code="VER", team="Red Bull"):
    """Returns a Mock mimicking session.laps.pick_driver(code) result."""
    drv_laps = MagicMock()
    drv_laps.empty = False
    drv_laps.pick_fastest.return_value = _build_fastest_lap(driver_code, team)

    # Simulate filtered laps DataFrame for lap_chart construction
    lap_df = pd.DataFrame(
        {
            "LapTime": [
                pd.Timedelta(seconds=91.0),
                pd.Timedelta(seconds=90.5),
                pd.Timedelta(seconds=90.8),
            ],
            "LapNumber": [1, 2, 3],
            "Compound": ["MEDIUM", "MEDIUM", "MEDIUM"],
        }
    )
    drv_laps.__getitem__.return_value = lap_df
    return drv_laps


def _build_session():
    """Returns a Mock session compatible with telemetry endpoint usage."""
    session = MagicMock()
    session.load.return_value = None
    laps = MagicMock()
    laps.pick_driver.return_value = _build_drv_laps()
    session.laps = laps
    return session


# ─────────────────────────────────────────────────────────────────────────────
# /telemetry/ — multi-driver
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_telemetry_happy_path(async_client):
    """Happy path: one driver, valid session, full payload returned."""
    with patch("src.api.telemetry.fastf1.get_session") as mock_get_session:
        mock_get_session.return_value = _build_session()
        response = await async_client.get(
            "/api/v1/telemetry/?year=2023&round_num=1&drivers=VER&session_type=R"
        )
        assert response.status_code == 200
        data = response.json()
        assert "drivers" in data
        assert "track_map" in data
        assert "VER" in data["drivers"]
        assert data["drivers"]["VER"]["compound"] == "MEDIUM"


@pytest.mark.asyncio
async def test_telemetry_multiple_drivers(async_client):
    """Multiple drivers: each appears in the response."""
    with patch("src.api.telemetry.fastf1.get_session") as mock_get_session:
        mock_get_session.return_value = _build_session()
        response = await async_client.get(
            "/api/v1/telemetry/?year=2023&round_num=1&drivers=VER&drivers=HAM"
        )
        assert response.status_code == 200
        data = response.json()
        assert "VER" in data["drivers"]
        assert "HAM" in data["drivers"]


@pytest.mark.asyncio
async def test_telemetry_missing_required_param(async_client):
    """No drivers query param -> 422 Unprocessable Entity."""
    response = await async_client.get(
        "/api/v1/telemetry/?year=2023&round_num=1"
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_telemetry_no_drivers_processed_returns_404(async_client):
    """If all driver lookups return empty laps, endpoint returns 404."""
    session = MagicMock()
    session.load.return_value = None
    empty_drv_laps = MagicMock()
    empty_drv_laps.empty = True
    session.laps = MagicMock()
    session.laps.pick_driver.return_value = empty_drv_laps

    with patch("src.api.telemetry.fastf1.get_session") as mock_get_session:
        mock_get_session.return_value = session
        response = await async_client.get(
            "/api/v1/telemetry/?year=2023&round_num=1&drivers=GHOST"
        )
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_telemetry_fastf1_failure_returns_500(async_client):
    """If fastf1.get_session raises, the endpoint returns a 500 error."""
    with patch("src.api.telemetry.fastf1.get_session") as mock_get_session:
        mock_get_session.side_effect = RuntimeError("FastF1 service down")
        response = await async_client.get(
            "/api/v1/telemetry/?year=2099&round_num=1&drivers=VER"
        )
        assert response.status_code == 500


# ─────────────────────────────────────────────────────────────────────────────
# /telemetry/lap/ — single lap detail
# ─────────────────────────────────────────────────────────────────────────────


def _build_session_with_specific_lap(lap_number=15):
    """Builds a session whose laps DataFrame includes a row at lap_number."""
    session = MagicMock()
    session.load.return_value = None

    # The endpoint calls drv_laps[drv_laps["LapNumber"] == lap_number]
    # which must return a DataFrame with .empty=False and .iloc[0]
    target_row = MagicMock()
    target_row.__getitem__.side_effect = lambda key: {
        "LapTime": pd.Timedelta(seconds=90.5),
        "Compound": "MEDIUM",
        "Team": "Red Bull",
    }[key]
    target_row.get_telemetry.return_value = _build_telemetry_frame()

    target_lap_df = MagicMock()
    target_lap_df.empty = False
    target_lap_df.iloc = MagicMock()
    target_lap_df.iloc.__getitem__.return_value = target_row

    drv_laps = MagicMock()
    drv_laps.empty = False
    drv_laps.__getitem__.return_value = target_lap_df

    session.laps = MagicMock()
    session.laps.pick_driver.return_value = drv_laps
    return session


@pytest.mark.asyncio
async def test_lap_telemetry_happy_path(async_client):
    with patch("src.api.telemetry.fastf1.get_session") as mock_get_session:
        mock_get_session.return_value = _build_session_with_specific_lap(15)
        response = await async_client.get(
            "/api/v1/telemetry/lap/?year=2023&round_num=1&driver=VER&lap_number=15"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["driver"] == "VER"
        assert data["lap_number"] == 15
        assert "telemetry" in data
        assert len(data["telemetry"]["distance"]) == 3


@pytest.mark.asyncio
async def test_lap_telemetry_missing_param(async_client):
    """Missing lap_number -> 422."""
    response = await async_client.get(
        "/api/v1/telemetry/lap/?year=2023&round_num=1&driver=VER"
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_lap_telemetry_unknown_driver(async_client):
    """Driver with no laps -> 404."""
    session = MagicMock()
    session.load.return_value = None
    empty = MagicMock()
    empty.empty = True
    session.laps = MagicMock()
    session.laps.pick_driver.return_value = empty

    with patch("src.api.telemetry.fastf1.get_session") as mock_get_session:
        mock_get_session.return_value = session
        response = await async_client.get(
            "/api/v1/telemetry/lap/?year=2023&round_num=1&driver=GHOST&lap_number=1"
        )
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_lap_telemetry_lap_not_found(async_client):
    """Lap number not present in driver's laps -> 404."""
    session = MagicMock()
    session.load.return_value = None
    empty_lap_df = MagicMock()
    empty_lap_df.empty = True

    drv_laps = MagicMock()
    drv_laps.empty = False
    drv_laps.__getitem__.return_value = empty_lap_df

    session.laps = MagicMock()
    session.laps.pick_driver.return_value = drv_laps

    with patch("src.api.telemetry.fastf1.get_session") as mock_get_session:
        mock_get_session.return_value = session
        response = await async_client.get(
            "/api/v1/telemetry/lap/?year=2023&round_num=1&driver=VER&lap_number=999"
        )
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_lap_telemetry_fastf1_failure(async_client):
    with patch("src.api.telemetry.fastf1.get_session") as mock_get_session:
        mock_get_session.side_effect = RuntimeError("network down")
        response = await async_client.get(
            "/api/v1/telemetry/lap/?year=2023&round_num=1&driver=VER&lap_number=1"
        )
        assert response.status_code == 500


# ─────────────────────────────────────────────────────────────────────────────
# Helper _sanitize_nan
# ─────────────────────────────────────────────────────────────────────────────


def test_sanitize_nan_handles_nat_and_nan():
    from src.api.telemetry import _sanitize_nan

    assert _sanitize_nan(pd.NaT) is None
    assert _sanitize_nan(float("nan")) is None
    assert _sanitize_nan(42) == 42
    assert _sanitize_nan("ok") == "ok"
