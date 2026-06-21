"""
Database Models Module.

[EN] Defines the SQLAlchemy ORM models that represent the database tables
for the F1 Insights application. Contains models for seasons, circuits,
races, drivers, constructors, race results, sprint results, qualifying
results, championship standings, pit stops, lap times, and finishing
statuses — covering all data entities from the Ergast/Jolpica F1 API.

[PT-BR] Define os modelos ORM do SQLAlchemy que representam as tabelas do
banco de dados da aplicação F1 Insights. Contém modelos para temporadas,
circuitos, corridas, pilotos, construtores, resultados de corridas,
resultados de sprint, resultados de classificação, classificações de
campeonato, pit stops, tempos de volta e status de finalização —
cobrindo todas as entidades de dados da API Ergast/Jolpica F1.

Author: Bruno Krieger
"""

from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base

# ─────────────────────────────────────────────────────────────────────────────
# Circuit
# ─────────────────────────────────────────────────────────────────────────────


class Circuit(Base):
    """
    ORM model representing a Formula 1 circuit.

    [EN] Maps to the 'circuits' table. Stores information about each
    racing circuit, including its name, location, country, geographic
    coordinates, and Wikipedia URL.

    [PT-BR] Mapeia para a tabela 'circuits'. Armazena informações sobre
    cada circuito de corrida, incluindo nome, localização, país,
    coordenadas geográficas e URL da Wikipedia.

    Attributes:
        id (int): Primary key. / Chave primária.
        circuit_ref (str): Unique short identifier (e.g. "monza").
        circuit_ref (str): Identificador curto único (ex: "monza").
        circuit_name (str): Official circuit name. / Nome oficial do circuito.
        location (str): City where the circuit is located. /
                        Cidade onde o circuito está localizado.
        country (str): Country of the circuit. / País do circuito.
        latitude (float): Geographic latitude. / Latitude geográfica.
        longitude (float): Geographic longitude. / Longitude geográfica.
        url (str): Wikipedia URL. / URL da Wikipedia.

    Author: Bruno Krieger
    """

    __tablename__ = "circuits"

    id = Column(Integer, primary_key=True, index=True)
    circuit_ref = Column(String, unique=True, index=True)
    circuit_name = Column(String)
    location = Column(String)
    country = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    url = Column(String)

    # Relationships / Relacionamentos
    races = relationship("Race", back_populates="circuit")

    def __repr__(self):
        """
        Return a string representation of the Circuit instance.

        [EN] Returns a human-readable string for debugging.
        [PT-BR] Retorna uma string legível para depuração.

        Author: Bruno Krieger
        """
        return f"<Circuit(name='{self.circuit_name}', country='{self.country}')>"


# ─────────────────────────────────────────────────────────────────────────────
# Driver
# ─────────────────────────────────────────────────────────────────────────────


