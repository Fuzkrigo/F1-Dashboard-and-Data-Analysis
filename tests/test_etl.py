"""
Tests for the ETL Extract layer.

[EN] Verifies the HTTP fetching logic with retries, pagination, and the
high-level extract_* functions. All HTTP calls are mocked — no real
requests to the Jolpica API are made.

[PT-BR] Verifica a lógica de busca HTTP com retries, paginação e as
funções extract_* de alto nível. Todas as chamadas HTTP são mockadas —
nenhuma requisição real à API Jolpica é feita.
"""

from unittest.mock import Mock, patch

import requests
from src.etl.extract import (
    _fetch_paginated,
    _fetch_with_retry,
    extract_circuits,
    extract_constructor_standings,
    extract_constructors,
    extract_driver_standings,
    extract_drivers,
    extract_laps,
    extract_pit_stops,
    extract_qualifying,
    extract_races,
    extract_results,
    extract_seasons,
    extract_sprint,
    extract_statuses,
)


# ─────────────────────────────────────────────────────────────────────────────
# _fetch_with_retry
# ─────────────────────────────────────────────────────────────────────────────


def test_fetch_with_retry_invalid_url():
    """Retrier returns None and tries MAX_RETRIES times on connection error."""
    with patch("requests.get") as mock_get, patch("time.sleep"):
        mock_get.side_effect = requests.exceptions.RequestException(
            "Fake Connection Error"
        )
        data = _fetch_with_retry("http://fake-url.com")
        assert data is None
        assert mock_get.call_count == 3  # MAX_RETRIES


def test_fetch_with_retry_valid_url():
    """First-try success returns data and only calls once."""
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"MRData": {"RaceTable": {}}}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        data = _fetch_with_retry("https://api.fake.com")
        assert data is not None
        assert "MRData" in data
        assert mock_get.call_count == 1


def test_fetch_with_retry_recovers_after_failure():
    """First call fails, second succeeds — retrier returns data."""
    success_response = Mock()
    success_response.status_code = 200
    success_response.json.return_value = {"MRData": {}}
    success_response.raise_for_status.return_value = None

    with patch("requests.get") as mock_get, patch("time.sleep"):
        mock_get.side_effect = [
            requests.exceptions.RequestException("Transient"),
            success_response,
        ]
        data = _fetch_with_retry("https://api.fake.com")
        assert data == {"MRData": {}}
        assert mock_get.call_count == 2


# ─────────────────────────────────────────────────────────────────────────────
# _fetch_paginated
# ─────────────────────────────────────────────────────────────────────────────


def _build_page_response(items, total):
    """Build a mock MRData payload for one page."""
    return {
        "MRData": {
            "total": str(total),
            "RaceTable": {"Races": items},
        }
    }


def test_fetch_paginated_single_page():
    """Single page (total <= PAGE_LIMIT) returns all items in one call."""
    items = [{"id": i} for i in range(5)]
    with patch("src.etl.extract._fetch_with_retry") as mock_fetch:
        mock_fetch.return_value = _build_page_response(items, total=5)
        result = _fetch_paginated("http://x", "RaceTable", "Races")
        assert result == items
        assert mock_fetch.call_count == 1


def test_fetch_paginated_multi_page():
    """When total > PAGE_LIMIT, the fetcher loops until all items collected."""
    page1 = [{"id": i} for i in range(100)]
    page2 = [{"id": i} for i in range(100, 150)]

    with (
        patch("src.etl.extract._fetch_with_retry") as mock_fetch,
        patch("time.sleep"),
    ):
        mock_fetch.side_effect = [
            _build_page_response(page1, total=150),
            _build_page_response(page2, total=150),
        ]
        result = _fetch_paginated("http://x", "RaceTable", "Races")
        assert len(result) == 150
        assert mock_fetch.call_count == 2


def test_fetch_paginated_aborts_on_fetch_failure():
    """If a page fetch returns None, loop breaks early."""
    with patch("src.etl.extract._fetch_with_retry") as mock_fetch:
        mock_fetch.return_value = None
        result = _fetch_paginated("http://x", "RaceTable", "Races")
        assert result == []


# ─────────────────────────────────────────────────────────────────────────────
# Top-level extract_* functions — verify URL composition + return shape
# ─────────────────────────────────────────────────────────────────────────────


def test_extract_seasons_calls_correct_endpoint():
    with patch("src.etl.extract._fetch_paginated") as mock_paginated:
        mock_paginated.return_value = [{"season": "2023"}]
        result = extract_seasons()
        mock_paginated.assert_called_once()
        url_arg = mock_paginated.call_args[0][0]
        assert "seasons.json" in url_arg
        assert result == [{"season": "2023"}]


