"""
ETL — Transform Module.

[EN] Handles the transformation step of the ETL pipeline. Converts raw
JSON responses from the Jolpica F1 API into clean, flat dictionaries
that map directly to the SQLAlchemy ORM models. Provides transformation
functions for all 12 data entities: seasons, circuits, drivers,
constructors, races, race results, qualifying results, sprint results,
driver standings, constructor standings, pit stops, lap times,
and finishing statuses.

[PT-BR] Realiza a etapa de transformação do pipeline ETL. Converte
respostas JSON brutas da API Jolpica F1 em dicionários planos e limpos
que mapeiam diretamente para os modelos ORM do SQLAlchemy. Fornece
funções de transformação para todas as 12 entidades de dados: temporadas,
circuitos, pilotos, construtores, corridas, resultados de corridas,
resultados de classificação, resultados de sprint, classificações de
pilotos, classificações de construtores, pit stops, tempos de volta
e status de finalização.

Author: Bruno Krieger
"""

from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# Helpers / Funções auxiliares
# ─────────────────────────────────────────────────────────────────────────────


def _safe_int(value: str | None) -> int | None:
    """
    Safely convert a string to int, returning None on failure.

    [EN] Handles None, empty strings, and non-numeric strings.
    [PT-BR] Trata None, strings vazias e strings não numéricas.

    Author: Bruno Krieger
    """
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _safe_float(value: str | None) -> float | None:
    """
    Safely convert a string to float, returning None on failure.

    [EN] Handles None, empty strings, and non-numeric strings.
    [PT-BR] Trata None, strings vazias e strings não numéricas.

    Author: Bruno Krieger
    """
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _safe_date(value: str | None):
    """
    Safely parse a date string (YYYY-MM-DD) to a date object.

    [EN] Returns None if the string is missing or malformed.
    [PT-BR] Retorna None se a string estiver ausente ou malformada.

    Author: Bruno Krieger
    """
    if value is None or value == "":
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Transformation Functions / Funções de Transformação
# ─────────────────────────────────────────────────────────────────────────────


def transform_seasons(raw_seasons: list[dict]) -> list[dict]:
    """
    Transform raw season data into model-ready dictionaries.

    [EN] Maps API fields to Season model columns.
    [PT-BR] Mapeia campos da API para colunas do modelo Season.

    Args:
        raw_seasons: Raw season data from the API extract.

    Returns:
        list[dict]: Dicts with keys: year, url.

    Author: Bruno Krieger
    """
    return [
        {
            "year": int(s["season"]),
            "url": s.get("url", ""),
        }
        for s in raw_seasons
    ]


def transform_statuses(raw_statuses: list[dict]) -> list[dict]:
    """
    Transform raw status data into model-ready dictionaries.

    [EN] Maps API fields to Status model columns. Uses the API's statusId
    as the primary key.
    [PT-BR] Mapeia campos da API para colunas do modelo Status. Usa o
    statusId da API como chave primária.

    Args:
        raw_statuses: Raw status data from the API extract.

    Returns:
        list[dict]: Dicts with keys: id, status, count.

    Author: Bruno Krieger
    """
    return [
        {
            "id": int(s["statusId"]),
            "status": s["status"],
            "count": _safe_int(s.get("count")),
        }
        for s in raw_statuses
    ]


def transform_circuits(raw_circuits: list[dict]) -> list[dict]:
    """
    Transform raw circuit data into model-ready dictionaries.

    [EN] Maps API fields to Circuit model columns. Extracts nested
    Location information into flat fields.
    [PT-BR] Mapeia campos da API para colunas do modelo Circuit. Extrai
    informações aninhadas de Location em campos planos.

    Args:
        raw_circuits: Raw circuit data from the API extract.

    Returns:
        list[dict]: Dicts with keys: circuit_ref, circuit_name, location,
                    country, latitude, longitude, url.

    Author: Bruno Krieger
    """
    results = []
    for c in raw_circuits:
        location = c.get("Location", {})
        results.append(
            {
                "circuit_ref": c["circuitId"],
                "circuit_name": c["circuitName"],
                "location": location.get("locality", ""),
                "country": location.get("country", ""),
                "latitude": _safe_float(location.get("lat")),
                "longitude": _safe_float(location.get("long")),
                "url": c.get("url", ""),
            }
        )
    return results