class Driver(Base):
    """
    ORM model representing a Formula 1 driver.

    [EN] Maps to the 'drivers' table. Stores biographical and career
    information about each driver, including name, nationality, date of
    birth, permanent number, and driver code.

    [PT-BR] Mapeia para a tabela 'drivers'. Armazena informações
    biográficas e de carreira de cada piloto, incluindo nome,
    nacionalidade, data de nascimento, número permanente e código.

    Attributes:
        id (int): Primary key. / Chave primária.
        driver_ref (str): Unique short identifier (e.g. "hamilton").
                          Identificador curto único (ex: "hamilton").
        permanent_number (int): Permanent car number. / Número permanente.
        code (str): Three-letter driver code (e.g. "HAM"). /
                    Código de três letras (ex: "HAM").
        first_name (str): Driver's first name. / Primeiro nome do piloto.
        last_name (str): Driver's last name. / Sobrenome do piloto.
        date_of_birth (date): Date of birth. / Data de nascimento.
        nationality (str): Nationality. / Nacionalidade.
        url (str): Wikipedia URL. / URL da Wikipedia.

    Author: Bruno Krieger
    """

    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    driver_ref = Column(String, unique=True, index=True)
    permanent_number = Column(Integer, nullable=True)
    code = Column(String(3), nullable=True)
    first_name = Column(String)
    last_name = Column(String)
    date_of_birth = Column(Date, nullable=True)
    nationality = Column(String, index=True)
    url = Column(String)

    # Relationships / Relacionamentos
    race_results = relationship("RaceResult", back_populates="driver")
    qualifying_results = relationship("QualifyingResult", back_populates="driver")
    standings = relationship("DriverStanding", back_populates="driver")
    pit_stops = relationship("PitStop", back_populates="driver")
    sprint_results = relationship("SprintResult", back_populates="driver")
    lap_times = relationship("LapTime", back_populates="driver")

    def __repr__(self):
        """
        Return a string representation of the Driver instance.

        [EN] Returns a human-readable string for debugging.
        [PT-BR] Retorna uma string legível para depuração.

        Author: Bruno Krieger
        """
        return (
            f"<Driver(code='{self.code}', name='{self.first_name} {self.last_name}')>"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Constructor (Team)
# ─────────────────────────────────────────────────────────────────────────────


class Constructor(Base):
    """
    ORM model representing a Formula 1 constructor (team).

    [EN] Maps to the 'constructors' table. Stores information about each
    racing team, including name, nationality, and Wikipedia URL.

    [PT-BR] Mapeia para a tabela 'constructors'. Armazena informações
    sobre cada equipe de corrida, incluindo nome, nacionalidade e URL
    da Wikipedia.

    Attributes:
        id (int): Primary key. / Chave primária.
        constructor_ref (str): Unique short identifier (e.g. "mclaren").
                               Identificador curto único (ex: "mclaren").
        constructor_name (str): Official team name. / Nome oficial da equipe.
        nationality (str): Team nationality. / Nacionalidade da equipe.
        url (str): Wikipedia URL. / URL da Wikipedia.

    Author: Bruno Krieger
    """

    __tablename__ = "constructors"

    id = Column(Integer, primary_key=True, index=True)
    constructor_ref = Column(String, unique=True, index=True)
    constructor_name = Column(String)
    nationality = Column(String, index=True)
    url = Column(String)

    # Relationships / Relacionamentos
    race_results = relationship("RaceResult", back_populates="constructor")
    standings = relationship("ConstructorStanding", back_populates="constructor")

    def __repr__(self):
        """
        Return a string representation of the Constructor instance.

        [EN] Returns a human-readable string for debugging.
        [PT-BR] Retorna uma string legível para depuração.

        Author: Bruno Krieger
        """
        return f"<Constructor(name='{self.constructor_name}')>"


# ─────────────────────────────────────────────────────────────────────────────
# Race (updated with Circuit relationship)
# ─────────────────────────────────────────────────────────────────────────────


class Race(Base):
    """
    ORM model representing a Formula 1 race.

    [EN] Maps to the 'races' table. Stores information about individual
    Formula 1 races, including season, round number, name, date, and a
    foreign key linking to the circuit where the race took place.

    [PT-BR] Mapeia para a tabela 'races'. Armazena informações sobre
    corridas individuais de Fórmula 1, incluindo temporada, número da
    rodada, nome, data e uma chave estrangeira para o circuito onde a
    corrida aconteceu.

    Attributes:
        id (int): Primary key. / Chave primária.
        season (int): The season year. / O ano da temporada.
        round (int): The round number within the season. / Número da rodada.
        url (str): Wikipedia URL for the race. / URL da Wikipedia da corrida.
        race_name (str): Official name of the race. / Nome oficial da corrida.
        circuit_id (int): Foreign key to circuits table. / Chave estrangeira
            para a tabela circuits.
        circuit_name (str): Circuit name (denormalized for convenience). /
            Nome do circuito (desnormalizado por conveniência).
        date (date): Date the race took place. / Data da corrida.

    Author: Bruno Krieger
    """

    __tablename__ = "races"

    id = Column(Integer, primary_key=True, index=True)
    season = Column(Integer, index=True)
    round = Column(Integer, index=True)
    url = Column(String)
    race_name = Column(String)
    circuit_id = Column(Integer, ForeignKey("circuits.id"), nullable=True)
    circuit_name = Column(String)
    date = Column(Date)

    # Relationships / Relacionamentos
    circuit = relationship("Circuit", back_populates="races")
    results = relationship("RaceResult", back_populates="race")
    qualifying_results = relationship("QualifyingResult", back_populates="race")
    driver_standings = relationship("DriverStanding", back_populates="race")
    constructor_standings = relationship("ConstructorStanding", back_populates="race")
    pit_stops = relationship("PitStop", back_populates="race")
    sprint_results = relationship("SprintResult", back_populates="race")
    lap_times = relationship("LapTime", back_populates="race")

    def __repr__(self):
        """
        Return a string representation of the Race instance.

        [EN] Returns a human-readable string for debugging.
        [PT-BR] Retorna uma string legível para depuração.

        Author: Bruno Krieger
        """
        return (
            f"<Race(season={self.season}, round={self.round}, name='{self.race_name}')>"
        )


# ─────────────────────────────────────────────────────────────────────────────
# RaceResult
# ─────────────────────────────────────────────────────────────────────────────


class RaceResult(Base):
    """
    ORM model representing a driver's result in a specific race.

    [EN] Maps to the 'race_results' table. Stores the finishing position,
    points scored, grid position, laps completed, finishing status, and
    fastest lap information for each driver in each race.

    [PT-BR] Mapeia para a tabela 'race_results'. Armazena posição de
    chegada, pontos marcados, posição no grid, voltas completadas, status
    de finalização e informações da volta mais rápida para cada piloto
    em cada corrida.

    Attributes:
        id (int): Primary key. / Chave primária.
        race_id (int): FK to races. / FK para corridas.
        driver_id (int): FK to drivers. / FK para pilotos.
        constructor_id (int): FK to constructors. / FK para construtores.
        grid (int): Starting grid position. / Posição no grid de largada.
        position (int): Finishing position (null if DNF). /
                        Posição de chegada (null se DNF).
        position_text (str): Position as text (e.g. "1", "R" for retired). /
                             Posição como texto (ex: "1", "R" para abandonou).
        points (float): Points scored. / Pontos marcados.
        laps (int): Number of laps completed. / Número de voltas completadas.
        time_result (str): Finishing time or gap to leader. /
                           Tempo de chegada ou diferença para o líder.
        fastest_lap_time (str): Fastest lap time. / Tempo da volta mais rápida.
        fastest_lap_speed (float): Fastest lap avg speed (km/h). /
                                   Velocidade média da volta mais rápida (km/h).
        status (str): Finish status (e.g. "Finished", "Engine"). /
                      Status de finalização (ex: "Finished", "Engine").

    Author: Bruno Krieger
    """

    __tablename__ = "race_results"

    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), index=True)
    constructor_id = Column(Integer, ForeignKey("constructors.id"), index=True)
    grid = Column(Integer)
    position = Column(Integer, nullable=True)
    position_text = Column(String)
    points = Column(Float)
    laps = Column(Integer)
    time_result = Column(String, nullable=True)
    fastest_lap_time = Column(String, nullable=True)
    fastest_lap_speed = Column(Float, nullable=True)
    status = Column(String)

    # Relationships / Relacionamentos
    race = relationship("Race", back_populates="results")
    driver = relationship("Driver", back_populates="race_results")
    constructor = relationship("Constructor", back_populates="race_results")

    def __repr__(self):
        """
        Return a string representation of the RaceResult instance.

        [EN] Returns a human-readable string for debugging.
        [PT-BR] Retorna uma string legível para depuração.

        Author: Bruno Krieger
        """
        return f"<RaceResult(race_id={self.race_id}, driver_id={self.driver_id}, pos={self.position})>"


