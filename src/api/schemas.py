"""
Pydantic Schema Definitions Module.

[EN] Defines Pydantic models (schemas) used for request/response validation
and serialization in the F1 Insights API. Includes schemas for seasons,
circuits, races, drivers, constructors, race results, sprint results,
qualifying results, championship standings, pit stops, lap times, and
finishing statuses.

[PT-BR] Define os modelos Pydantic (schemas) utilizados para validação e
serialização de requisições/respostas na API do F1 Insights. Inclui schemas
para temporadas, circuitos, corridas, pilotos, construtores, resultados de
corridas, resultados de sprint, resultados de classificação, classificações
de campeonato, pit stops, tempos de volta e status de finalização.

Author: Bruno Krieger
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict

# ─────────────────────────────────────────────────────────────────────────────
# Circuit Schemas
# ─────────────────────────────────────────────────────────────────────────────


class CircuitBase(BaseModel):
    """
    Base schema for a Formula 1 circuit.

    [EN] Common fields for circuit data.
    [PT-BR] Campos comuns para dados de circuito.

    Author: Bruno Krieger
    """

    circuit_ref: str
    circuit_name: str
    location: str
    country: str
    latitude: float
    longitude: float
    url: str


class Circuit(CircuitBase):
    """
    Schema for reading a circuit from the database.

    [EN] Extends CircuitBase with the database-generated id.
    [PT-BR] Estende CircuitBase com o id gerado pelo banco.

    Author: Bruno Krieger
    """

    id: int

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# Driver Schemas
# ─────────────────────────────────────────────────────────────────────────────


class DriverBase(BaseModel):
    """
    Base schema for a Formula 1 driver.

    [EN] Common fields for driver data.
    [PT-BR] Campos comuns para dados de piloto.

    Author: Bruno Krieger
    """

    driver_ref: str
    permanent_number: Optional[int] = None
    code: Optional[str] = None
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    nationality: str
    url: str


class Driver(DriverBase):
    """
    Schema for reading a driver from the database.

    [EN] Extends DriverBase with the database-generated id.
    [PT-BR] Estende DriverBase com o id gerado pelo banco.

    Author: Bruno Krieger
    """

    id: int

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# Constructor Schemas
# ─────────────────────────────────────────────────────────────────────────────


class ConstructorBase(BaseModel):
    """
    Base schema for a Formula 1 constructor (team).

    [EN] Common fields for constructor data.
    [PT-BR] Campos comuns para dados de construtor/equipe.

    Author: Bruno Krieger
    """

    constructor_ref: str
    constructor_name: str
    nationality: str
    url: str


class Constructor(ConstructorBase):
    """
    Schema for reading a constructor from the database.

    [EN] Extends ConstructorBase with the database-generated id.
    [PT-BR] Estende ConstructorBase com o id gerado pelo banco.

    Author: Bruno Krieger
    """

    id: int

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# Race Schemas
# ─────────────────────────────────────────────────────────────────────────────


class RaceBase(BaseModel):
    """
    Base schema for a Formula 1 race.

    [EN] Common fields for race data.
    [PT-BR] Campos comuns para dados de corrida.

    Author: Bruno Krieger
    """

    season: int
    round: int
    url: str
    race_name: str
    circuit_id: Optional[int] = None
    circuit_name: str
    date: date


class Race(RaceBase):
    """
    Schema for reading a race from the database.

    [EN] Extends RaceBase with the database-generated id.
    [PT-BR] Estende RaceBase com o id gerado pelo banco.

    Author: Bruno Krieger
    """

    id: int

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# RaceResult Schemas
# ─────────────────────────────────────────────────────────────────────────────


class RaceResultBase(BaseModel):
    """
    Base schema for a race result.

    [EN] Common fields for race result data.
    [PT-BR] Campos comuns para dados de resultado de corrida.

    Author: Bruno Krieger
    """

    race_id: int
    driver_id: int
    constructor_id: int
    grid: int
    position: Optional[int] = None
    position_text: str
    points: float
    laps: int
    time_result: Optional[str] = None
    fastest_lap_time: Optional[str] = None
    fastest_lap_speed: Optional[float] = None
    status: str


class RaceResult(RaceResultBase):
    """
    Schema for reading a race result from the database.

    [EN] Extends RaceResultBase with the database-generated id.
    [PT-BR] Estende RaceResultBase com o id gerado pelo banco.

    Author: Bruno Krieger
    """

    id: int

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# QualifyingResult Schemas
# ─────────────────────────────────────────────────────────────────────────────


class QualifyingResultBase(BaseModel):
    """
    Base schema for a qualifying result.

    [EN] Common fields for qualifying result data.
    [PT-BR] Campos comuns para dados de resultado de classificação.

    Author: Bruno Krieger
    """

    race_id: int
    driver_id: int
    constructor_id: int
    position: int
    q1: Optional[str] = None
    q2: Optional[str] = None
    q3: Optional[str] = None


class QualifyingResult(QualifyingResultBase):
    """
    Schema for reading a qualifying result from the database.

    [EN] Extends QualifyingResultBase with the database-generated id.
    [PT-BR] Estende QualifyingResultBase com o id gerado pelo banco.

    Author: Bruno Krieger
    """

    id: int

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# DriverStanding Schemas
# ─────────────────────────────────────────────────────────────────────────────


class DriverStandingBase(BaseModel):
    """
    Base schema for a driver championship standing.

    [EN] Common fields for driver standing data.
    [PT-BR] Campos comuns para dados de classificação de piloto.

    Author: Bruno Krieger
    """

    race_id: int
    driver_id: int
    points: float
    position: int
    wins: int


class DriverStanding(DriverStandingBase):
    """
    Schema for reading a driver standing from the database.

    [EN] Extends DriverStandingBase with the database-generated id.
    [PT-BR] Estende DriverStandingBase com o id gerado pelo banco.

    Author: Bruno Krieger
    """

    id: int

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# ConstructorStanding Schemas
# ─────────────────────────────────────────────────────────────────────────────


class ConstructorStandingBase(BaseModel):
    """
    Base schema for a constructor championship standing.

    [EN] Common fields for constructor standing data.
    [PT-BR] Campos comuns para dados de classificação de construtor.

    Author: Bruno Krieger
    """

    race_id: int
    constructor_id: int
    points: float
    position: int
    wins: int


class ConstructorStanding(ConstructorStandingBase):
    """
    Schema for reading a constructor standing from the database.

    [EN] Extends ConstructorStandingBase with the database-generated id.
    [PT-BR] Estende ConstructorStandingBase com o id gerado pelo banco.

    Author: Bruno Krieger
    """

    id: int

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# PitStop Schemas
# ─────────────────────────────────────────────────────────────────────────────


class PitStopBase(BaseModel):
    """
    Base schema for a pit stop.

    [EN] Common fields for pit stop data.
    [PT-BR] Campos comuns para dados de pit stop.

    Author: Bruno Krieger
    """

    race_id: int
    driver_id: int
    stop: int
    lap: int
    time_of_day: Optional[str] = None
    duration: Optional[str] = None
    duration_ms: Optional[int] = None


class PitStop(PitStopBase):
    """
    Schema for reading a pit stop from the database.

    [EN] Extends PitStopBase with the database-generated id.
    [PT-BR] Estende PitStopBase com o id gerado pelo banco.

    Author: Bruno Krieger
    """

    id: int

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# Season Schemas
# ─────────────────────────────────────────────────────────────────────────────


class SeasonBase(BaseModel):
    """
    Base schema for a Formula 1 season.

    [EN] Common fields for season data.
    [PT-BR] Campos comuns para dados de temporada.

    Author: Bruno Krieger
    """

    year: int
    url: str


class Season(SeasonBase):
    """
    Schema for reading a season from the database.

    [EN] Extends SeasonBase with the database-generated id.
    [PT-BR] Estende SeasonBase com o id gerado pelo banco.

    Author: Bruno Krieger
    """

    id: int

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# SprintResult Schemas
# ─────────────────────────────────────────────────────────────────────────────


class SprintResultBase(BaseModel):
    """
    Base schema for a sprint race result.

    [EN] Common fields for sprint result data.
    [PT-BR] Campos comuns para dados de resultado de sprint.

    Author: Bruno Krieger
    """

    race_id: int
    driver_id: int
    constructor_id: int
    grid: int
    position: Optional[int] = None
    position_text: str
    points: float
    laps: int
    time_result: Optional[str] = None
    fastest_lap_time: Optional[str] = None
    status: str


class SprintResult(SprintResultBase):
    """
    Schema for reading a sprint result from the database.

    [EN] Extends SprintResultBase with the database-generated id.
    [PT-BR] Estende SprintResultBase com o id gerado pelo banco.

    Author: Bruno Krieger
    """

    id: int

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# LapTime Schemas
# ─────────────────────────────────────────────────────────────────────────────


class LapTimeBase(BaseModel):
    """
    Base schema for a lap time.

    [EN] Common fields for lap time data.
    [PT-BR] Campos comuns para dados de tempo de volta.

    Author: Bruno Krieger
    """

    race_id: int
    driver_id: int
    lap: int
    position: int
    time: Optional[str] = None
    time_ms: Optional[int] = None


class LapTime(LapTimeBase):
    """
    Schema for reading a lap time from the database.

    [EN] Extends LapTimeBase with the database-generated id.
    [PT-BR] Estende LapTimeBase com o id gerado pelo banco.

    Author: Bruno Krieger
    """

    id: int

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# Status Schemas
# ─────────────────────────────────────────────────────────────────────────────


class StatusBase(BaseModel):
    """
    Base schema for a race finishing status.

    [EN] Common fields for status data.
    [PT-BR] Campos comuns para dados de status.

    Author: Bruno Krieger
    """

    status: str
    count: Optional[int] = None


class Status(StatusBase):
    """
    Schema for reading a status from the database.

    [EN] Extends StatusBase with the database-generated id.
    [PT-BR] Estende StatusBase com o id gerado pelo banco.

    Author: Bruno Krieger
    """

    id: int

    model_config = ConfigDict(from_attributes=True)