def transform_drivers(raw_drivers: list[dict]) -> list[dict]:
    """
    Transform raw driver data into model-ready dictionaries.

    [EN] Maps API fields to Driver model columns. Handles optional
    fields like permanentNumber and code that may not exist for
    older drivers.
    [PT-BR] Mapeia campos da API para colunas do modelo Driver. Trata
    campos opcionais como permanentNumber e code que podem não existir
    para pilotos mais antigos.

    Args:
        raw_drivers: Raw driver data from the API extract.

    Returns:
        list[dict]: Dicts with keys: driver_ref, permanent_number, code,
                    first_name, last_name, date_of_birth, nationality, url.

    Author: Bruno Krieger
    """
    return [
        {
            "driver_ref": d["driverId"],
            "permanent_number": _safe_int(d.get("permanentNumber")),
            "code": d.get("code"),
            "first_name": d.get("givenName", ""),
            "last_name": d.get("familyName", ""),
            "date_of_birth": _safe_date(d.get("dateOfBirth")),
            "nationality": d.get("nationality", ""),
            "url": d.get("url", ""),
        }
        for d in raw_drivers
    ]


def transform_constructors(raw_constructors: list[dict]) -> list[dict]:
    """
    Transform raw constructor data into model-ready dictionaries.

    [EN] Maps API fields to Constructor model columns.
    [PT-BR] Mapeia campos da API para colunas do modelo Constructor.

    Args:
        raw_constructors: Raw constructor data from the API extract.

    Returns:
        list[dict]: Dicts with keys: constructor_ref, constructor_name,
                    nationality, url.

    Author: Bruno Krieger
    """
    return [
        {
            "constructor_ref": c["constructorId"],
            "constructor_name": c["name"],
            "nationality": c.get("nationality", ""),
            "url": c.get("url", ""),
        }
        for c in raw_constructors
    ]


def transform_races(raw_races: list[dict]) -> list[dict]:
    """
    Transform raw race data into model-ready dictionaries.

    [EN] Maps API fields to Race model columns. Extracts the circuit
    reference ID for FK lookup during load, plus the denormalized
    circuit_name.
    [PT-BR] Mapeia campos da API para colunas do modelo Race. Extrai o
    ID de referência do circuito para lookup de FK durante a carga, além
    do circuit_name desnormalizado.

    Args:
        raw_races: Raw race data from the API extract.

    Returns:
        list[dict]: Dicts with keys: season, round, url, race_name,
                    circuit_ref, circuit_name, date.

    Author: Bruno Krieger
    """
    results = []
    for race in raw_races:
        circuit = race.get("Circuit", {})
        results.append(
            {
                "season": int(race["season"]),
                "round": int(race["round"]),
                "url": race.get("url", ""),
                "race_name": race.get("raceName", ""),
                "circuit_ref": circuit.get("circuitId", ""),
                "circuit_name": circuit.get("circuitName", ""),
                "date": _safe_date(race.get("date")),
            }
        )
    return results


