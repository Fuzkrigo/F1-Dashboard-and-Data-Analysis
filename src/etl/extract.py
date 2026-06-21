"""
ETL — Extract Module.

[EN] Handles data extraction from the Jolpica F1 API (Ergast successor).
Provides paginated fetching functions for all 12 data entities: seasons,
circuits, drivers, constructors, races, race results, qualifying results,
sprint results, driver standings, constructor standings, pit stops, lap
times, and finishing statuses.

[PT-BR] Realiza a extração de dados da API Jolpica F1 (sucessora do Ergast).
Fornece funções de busca paginada para todas as 12 entidades de dados:
temporadas, circuitos, pilotos, construtores, corridas, resultados de
corridas, resultados de classificação, resultados de sprint, classificações
de pilotos, classificações de construtores, pit stops, tempos de volta e
status de finalização.

Author: Bruno Krieger
"""

import time

import requests

# ─────────────────────────────────────────────────────────────────────────────
# Configuration / Configuração
# ─────────────────────────────────────────────────────────────────────────────

BASE_URL = "https://api.jolpi.ca/ergast/f1"
PAGE_LIMIT = 100  # Max allowed by the API / Máximo permitido pela API
REQUEST_DELAY = 0.2  # Seconds between requests / Segundos entre requisições
MAX_RETRIES = 3  # Max retry attempts / Tentativas máximas de retry
RETRY_BACKOFF = 2  # Backoff multiplier / Multiplicador de backoff


# ─────────────────────────────────────────────────────────────────────────────
# Generic Paginated Fetcher / Buscador Genérico Paginado
# ─────────────────────────────────────────────────────────────────────────────


def _fetch_paginated(url: str, table_key: str, list_key: str) -> list[dict]:
    """
    Fetch all pages of data from a Jolpica API endpoint.

    [EN] Sends paginated GET requests to the API, collecting all items
    across pages. Uses exponential backoff retry on failures. The
    `table_key` and `list_key` parameters navigate the nested JSON
    response (e.g., table_key="RaceTable", list_key="Races").

    [PT-BR] Envia requisições GET paginadas para a API, coletando todos
    os itens através das páginas. Usa retry com backoff exponencial em
    falhas. Os parâmetros `table_key` e `list_key` navegam a resposta
    JSON aninhada (ex: table_key="RaceTable", list_key="Races").

    Args:
        url (str): The API endpoint URL (without pagination params).
                   A URL do endpoint da API (sem parâmetros de paginação).
        table_key (str): Top-level key in MRData (e.g. "RaceTable").
                         Chave de nível superior em MRData.
        list_key (str): Key for the data list within the table.
                        Chave para a lista de dados dentro da tabela.

    Returns:
        list[dict]: All collected items from all pages.
                    Todos os itens coletados de todas as páginas.

    Author: Bruno Krieger
    """
    all_items = []
    offset = 0

    while True:
        paginated_url = f"{url}?limit={PAGE_LIMIT}&offset={offset}"

        data = _fetch_with_retry(paginated_url)
        if data is None:
            print(f"  [WARN] Failed to fetch {paginated_url}, skipping...")
            break

        mr_data = data.get("MRData", {})
        total = int(mr_data.get("total", 0))
        table = mr_data.get(table_key, {})
        items = table.get(list_key, [])

        all_items.extend(items)

        # Check if we've collected all items
        # Verifica se coletamos todos os itens
        if offset + PAGE_LIMIT >= total:
            break

        offset += PAGE_LIMIT
        time.sleep(REQUEST_DELAY)

    return all_items


def _fetch_with_retry(url: str) -> dict | None:
    """
    Fetch a URL with retry logic and exponential backoff.

    [EN] Attempts to fetch the URL up to MAX_RETRIES times. On failure,
    waits with exponential backoff before retrying. Returns None if all
    attempts fail.

    [PT-BR] Tenta buscar a URL até MAX_RETRIES vezes. Em caso de falha,
    espera com backoff exponencial antes de tentar novamente. Retorna
    None se todas as tentativas falharem.

    Args:
        url (str): The URL to fetch. / A URL para buscar.

    Returns:
        dict | None: Parsed JSON response, or None on failure.
                     Resposta JSON parseada, ou None em caso de falha.

    Author: Bruno Krieger
    """
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            wait_time = RETRY_BACKOFF**attempt
            print(
                f"  [RETRY {attempt + 1}/{MAX_RETRIES}] "
                f"Error: {e}. Waiting {wait_time}s..."
            )
            time.sleep(wait_time)

    return None