def test_extract_statuses():
    with patch("src.etl.extract._fetch_paginated") as mock:
        mock.return_value = [{"statusId": "1", "status": "Finished"}]
        result = extract_statuses()
        assert result[0]["status"] == "Finished"
        assert "status.json" in mock.call_args[0][0]


def test_extract_circuits():
    with patch("src.etl.extract._fetch_paginated") as mock:
        mock.return_value = [{"circuitId": "monaco"}]
        extract_circuits()
        assert "circuits.json" in mock.call_args[0][0]


def test_extract_drivers():
    with patch("src.etl.extract._fetch_paginated") as mock:
        mock.return_value = []
        extract_drivers()
        assert "drivers.json" in mock.call_args[0][0]


def test_extract_constructors():
    with patch("src.etl.extract._fetch_paginated") as mock:
        mock.return_value = []
        extract_constructors()
        assert "constructors.json" in mock.call_args[0][0]


def test_extract_races_uses_year_in_url():
    with patch("src.etl.extract._fetch_paginated") as mock:
        mock.return_value = []
        extract_races(2023)
        assert "/2023.json" in mock.call_args[0][0]


def test_extract_results_returns_results_list():
    with patch("src.etl.extract._fetch_paginated") as mock:
        mock.return_value = [{"Results": [{"position": "1"}]}]
        result = extract_results(2023, 1)
        assert result == [{"position": "1"}]


def test_extract_results_empty_when_no_races():
    with patch("src.etl.extract._fetch_paginated") as mock:
        mock.return_value = []
        assert extract_results(2023, 99) == []


def test_extract_qualifying_returns_qualifying_results():
    with patch("src.etl.extract._fetch_paginated") as mock:
        mock.return_value = [{"QualifyingResults": [{"position": "1"}]}]
        result = extract_qualifying(2023, 1)
        assert result == [{"position": "1"}]


def test_extract_qualifying_empty():
    with patch("src.etl.extract._fetch_paginated") as mock:
        mock.return_value = []
        assert extract_qualifying(2023, 99) == []


def test_extract_sprint_returns_sprint_results():
    with patch("src.etl.extract._fetch_paginated") as mock:
        mock.return_value = [{"SprintResults": [{"position": "1"}]}]
        result = extract_sprint(2023, 4)
        assert len(result) == 1


def test_extract_sprint_no_sprint_in_race():
    """Race without sprint returns empty list."""
    with patch("src.etl.extract._fetch_paginated") as mock:
        mock.return_value = []
        assert extract_sprint(2023, 1) == []


def test_extract_driver_standings_unwraps_nested():
    with patch("src.etl.extract._fetch_paginated") as mock:
        mock.return_value = [
            {"DriverStandings": [{"position": "1", "points": "454"}]}
        ]
        result = extract_driver_standings(2023)
        assert result[0]["points"] == "454"


def test_extract_driver_standings_empty():
    with patch("src.etl.extract._fetch_paginated") as mock:
        mock.return_value = []
        assert extract_driver_standings(2023) == []


def test_extract_constructor_standings_unwraps_nested():
    with patch("src.etl.extract._fetch_paginated") as mock:
        mock.return_value = [{"ConstructorStandings": [{"position": "1"}]}]
        result = extract_constructor_standings(2023)
        assert result[0]["position"] == "1"


def test_extract_constructor_standings_empty():
    with patch("src.etl.extract._fetch_paginated") as mock:
        mock.return_value = []
        assert extract_constructor_standings(2023) == []


def test_extract_pit_stops():
    with patch("src.etl.extract._fetch_paginated") as mock:
        mock.return_value = [{"PitStops": [{"driverId": "ver", "stop": "1"}]}]
        result = extract_pit_stops(2023, 1)
        assert result[0]["driverId"] == "ver"


def test_extract_pit_stops_empty():
    with patch("src.etl.extract._fetch_paginated") as mock:
        mock.return_value = []
        assert extract_pit_stops(2023, 1) == []


def test_extract_laps():
    with patch("src.etl.extract._fetch_paginated") as mock:
        mock.return_value = [{"Laps": [{"number": "1", "Timings": []}]}]
        result = extract_laps(2023, 1)
        assert result[0]["number"] == "1"


def test_extract_laps_empty():
    with patch("src.etl.extract._fetch_paginated") as mock:
        mock.return_value = []
        assert extract_laps(2023, 1) == []