def transform_results(raw_results: list[dict]) -> list[dict]:
    """
    Transform raw race result data into model-ready dictionaries.

    [EN] Maps API fields to RaceResult model columns. Extracts nested
    Driver, Constructor, Time, and FastestLap data into flat fields.
    Uses ref IDs for FK lookup during load.
    [PT-BR] Mapeia campos da API para colunas do modelo RaceResult.
    Extrai dados aninhados de Driver, Constructor, Time e FastestLap
    em campos planos. Usa IDs de referência para lookup de FK na carga.

    Args:
        raw_results: Raw result data from the API extract.

    Returns:
        list[dict]: Dicts with keys matching RaceResult columns + ref fields.

    Author: Bruno Krieger
    """
    results = []
    for r in raw_results:
        driver = r.get("Driver", {})
        constructor = r.get("Constructor", {})
        time_data = r.get("Time", {})
        fastest_lap = r.get("FastestLap", {})
        fastest_lap_time = fastest_lap.get("Time", {})
        fastest_lap_speed = fastest_lap.get("AverageSpeed", {})

        results.append(
            {
                "driver_ref": driver.get("driverId", ""),
                "constructor_ref": constructor.get("constructorId", ""),
                "grid": _safe_int(r.get("grid")),
                "position": _safe_int(r.get("position")),
                "position_text": r.get("positionText", ""),
                "points": _safe_float(r.get("points")),
                "laps": _safe_int(r.get("laps")),
                "time_result": time_data.get("time"),
                "fastest_lap_time": fastest_lap_time.get("time"),
                "fastest_lap_speed": _safe_float(fastest_lap_speed.get("speed")),
                "status": r.get("status", ""),
            }
        )
    return results


def transform_qualifying(raw_qualifying: list[dict]) -> list[dict]:
    """
    Transform raw qualifying data into model-ready dictionaries.

    [EN] Maps API fields to QualifyingResult model columns. Q2 and Q3
    may be null if the driver was eliminated in an earlier session.
    [PT-BR] Mapeia campos da API para colunas do modelo QualifyingResult.
    Q2 e Q3 podem ser null se o piloto foi eliminado em sessão anterior.

    Args:
        raw_qualifying: Raw qualifying data from the API extract.

    Returns:
        list[dict]: Dicts with keys matching QualifyingResult columns.

    Author: Bruno Krieger
    """
    results = []
    for q in raw_qualifying:
        driver = q.get("Driver", {})
        constructor = q.get("Constructor", {})

        results.append(
            {
                "driver_ref": driver.get("driverId", ""),
                "constructor_ref": constructor.get("constructorId", ""),
                "position": _safe_int(q.get("position")),
                "q1": q.get("Q1"),
                "q2": q.get("Q2"),
                "q3": q.get("Q3"),
            }
        )
    return results


def transform_sprint(raw_sprint: list[dict]) -> list[dict]:
    """
    Transform raw sprint result data into model-ready dictionaries.

    [EN] Maps API fields to SprintResult model columns. Similar to
    race results but for shorter sprint races (2021+).
    [PT-BR] Mapeia campos da API para colunas do modelo SprintResult.
    Similar aos resultados de corrida, mas para sprints (2021+).

    Args:
        raw_sprint: Raw sprint data from the API extract.

    Returns:
        list[dict]: Dicts with keys matching SprintResult columns.

    Author: Bruno Krieger
    """
    results = []
    for r in raw_sprint:
        driver = r.get("Driver", {})
        constructor = r.get("Constructor", {})
        time_data = r.get("Time", {})
        fastest_lap = r.get("FastestLap", {})
        fastest_lap_time = fastest_lap.get("Time", {})

        results.append(
            {
                "driver_ref": driver.get("driverId", ""),
                "constructor_ref": constructor.get("constructorId", ""),
                "grid": _safe_int(r.get("grid")),
                "position": _safe_int(r.get("position")),
                "position_text": r.get("positionText", ""),
                "points": _safe_float(r.get("points")),
                "laps": _safe_int(r.get("laps")),
                "time_result": time_data.get("time"),
                "fastest_lap_time": fastest_lap_time.get("time"),
                "status": r.get("status", ""),
            }
        )
    return results