# ─────────────────────────────────────────────────────────────────────────────
# QualifyingResult
# ─────────────────────────────────────────────────────────────────────────────


class QualifyingResult(Base):
    """
    ORM model representing a driver's qualifying session result.

    [EN] Maps to the 'qualifying_results' table. Stores the qualifying
    position and lap times for each of the three qualifying sessions
    (Q1, Q2, Q3) for each driver in a race weekend.

    [PT-BR] Mapeia para a tabela 'qualifying_results'. Armazena a posição
    de classificação e tempos de volta de cada uma das três sessões (Q1,
    Q2, Q3) para cada piloto em um fim de semana de corrida.

    Attributes:
        id (int): Primary key. / Chave primária.
        race_id (int): FK to races. / FK para corridas.
        driver_id (int): FK to drivers. / FK para pilotos.
        constructor_id (int): FK to constructors. / FK para construtores.
        position (int): Qualifying position. / Posição na classificação.
        q1 (str): Q1 lap time. / Tempo de volta no Q1.
        q2 (str): Q2 lap time (null if eliminated in Q1). /
                  Tempo de volta no Q2 (null se eliminado no Q1).
        q3 (str): Q3 lap time (null if eliminated in Q2). /
                  Tempo de volta no Q3 (null se eliminado no Q2).

    Author: Bruno Krieger
    """

    __tablename__ = "qualifying_results"

    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), index=True)
    constructor_id = Column(Integer, ForeignKey("constructors.id"), index=True)
    position = Column(Integer)
    q1 = Column(String, nullable=True)
    q2 = Column(String, nullable=True)
    q3 = Column(String, nullable=True)

    # Relationships / Relacionamentos
    race = relationship("Race", back_populates="qualifying_results")
    driver = relationship("Driver", back_populates="qualifying_results")
    constructor = relationship("Constructor")

    def __repr__(self):
        """
        Return a string representation of the QualifyingResult instance.

        [EN] Returns a human-readable string for debugging.
        [PT-BR] Retorna uma string legível para depuração.

        Author: Bruno Krieger
        """
        return f"<QualifyingResult(race_id={self.race_id}, driver_id={self.driver_id}, pos={self.position})>"