# ─────────────────────────────────────────────────────────────────────────────
# Extraction Functions / Funções de Extração
# ─────────────────────────────────────────────────────────────────────────────


def extract_seasons() -> list[dict]:
    """
    Extract all F1 seasons from the API.

    [EN] Fetches the complete list of F1 seasons (1950–present).
    [PT-BR] Busca a lista completa de temporadas de F1 (1950–presente).

    Returns:
        list[dict]: Raw season data from the API.

    Author: Bruno Krieger
    """
    print("  Extracting seasons...")
    return _fetch_paginated(f"{BASE_URL}/seasons.json", "SeasonTable", "Seasons")


def extract_statuses() -> list[dict]:
    """
    Extract all finishing statuses from the API.

    [EN] Fetches the complete list of race finishing statuses.
    [PT-BR] Busca a lista completa de status de finalização de corrida.

    Returns:
        list[dict]: Raw status data from the API.

    Author: Bruno Krieger
    """
    print("  Extracting statuses...")
    return _fetch_paginated(f"{BASE_URL}/status.json", "StatusTable", "Status")


def extract_circuits() -> list[dict]:
    """
    Extract all circuits from the API.

    [EN] Fetches the complete list of F1 circuits.
    [PT-BR] Busca a lista completa de circuitos de F1.

    Returns:
        list[dict]: Raw circuit data from the API.

    Author: Bruno Krieger
    """
    print("  Extracting circuits...")
    return _fetch_paginated(f"{BASE_URL}/circuits.json", "CircuitTable", "Circuits")


def extract_drivers() -> list[dict]:
    """
    Extract all drivers from the API.

    [EN] Fetches the complete list of F1 drivers (all-time).
    [PT-BR] Busca a lista completa de pilotos de F1 (todos os tempos).

    Returns:
        list[dict]: Raw driver data from the API.

    Author: Bruno Krieger
    """
    print("  Extracting drivers...")
    return _fetch_paginated(f"{BASE_URL}/drivers.json", "DriverTable", "Drivers")


def extract_constructors() -> list[dict]:
    """
    Extract all constructors from the API.

    [EN] Fetches the complete list of F1 constructors (teams).
    [PT-BR] Busca a lista completa de construtores (equipes) de F1.

    Returns:
        list[dict]: Raw constructor data from the API.

    Author: Bruno Krieger
    """
    print("  Extracting constructors...")
    return _fetch_paginated(
        f"{BASE_URL}/constructors.json", "ConstructorTable", "Constructors"
    )


def extract_races(year: int) -> list[dict]:
    """
    Extract all races for a given season.

    [EN] Fetches the race schedule for the specified year.
    [PT-BR] Busca o calendário de corridas para o ano especificado.

    Args:
        year (int): Season year. / Ano da temporada.

    Returns:
        list[dict]: Raw race data from the API.

    Author: Bruno Krieger
    """
    print(f"  Extracting races for {year}...")
    return _fetch_paginated(f"{BASE_URL}/{year}.json", "RaceTable", "Races")


def extract_results(year: int, round_num: int) -> list[dict]:
    """
    Extract race results for a specific race.

    [EN] Fetches the results for a specific race (year + round).
    [PT-BR] Busca os resultados para uma corrida específica (ano + rodada).

    Args:
        year (int): Season year. / Ano da temporada.
        round_num (int): Race round number. / Número da rodada.

    Returns:
        list[dict]: Raw result data from the API.

    Author: Bruno Krieger
    """
    races = _fetch_paginated(
        f"{BASE_URL}/{year}/{round_num}/results.json", "RaceTable", "Races"
    )
    if races:
        return races[0].get("Results", [])
    return []


def extract_qualifying(year: int, round_num: int) -> list[dict]:
    """
    Extract qualifying results for a specific race.

    [EN] Fetches qualifying session data for a specific race.
    [PT-BR] Busca dados da sessão de classificação para uma corrida.

    Args:
        year (int): Season year. / Ano da temporada.
        round_num (int): Race round number. / Número da rodada.

    Returns:
        list[dict]: Raw qualifying data from the API.

    Author: Bruno Krieger
    """
    races = _fetch_paginated(
        f"{BASE_URL}/{year}/{round_num}/qualifying.json", "RaceTable", "Races"
    )
    if races:
        return races[0].get("QualifyingResults", [])
    return []