def transform_driver_standings(raw_standings: list[dict]) -> list[dict]:
    """
    Transform raw driver standings data into model-ready dictionaries.

    [EN] Maps API fields to DriverStanding model columns. Extracts the
    driver ref from nested Driver object for FK lookup.
    [PT-BR] Mapeia campos da API para colunas do modelo DriverStanding.
    Extrai a referência do piloto do objeto Driver aninhado para lookup FK.

    Args:
        raw_standings: Raw driver standings from the API extract.

    Returns:
        list[dict]: Dicts with keys matching DriverStanding columns.

    Author: Bruno Krieger
    """
    results = []
    for s in raw_standings:
        driver = s.get("Driver", {})

        results.append(
            {
                "driver_ref": driver.get("driverId", ""),
                "points": _safe_float(s.get("points")),
                "position": _safe_int(s.get("position")),
                "wins": _safe_int(s.get("wins")),
            }
        )
    return results


def transform_constructor_standings(raw_standings: list[dict]) -> list[dict]:
    """
    Transform raw constructor standings into model-ready dictionaries.

    [EN] Maps API fields to ConstructorStanding model columns.
    [PT-BR] Mapeia campos da API para colunas do modelo ConstructorStanding.

    Args:
        raw_standings: Raw constructor standings from the API extract.

    Returns:
        list[dict]: Dicts with keys matching ConstructorStanding columns.

    Author: Bruno Krieger
    """
    results = []
    for s in raw_standings:
        constructor = s.get("Constructor", {})

        results.append(
            {
                "constructor_ref": constructor.get("constructorId", ""),
                "points": _safe_float(s.get("points")),
                "position": _safe_int(s.get("position")),
                "wins": _safe_int(s.get("wins")),
            }
        )
    return results


def transform_pit_stops(raw_pit_stops: list[dict]) -> list[dict]:
    """
    Transform raw pit stop data into model-ready dictionaries.

    [EN] Maps API fields to PitStop model columns. The API provides
    the driverId for FK lookup. Duration is kept as a string
    (e.g. "23.450") and also parsed to milliseconds when possible.
    [PT-BR] Mapeia campos da API para colunas do modelo PitStop.
    A API fornece o driverId para lookup FK. A duração é mantida
    como string e também convertida para milissegundos quando possível.

    Args:
        raw_pit_stops: Raw pit stop data from the API extract.

    Returns:
        list[dict]: Dicts with keys matching PitStop columns.

    Author: Bruno Krieger
    """
    results = []
    for ps in raw_pit_stops:
        duration_str = ps.get("duration", "")
        # Try to convert duration string (e.g. "23.450") to ms
        # Tenta converter string de duração para milissegundos
        duration_ms = None
        if duration_str:
            try:
                duration_ms = int(float(duration_str) * 1000)
            except ValueError:
                pass

        results.append(
            {
                "driver_ref": ps.get("driverId", ""),
                "stop": _safe_int(ps.get("stop")),
                "lap": _safe_int(ps.get("lap")),
                "time_of_day": ps.get("time"),
                "duration": duration_str if duration_str else None,
                "duration_ms": duration_ms,
            }
        )
    return results


def transform_laps(raw_laps: list[dict]) -> list[dict]:
    """
    Transform raw lap data into model-ready dictionaries.

    [EN] Flattens the nested Laps→Timings structure into individual
    lap time records. Each raw lap contains a list of Timings (one per
    driver), which are exploded into separate records.
    [PT-BR] Achata a estrutura aninhada Laps→Timings em registros
    individuais de tempo de volta. Cada volta bruta contém uma lista
    de Timings (um por piloto), que são expandidos em registros separados.

    Args:
        raw_laps: Raw lap data from the API extract.

    Returns:
        list[dict]: Dicts with keys: driver_ref, lap, position, time.

    Author: Bruno Krieger
    """
    results = []
    for lap in raw_laps:
        lap_number = _safe_int(lap.get("number"))
        timings = lap.get("Timings", [])

        for timing in timings:
            results.append(
                {
                    "driver_ref": timing.get("driverId", ""),
                    "lap": lap_number,
                    "position": _safe_int(timing.get("position")),
                    "time": timing.get("time"),
                    "time_ms": None,  # API doesn't provide ms for laps
                }
            )
    return results