# ─────────────────────────────────────────────────────────────────────────────
# DriverStanding
# ─────────────────────────────────────────────────────────────────────────────


class DriverStanding(Base):
    """
    ORM model representing a driver's championship standing after a race.

    [EN] Maps to the 'driver_standings' table. Stores the cumulative
    championship points, position, and number of wins for each driver
    after each race in the season.

    [PT-BR] Mapeia para a tabela 'driver_standings'. Armazena os pontos
    acumulados do campeonato, posição e número de vitórias para cada
    piloto após cada corrida da temporada.

    Attributes:
        id (int): Primary key. / Chave primária.
        race_id (int): FK to races (standing after this race). /
                       FK para corridas (classificação após esta corrida).
        driver_id (int): FK to drivers. / FK para pilotos.
        points (float): Cumulative championship points. /
                        Pontos acumulados do campeonato.
        position (int): Championship position. / Posição no campeonato.
        wins (int): Number of wins so far in the season. /
                    Número de vitórias até o momento na temporada.

    Author: Bruno Krieger
    """

    __tablename__ = "driver_standings"

    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), index=True)
    points = Column(Float)
    position = Column(Integer)
    wins = Column(Integer)

    # Relationships / Relacionamentos
    race = relationship("Race", back_populates="driver_standings")
    driver = relationship("Driver", back_populates="standings")

    def __repr__(self):
        """
        Return a string representation of the DriverStanding instance.

        [EN] Returns a human-readable string for debugging.
        [PT-BR] Retorna uma string legível para depuração.

        Author: Bruno Krieger
        """
        return f"<DriverStanding(driver_id={self.driver_id}, pos={self.position}, pts={self.points})>"


# ─────────────────────────────────────────────────────────────────────────────
# ConstructorStanding
# ─────────────────────────────────────────────────────────────────────────────


class ConstructorStanding(Base):
    """
    ORM model representing a constructor's championship standing after a race.

    [EN] Maps to the 'constructor_standings' table. Stores the cumulative
    championship points, position, and number of wins for each constructor
    after each race in the season.

    [PT-BR] Mapeia para a tabela 'constructor_standings'. Armazena os
    pontos acumulados do campeonato, posição e número de vitórias para
    cada construtor após cada corrida da temporada.

    Attributes:
        id (int): Primary key. / Chave primária.
        race_id (int): FK to races. / FK para corridas.
        constructor_id (int): FK to constructors. / FK para construtores.
        points (float): Cumulative championship points. /
                        Pontos acumulados do campeonato.
        position (int): Championship position. / Posição no campeonato.
        wins (int): Number of wins. / Número de vitórias.

    Author: Bruno Krieger
    """

    __tablename__ = "constructor_standings"

    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), index=True)
    constructor_id = Column(Integer, ForeignKey("constructors.id"), index=True)
    points = Column(Float)
    position = Column(Integer)
    wins = Column(Integer)

    # Relationships / Relacionamentos
    race = relationship("Race", back_populates="constructor_standings")
    constructor = relationship("Constructor", back_populates="standings")

    def __repr__(self):
        """
        Return a string representation of the ConstructorStanding instance.

        [EN] Returns a human-readable string for debugging.
        [PT-BR] Retorna uma string legível para depuração.

        Author: Bruno Krieger
        """
        return f"<ConstructorStanding(constructor_id={self.constructor_id}, pos={self.position}, pts={self.points})>"


# ─────────────────────────────────────────────────────────────────────────────
# PitStop
# ─────────────────────────────────────────────────────────────────────────────


