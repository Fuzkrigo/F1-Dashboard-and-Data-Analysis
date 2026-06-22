"""
Telemetry API Route Definitions Module (V2 - Multi-Driver).

[EN] Defines the FastAPI route handlers for the FastF1 live timing engine.
Exposes real telemetry traces (Speed, Gear, RPM, Throttle, Brake)
and track location data (X,Y,Z) for multiple drivers simultaneously.

[PT-BR] Define os handlers de rotas do FastAPI para a engine de live timing FastF1.
Expoe rastros reais de telemetria e coordenadas espaciais da pista
para multiplos pilotos simultaneamente.

Author: Bruno Krieger
"""

import logging
from pathlib import Path
from typing import Any

import fastf1
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

# Configure FastF1 caching (CRITICAL for performance)
CACHE_DIR = Path(__file__).parent.parent.parent / ".cache_fastf1"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
fastf1.Cache.enable_cache(str(CACHE_DIR))

router = APIRouter()


def _sanitize_nan(val: Any) -> Any:
    """Helper to convert pandas NaN/NaT to None for JSON serialization."""
    if pd.isna(val):
        return None
    return val


@router.get("/telemetry/", tags=["Telemetry"])
async def get_telemetry(
    year: int = Query(..., description="Season year (e.g. 2023)"),
    round_num: int = Query(..., description="Round number (e.g. 1)"),
    drivers: list[str] = Query(
        ..., description="List of three-letter driver codes (e.g. VER, HAM)"
    ),
    session_type: str = Query(
        "R", description="Session type (R for Race, Q for Qualifying)"
    ),
):
    """
    Get Lap Chart + KPI data for Multiple Drivers.

    [EN] Returns lap times, compounds, and track map for the selected drivers.
    Telemetry detail is NOT included - use /telemetry/lap/ for specific laps.
    [PT-BR] Retorna tempos de volta, compostos e mapa para os pilotos selecionados.
    Telemetria detalhada NAO inclusa - use /telemetry/lap/ para voltas especificas.
    """
    try:
        session_obj = fastf1.get_session(year, round_num, session_type)
        session_obj.load(telemetry=True, weather=False, messages=False, livedata=None)

        laps = session_obj.laps
        response_data = {"drivers": {}, "track_map": None}

        for driver_code in drivers:
            try:
                drv_laps = laps.pick_driver(driver_code)
                if drv_laps.empty:
                    logger.warning(f"No laps found for driver {driver_code}")
                    continue

                drv_fastest = drv_laps.pick_fastest()
                if pd.isna(drv_fastest["LapTime"]):
                    logger.warning(f"No valid fastest lap for {driver_code}")
                    continue

                drv_laps_clean = drv_laps[pd.notna(drv_laps["LapTime"])]

                response_data["drivers"][driver_code] = {
                    "name": driver_code,
                    "fastest_lap_time": str(drv_fastest["LapTime"])[-12:],
                    "compound": str(drv_fastest["Compound"]),
                    "team": str(drv_fastest["Team"]),
                    "lap_chart": {
                        "lap_number": [
                            _sanitize_nan(x) for x in drv_laps_clean["LapNumber"]
                        ],
                        "lap_time": [
                            _sanitize_nan(x)
                            for x in drv_laps_clean["LapTime"].dt.total_seconds()
                        ],
                        "compound": [
                            _sanitize_nan(x) for x in drv_laps_clean["Compound"]
                        ],
                    },
                }

                # Capture Track Map from the first valid driver fastest lap
                if response_data["track_map"] is None:
                    drv_tel = drv_fastest.get_telemetry()
                    response_data["track_map"] = {
                        "x": [_sanitize_nan(x) for x in drv_tel["X"]],
                        "y": [_sanitize_nan(x) for x in drv_tel["Y"]],
                    }

            except Exception as e_driver:
                logger.warning(f"Error parsing driver {driver_code}: {e_driver}")
                continue

        if not response_data["drivers"]:
            raise HTTPException(
                status_code=404,
                detail="No telemetry could be processed for any of the selected drivers.",
            )

        return response_data

    except HTTPException:
        # Re-raise explicit HTTP errors without wrapping them as 500
        # Re-lança erros HTTP explícitos sem encapsulá-los como 500
        raise
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"FastF1 data error: {str(e)}")
    except Exception as e:
        logger.exception("Unexpected error in telemetry endpoint")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/telemetry/lap/", tags=["Telemetry"])
async def get_lap_telemetry(
    year: int = Query(..., description="Season year (e.g. 2023)"),
    round_num: int = Query(..., description="Round number (e.g. 1)"),
    driver: str = Query(..., description="Three-letter driver code (e.g. VER)"),
    lap_number: int = Query(..., description="Lap number to fetch telemetry for"),
    session_type: str = Query(
        "R", description="Session type (R for Race, Q for Qualifying)"
    ),
):
    """
    Get Telemetry for a Specific Lap of a Specific Driver.

    [EN] Returns precise telemetry arrays (Speed, Gear, RPM, Throttle, Brake)
    for the requested lap number of the given driver.
    [PT-BR] Retorna arrays de telemetria precisa para a volta solicitada do piloto.
    """
    try:
        session_obj = fastf1.get_session(year, round_num, session_type)
        session_obj.load(telemetry=True, weather=False, messages=False, livedata=None)

        laps = session_obj.laps
        drv_laps = laps.pick_driver(driver)

        if drv_laps.empty:
            raise HTTPException(
                status_code=404, detail=f"No laps found for driver {driver}"
            )

        # Filter for the specific lap number
        target_lap = drv_laps[drv_laps["LapNumber"] == lap_number]

        if target_lap.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Lap {lap_number} not found for driver {driver}",
            )

        lap_row = target_lap.iloc[0]
        lap_tel = lap_row.get_telemetry()
        lap_tel["Distance"] = lap_tel["Distance"] - lap_tel["Distance"].iloc[0]

        lap_time_str = str(lap_row["LapTime"])[-12:] if pd.notna(lap_row["LapTime"]) else "N/A"

        return {
            "driver": driver,
            "lap_number": int(lap_number),
            "lap_time": lap_time_str,
            "compound": str(lap_row["Compound"]),
            "team": str(lap_row["Team"]),
            "telemetry": {
                "distance": [_sanitize_nan(x) for x in lap_tel["Distance"]],
                "speed": [_sanitize_nan(x) for x in lap_tel["Speed"]],
                "gear": [_sanitize_nan(x) for x in lap_tel["nGear"]],
                "rpm": [_sanitize_nan(x) for x in lap_tel["RPM"]],
                "throttle": [_sanitize_nan(x) for x in lap_tel["Throttle"]],
                "brake": [_sanitize_nan(x) for x in lap_tel["Brake"]],
                "drs": [_sanitize_nan(x) for x in lap_tel["DRS"]],
            },
        }

    except HTTPException:
        # Re-raise explicit HTTP errors without wrapping them as 500
        # Re-lança erros HTTP explícitos sem encapsulá-los como 500
        raise
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"FastF1 data error: {str(e)}")
    except Exception as e:
        logger.exception("Unexpected error in telemetry endpoint")
        raise HTTPException(status_code=500, detail=str(e))