def extract_sprint(year: int, round_num: int) -> list[dict]:
    """
    Extract sprint race results for a specific race.

    [EN] Fetches sprint results for a specific race (2021+ only).
    [PT-BR] Busca resultados de sprint para uma corrida (apenas 2021+).

    Args:
        year (int): Season year. / Ano da temporada.
        round_num (int): Race round number. / Número da rodada.

    Returns:
        list[dict]: Raw sprint data, or empty list if no sprint.

    Author: Bruno Krieger
    """
    races = _fetch_paginated(
        f"{BASE_URL}/{year}/{round_num}/sprint.json", "RaceTable", "Races"
    )
    if races:
        return races[0].get("SprintResults", [])
    return []


def extract_driver_standings(year: int) -> list[dict]:
    """
    Extract final driver standings for a season.

    [EN] Fetches the driver championship standings after the last race.
    [PT-BR] Busca a classificação do campeonato de pilotos após a última corrida.

    Args:
        year (int): Season year. / Ano da temporada.

    Returns:
        list[dict]: Raw driver standings data from the API.

    Author: Bruno Krieger
    """
    print(f"  Extracting driver standings for {year}...")
    standings_lists = _fetch_paginated(
        f"{BASE_URL}/{year}/driverstandings.json",
        "StandingsTable",
        "StandingsLists",
    )
    if standings_lists:
        return standings_lists[0].get("DriverStandings", [])
    return []


def extract_constructor_standings(year: int) -> list[dict]:
    """
    Extract final constructor standings for a season.

    [EN] Fetches the constructor championship standings after the last race.
    [PT-BR] Busca a classificação do campeonato de construtores após a última corrida.

    Args:
        year (int): Season year. / Ano da temporada.

    Returns:
        list[dict]: Raw constructor standings data from the API.

    Author: Bruno Krieger
    """
    print(f"  Extracting constructor standings for {year}...")
    standings_lists = _fetch_paginated(
        f"{BASE_URL}/{year}/constructorstandings.json",
        "StandingsTable",
        "StandingsLists",
    )
    if standings_lists:
        return standings_lists[0].get("ConstructorStandings", [])
    return []


def extract_pit_stops(year: int, round_num: int) -> list[dict]:
    """
    Extract pit stop data for a specific race.

    [EN] Fetches all pit stops for a specific race.
    [PT-BR] Busca todos os pit stops para uma corrida específica.

    Args:
        year (int): Season year. / Ano da temporada.
        round_num (int): Race round number. / Número da rodada.

    Returns:
        list[dict]: Raw pit stop data from the API.

    Author: Bruno Krieger
    """
    races = _fetch_paginated(
        f"{BASE_URL}/{year}/{round_num}/pitstops.json", "RaceTable", "Races"
    )
    if races:
        return races[0].get("PitStops", [])
    return []


def extract_laps(year: int, round_num: int) -> list[dict]:
    """
    Extract lap time data for a specific race.

    [EN] Fetches all lap times for a specific race. This is the most
    data-intensive endpoint — a single race can have ~1000+ lap records.
    Data is available from 1996 onward.

    [PT-BR] Busca todos os tempos de volta para uma corrida específica.
    Este é o endpoint mais intensivo em dados — uma única corrida pode
    ter ~1000+ registros de volta. Dados disponíveis a partir de 1996.

    Args:
        year (int): Season year. / Ano da temporada.
        round_num (int): Race round number. / Número da rodada.

    Returns:
        list[dict]: Raw lap data (each containing Timings list).

    Author: Bruno Krieger
    """
    races = _fetch_paginated(
        f"{BASE_URL}/{year}/{round_num}/laps.json", "RaceTable", "Races"
    )
    if races:
        return races[0].get("Laps", [])
    return []


(
    """
    CodeContent = above
    Description = Reescrita completa do extract.py com 12 funções de extração, paginação automática, retry com backoff exponencial, e rate limiting. Base URL atualizada para Jolpica API.
    EmptyFile = false
    IsArtifact = false
""",
)