class PitStop(Base):
    """
    ORM model representing a pit stop during a race.

    [EN] Maps to the 'pit_stops' table. Stores detailed information about
    each pit stop, including which lap it occurred, the stop number, the
    time of day, and the duration of the stop.

    [PT-BR] Mapeia para a tabela 'pit_stops'. Armazena informações
    detalhadas sobre cada pit stop, incluindo em qual volta ocorreu, o
    número da parada, o horário e a duração da parada.

    Attributes:
        id (int): Primary key. / Chave primária.
        race_id (int): FK to races. / FK para corridas.
        driver_id (int): FK to drivers. / FK para pilotos.
        stop (int): Pit stop number (1st, 2nd, 3rd...). /
                    Número do pit stop (1º, 2º, 3º...).
        lap (int): Lap number when the stop occurred. /
                   Número da volta quando a parada ocorreu.
        time_of_day (str): Time of day of the stop. /
                           Hora do dia da parada.
        duration (str): Duration of the pit stop (e.g. "23.450"). /
                        Duração do pit stop (ex: "23.450").
        duration_ms (int): Duration in milliseconds. /
                           Duração em milissegundos.

    Author: Bruno Krieger
    """

    __tablename__ = "pit_stops"

    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), index=True)
    stop = Column(Integer)
    lap = Column(Integer)
    time_of_day = Column(String, nullable=True)
    duration = Column(String, nullable=True)
    duration_ms = Column(Integer, nullable=True)

    # Relationships / Relacionamentos
    race = relationship("Race", back_populates="pit_stops")
    driver = relationship("Driver", back_populates="pit_stops")

    def __repr__(self):
        """
        Return a string representation of the PitStop instance.

        [EN] Returns a human-readable string for debugging.
        [PT-BR] Retorna uma string legível para depuração.

        Author: Bruno Krieger
        """
        return f"<PitStop(race_id={self.race_id}, driver_id={self.driver_id}, lap={self.lap}, stop={self.stop})>"


# ─────────────────────────────────────────────────────────────────────────────
# Season
# ─────────────────────────────────────────────────────────────────────────────


class Season(Base):
    """
    ORM model representing a Formula 1 season.

    [EN] Maps to the 'seasons' table. Stores information about each
    F1 season, including the year and a reference URL.

    [PT-BR] Mapeia para a tabela 'seasons'. Armazena informações sobre
    cada temporada de F1, incluindo o ano e uma URL de referência.

    Attributes:
        id (int): Primary key. / Chave primária.
        year (int): Season year (e.g. 2023). / Ano da temporada (ex: 2023).
        url (str): Wikipedia URL for the season. / URL da Wikipedia da temporada.

    Author: Bruno Krieger
    """

    __tablename__ = "seasons"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, unique=True, index=True)
    url = Column(String)

    def __repr__(self):
        """
        Return a string representation of the Season instance.

        [EN] Returns a human-readable string for debugging.
        [PT-BR] Retorna uma string legível para depuração.

        Author: Bruno Krieger
        """
        return f"<Season(year={self.year})>"


# ─────────────────────────────────────────────────────────────────────────────
# SprintResult
# ─────────────────────────────────────────────────────────────────────────────


class SprintResult(Base):
    """
    ORM model representing a driver's result in a sprint race.

    [EN] Maps to the 'sprint_results' table. Stores the finishing position,
    points, grid position, laps completed, and status for each driver in a
    sprint race. Sprint races are shorter races (introduced in 2021) held
    on Saturdays to determine the grid for the main Grand Prix.

    [PT-BR] Mapeia para a tabela 'sprint_results'. Armazena a posição de
    chegada, pontos, posição no grid, voltas completadas e status para cada
    piloto em uma corrida sprint. Corridas sprint são corridas curtas
    (introduzidas em 2021) realizadas aos sábados para definir o grid do
    Grande Prêmio principal.

    Attributes:
        id (int): Primary key. / Chave primária.
        race_id (int): FK to races. / FK para corridas.
        driver_id (int): FK to drivers. / FK para pilotos.
        constructor_id (int): FK to constructors. / FK para construtores.
        grid (int): Starting grid position. / Posição no grid de largada.
        position (int): Finishing position (null if DNF). /
                        Posição de chegada (null se DNF).
        position_text (str): Position as text. / Posição como texto.
        points (float): Points scored. / Pontos marcados.
        laps (int): Laps completed. / Voltas completadas.
        time_result (str): Finishing time or gap. / Tempo ou diferença.
        fastest_lap_time (str): Fastest lap time. / Volta mais rápida.
        status (str): Finish status. / Status de finalização.

    Author: Bruno Krieger
    """

    __tablename__ = "sprint_results"

    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), index=True)
    constructor_id = Column(Integer, ForeignKey("constructors.id"), index=True)
    grid = Column(Integer)
    position = Column(Integer, nullable=True)
    position_text = Column(String)
    points = Column(Float)
    laps = Column(Integer)
    time_result = Column(String, nullable=True)
    fastest_lap_time = Column(String, nullable=True)
    status = Column(String)

    # Relationships / Relacionamentos
    race = relationship("Race", back_populates="sprint_results")
    driver = relationship("Driver", back_populates="sprint_results")
    constructor = relationship("Constructor")

    def __repr__(self):
        """
        Return a string representation of the SprintResult instance.

        [EN] Returns a human-readable string for debugging.
        [PT-BR] Retorna uma string legível para depuração.

        Author: Bruno Krieger
        """
        return f"<SprintResult(race_id={self.race_id}, driver_id={self.driver_id}, pos={self.position})>"


# ─────────────────────────────────────────────────────────────────────────────
# LapTime
# ─────────────────────────────────────────────────────────────────────────────


class LapTime(Base):
    """
    ORM model representing a single lap time for a driver in a race.

    [EN] Maps to the 'lap_times' table. Stores individual lap timing data,
    including the lap number, position at that lap, and the lap time.
    Lap time data is available from the 1996 season onward.

    [PT-BR] Mapeia para a tabela 'lap_times'. Armazena dados individuais de
    tempo de volta, incluindo o número da volta, posição naquela volta e o
    tempo de volta. Dados de tempo de volta estão disponíveis a partir da
    temporada 1996.

    Attributes:
        id (int): Primary key. / Chave primária.
        race_id (int): FK to races. / FK para corridas.
        driver_id (int): FK to drivers. / FK para pilotos.
        lap (int): Lap number. / Número da volta.
        position (int): Driver position at this lap. /
                        Posição do piloto nesta volta.
        time (str): Lap time (e.g. "1:32.456"). /
                    Tempo de volta (ex: "1:32.456").
        time_ms (int): Lap time in milliseconds. /
                       Tempo de volta em milissegundos.

    Author: Bruno Krieger
    """

    __tablename__ = "lap_times"

    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), index=True)
    lap = Column(Integer)
    position = Column(Integer)
    time = Column(String, nullable=True)
    time_ms = Column(Integer, nullable=True)

    # Relationships / Relacionamentos
    race = relationship("Race", back_populates="lap_times")
    driver = relationship("Driver", back_populates="lap_times")

    def __repr__(self):
        """
        Return a string representation of the LapTime instance.

        [EN] Returns a human-readable string for debugging.
        [PT-BR] Retorna uma string legível para depuração.

        Author: Bruno Krieger
        """
        return f"<LapTime(race_id={self.race_id}, driver_id={self.driver_id}, lap={self.lap}, time='{self.time}')>"


# ─────────────────────────────────────────────────────────────────────────────
# Status (Finishing Status)
# ─────────────────────────────────────────────────────────────────────────────


class Status(Base):
    """
    ORM model representing a race finishing status.

    [EN] Maps to the 'statuses' table. Lookup table for all possible race
    finishing statuses (e.g. "Finished", "Engine", "Collision", "Spun off").
    A count field tracks how many times this status has occurred historically.

    [PT-BR] Mapeia para a tabela 'statuses'. Tabela de consulta para todos
    os possíveis status de finalização de corrida (ex: "Finished", "Engine",
    "Collision", "Spun off"). O campo count registra quantas vezes esse
    status ocorreu historicamente.

    Attributes:
        id (int): Primary key (matches Ergast status ID). /
                  Chave primária (corresponde ao ID de status do Ergast).
        status (str): Status description. / Descrição do status.
        count (int): Historical occurrence count. /
                     Contagem de ocorrências históricas.

    Author: Bruno Krieger
    """

    __tablename__ = "statuses"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, unique=True)
    count = Column(Integer, nullable=True)

    def __repr__(self):
        """
        Return a string representation of the Status instance.

        [EN] Returns a human-readable string for debugging.
        [PT-BR] Retorna uma string legível para depuração.

        Author: Bruno Krieger
        """
        return f"<Status(id={self.id}, status='{self.status}')>"
