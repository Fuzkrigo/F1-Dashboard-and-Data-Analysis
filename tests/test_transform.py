"""
Tests for the ETL Transform layer.

[EN] Verifies that all transformation functions correctly map raw API JSON
into flat model-ready dictionaries. Tests cover happy paths, missing
fields, malformed data, and edge cases (None, empty strings, non-numeric).

[PT-BR] Verifica que todas as funções de transformação mapeiam corretamente
o JSON bruto da API em dicionários planos prontos para os modelos. Cobre
caminhos felizes, campos ausentes, dados malformados e casos extremos
(None, strings vazias, não numéricos).
"""

from datetime import date

from src.etl.transform import (
    _safe_date,
    _safe_float,
    _safe_int,
    transform_circuits,
    transform_constructor_standings,
    transform_constructors,
    transform_driver_standings,
    transform_drivers,
    transform_laps,
    transform_pit_stops,
    transform_qualifying,
    transform_races,
    transform_results,
    transform_seasons,
    transform_sprint,
    transform_statuses,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers — _safe_int, _safe_float, _safe_date
# ─────────────────────────────────────────────────────────────────────────────


class TestSafeInt:
    def test_valid_string_number(self):
        assert _safe_int("42") == 42

    def test_negative_number(self):
        assert _safe_int("-7") == -7

    def test_none_returns_none(self):
        assert _safe_int(None) is None

    def test_empty_string_returns_none(self):
        assert _safe_int("") is None

    def test_non_numeric_string_returns_none(self):
        assert _safe_int("abc") is None

    def test_float_string_returns_none(self):
        # int("12.5") raises ValueError → must catch
        assert _safe_int("12.5") is None


class TestSafeFloat:
    def test_valid_float_string(self):
        assert _safe_float("3.14") == 3.14

    def test_integer_string_works(self):
        assert _safe_float("10") == 10.0

    def test_none_returns_none(self):
        assert _safe_float(None) is None

    def test_empty_string_returns_none(self):
        assert _safe_float("") is None

    def test_non_numeric_returns_none(self):
        assert _safe_float("not a number") is None


class TestSafeDate:
    def test_valid_iso_date(self):
        assert _safe_date("2023-03-05") == date(2023, 3, 5)

    def test_none_returns_none(self):
        assert _safe_date(None) is None

    def test_empty_string_returns_none(self):
        assert _safe_date("") is None

    def test_malformed_date_returns_none(self):
        assert _safe_date("05/03/2023") is None

    def test_invalid_date_returns_none(self):
        assert _safe_date("2023-13-99") is None


# ─────────────────────────────────────────────────────────────────────────────
# transform_seasons
# ─────────────────────────────────────────────────────────────────────────────


def test_transform_seasons_basic():
    raw = [{"season": "2023", "url": "https://example.com/2023"}]
    result = transform_seasons(raw)
    assert result == [{"year": 2023, "url": "https://example.com/2023"}]


def test_transform_seasons_missing_url():
    raw = [{"season": "2024"}]
    result = transform_seasons(raw)
    assert result[0]["year"] == 2024
    assert result[0]["url"] == ""


def test_transform_seasons_empty():
    assert transform_seasons([]) == []


# ─────────────────────────────────────────────────────────────────────────────
# transform_statuses
# ─────────────────────────────────────────────────────────────────────────────


def test_transform_statuses_with_count():
    raw = [{"statusId": "1", "status": "Finished", "count": "1234"}]
    result = transform_statuses(raw)
    assert result == [{"id": 1, "status": "Finished", "count": 1234}]


def test_transform_statuses_missing_count():
    raw = [{"statusId": "2", "status": "Disqualified"}]
    result = transform_statuses(raw)
    assert result[0]["count"] is None


# ─────────────────────────────────────────────────────────────────────────────
# transform_circuits
# ─────────────────────────────────────────────────────────────────────────────


def test_transform_circuits_full():
    raw = [
        {
            "circuitId": "monaco",
            "circuitName": "Circuit de Monaco",
            "Location": {
                "locality": "Monte Carlo",
                "country": "Monaco",
                "lat": "43.7347",
                "long": "7.4206",
            },
            "url": "https://example.com/monaco",
        }
    ]
    result = transform_circuits(raw)
    assert result[0]["circuit_ref"] == "monaco"
    assert result[0]["circuit_name"] == "Circuit de Monaco"
    assert result[0]["location"] == "Monte Carlo"
    assert result[0]["country"] == "Monaco"
    assert result[0]["latitude"] == 43.7347
    assert result[0]["longitude"] == 7.4206


def test_transform_circuits_missing_location():
    raw = [{"circuitId": "x", "circuitName": "X"}]
    result = transform_circuits(raw)
    assert result[0]["location"] == ""
    assert result[0]["country"] == ""
    assert result[0]["latitude"] is None
    assert result[0]["longitude"] is None


# ─────────────────────────────────────────────────────────────────────────────
# transform_drivers
# ─────────────────────────────────────────────────────────────────────────────


def test_transform_drivers_full():
    raw = [
        {
            "driverId": "max_verstappen",
            "permanentNumber": "1",
            "code": "VER",
            "givenName": "Max",
            "familyName": "Verstappen",
            "dateOfBirth": "1997-09-30",
            "nationality": "Dutch",
            "url": "https://example.com/ver",
        }
    ]
    result = transform_drivers(raw)
    assert result[0]["driver_ref"] == "max_verstappen"
    assert result[0]["permanent_number"] == 1
    assert result[0]["code"] == "VER"
    assert result[0]["first_name"] == "Max"
    assert result[0]["last_name"] == "Verstappen"
    assert result[0]["date_of_birth"] == date(1997, 9, 30)
    assert result[0]["nationality"] == "Dutch"


def test_transform_drivers_legacy_no_code():
    # Old drivers lack permanentNumber and code
    raw = [
        {
            "driverId": "fangio",
            "givenName": "Juan Manuel",
            "familyName": "Fangio",
            "dateOfBirth": "1911-06-24",
            "nationality": "Argentine",
        }
    ]
    result = transform_drivers(raw)
    assert result[0]["permanent_number"] is None
    assert result[0]["code"] is None
    assert result[0]["last_name"] == "Fangio"


# ─────────────────────────────────────────────────────────────────────────────
# transform_constructors
# ─────────────────────────────────────────────────────────────────────────────


def test_transform_constructors():
    raw = [
        {
            "constructorId": "ferrari",
            "name": "Ferrari",
            "nationality": "Italian",
            "url": "https://example.com/ferrari",
        }
    ]
    result = transform_constructors(raw)
    assert result[0]["constructor_ref"] == "ferrari"
    assert result[0]["constructor_name"] == "Ferrari"
    assert result[0]["nationality"] == "Italian"


def test_transform_constructors_missing_optional():
    raw = [{"constructorId": "x", "name": "X"}]
    result = transform_constructors(raw)
    assert result[0]["nationality"] == ""
    assert result[0]["url"] == ""


# ─────────────────────────────────────────────────────────────────────────────
# transform_races
# ─────────────────────────────────────────────────────────────────────────────


def test_transform_races_full():
    raw = [
        {
            "season": "2023",
            "round": "1",
            "url": "https://example.com/race",
            "raceName": "Bahrain Grand Prix",
            "Circuit": {"circuitId": "bahrain", "circuitName": "Bahrain Intl Circuit"},
            "date": "2023-03-05",
        }
    ]
    result = transform_races(raw)
    assert result[0]["season"] == 2023
    assert result[0]["round"] == 1
    assert result[0]["race_name"] == "Bahrain Grand Prix"
    assert result[0]["circuit_ref"] == "bahrain"
    assert result[0]["date"] == date(2023, 3, 5)


def test_transform_races_missing_circuit():
    raw = [{"season": "2024", "round": "5", "raceName": "Test"}]
    result = transform_races(raw)
    assert result[0]["circuit_ref"] == ""
    assert result[0]["circuit_name"] == ""


# ─────────────────────────────────────────────────────────────────────────────
# transform_results
# ─────────────────────────────────────────────────────────────────────────────


def test_transform_results_full():
    raw = [
        {
            "Driver": {"driverId": "max_verstappen"},
            "Constructor": {"constructorId": "red_bull"},
            "grid": "1",
            "position": "1",
            "positionText": "1",
            "points": "25",
            "laps": "57",
            "Time": {"time": "1:33:56.736"},
            "FastestLap": {
                "Time": {"time": "1:33.996"},
                "AverageSpeed": {"speed": "207.235"},
            },
            "status": "Finished",
        }
    ]
    result = transform_results(raw)
    r = result[0]
    assert r["driver_ref"] == "max_verstappen"
    assert r["constructor_ref"] == "red_bull"
    assert r["grid"] == 1
    assert r["position"] == 1
    assert r["points"] == 25.0
    assert r["laps"] == 57
    assert r["time_result"] == "1:33:56.736"
    assert r["fastest_lap_time"] == "1:33.996"
    assert r["fastest_lap_speed"] == 207.235
    assert r["status"] == "Finished"


def test_transform_results_dnf_no_time_no_fastest():
    raw = [
        {
            "Driver": {"driverId": "x"},
            "Constructor": {"constructorId": "y"},
            "grid": "5",
            "position": "20",
            "positionText": "R",
            "points": "0",
            "laps": "10",
            "status": "Engine",
        }
    ]
    result = transform_results(raw)
    r = result[0]
    assert r["time_result"] is None
    assert r["fastest_lap_time"] is None
    assert r["fastest_lap_speed"] is None
    assert r["status"] == "Engine"


# ─────────────────────────────────────────────────────────────────────────────
# transform_qualifying
# ─────────────────────────────────────────────────────────────────────────────


def test_transform_qualifying_all_sessions():
    raw = [
        {
            "Driver": {"driverId": "ham"},
            "Constructor": {"constructorId": "mercedes"},
            "position": "3",
            "Q1": "1:30.123",
            "Q2": "1:29.456",
            "Q3": "1:28.789",
        }
    ]
    result = transform_qualifying(raw)
    q = result[0]
    assert q["driver_ref"] == "ham"
    assert q["position"] == 3
    assert q["q1"] == "1:30.123"
    assert q["q2"] == "1:29.456"
    assert q["q3"] == "1:28.789"


def test_transform_qualifying_eliminated_q1():
    # Driver eliminated in Q1: no Q2, no Q3
    raw = [
        {
            "Driver": {"driverId": "x"},
            "Constructor": {"constructorId": "y"},
            "position": "18",
            "Q1": "1:32.500",
        }
    ]
    result = transform_qualifying(raw)
    assert result[0]["q1"] == "1:32.500"
    assert result[0]["q2"] is None
    assert result[0]["q3"] is None


# ─────────────────────────────────────────────────────────────────────────────
# transform_sprint
# ─────────────────────────────────────────────────────────────────────────────


def test_transform_sprint_basic():
    raw = [
        {
            "Driver": {"driverId": "ver"},
            "Constructor": {"constructorId": "red_bull"},
            "grid": "1",
            "position": "1",
            "positionText": "1",
            "points": "8",
            "laps": "23",
            "Time": {"time": "30:01.234"},
            "FastestLap": {"Time": {"time": "1:18.234"}},
            "status": "Finished",
        }
    ]
    result = transform_sprint(raw)
    s = result[0]
    assert s["driver_ref"] == "ver"
    assert s["points"] == 8.0
    assert s["fastest_lap_time"] == "1:18.234"


# ─────────────────────────────────────────────────────────────────────────────
# transform_driver_standings
# ─────────────────────────────────────────────────────────────────────────────


def test_transform_driver_standings():
    raw = [
        {
            "Driver": {"driverId": "ver"},
            "points": "454",
            "position": "1",
            "wins": "19",
        }
    ]
    result = transform_driver_standings(raw)
    s = result[0]
    assert s["driver_ref"] == "ver"
    assert s["points"] == 454.0
    assert s["position"] == 1
    assert s["wins"] == 19


# ─────────────────────────────────────────────────────────────────────────────
# transform_constructor_standings
# ─────────────────────────────────────────────────────────────────────────────


def test_transform_constructor_standings():
    raw = [
        {
            "Constructor": {"constructorId": "red_bull"},
            "points": "860",
            "position": "1",
            "wins": "21",
        }
    ]
    result = transform_constructor_standings(raw)
    s = result[0]
    assert s["constructor_ref"] == "red_bull"
    assert s["points"] == 860.0
    assert s["wins"] == 21


# ─────────────────────────────────────────────────────────────────────────────
# transform_pit_stops
# ─────────────────────────────────────────────────────────────────────────────


def test_transform_pit_stops_with_duration():
    raw = [
        {
            "driverId": "ver",
            "stop": "1",
            "lap": "15",
            "time": "14:32:55",
            "duration": "23.450",
        }
    ]
    result = transform_pit_stops(raw)
    p = result[0]
    assert p["driver_ref"] == "ver"
    assert p["stop"] == 1
    assert p["lap"] == 15
    assert p["duration"] == "23.450"
    assert p["duration_ms"] == 23450


def test_transform_pit_stops_invalid_duration():
    # If duration is non-numeric string, duration_ms must be None
    raw = [
        {
            "driverId": "ver",
            "stop": "1",
            "lap": "10",
            "time": "13:00:00",
            "duration": "invalid",
        }
    ]
    result = transform_pit_stops(raw)
    assert result[0]["duration"] == "invalid"
    assert result[0]["duration_ms"] is None


def test_transform_pit_stops_no_duration():
    raw = [{"driverId": "ham", "stop": "1", "lap": "20", "time": "15:00:00"}]
    result = transform_pit_stops(raw)
    assert result[0]["duration"] is None
    assert result[0]["duration_ms"] is None


# ─────────────────────────────────────────────────────────────────────────────
# transform_laps
# ─────────────────────────────────────────────────────────────────────────────


def test_transform_laps_explodes_timings():
    # One lap with 3 drivers must explode into 3 records
    raw = [
        {
            "number": "1",
            "Timings": [
                {"driverId": "ver", "position": "1", "time": "1:30.000"},
                {"driverId": "ham", "position": "2", "time": "1:30.500"},
                {"driverId": "lec", "position": "3", "time": "1:31.000"},
            ],
        }
    ]
    result = transform_laps(raw)
    assert len(result) == 3
    assert result[0]["driver_ref"] == "ver"
    assert result[0]["lap"] == 1
    assert result[0]["position"] == 1
    assert result[0]["time"] == "1:30.000"
    assert result[1]["driver_ref"] == "ham"
    assert result[2]["driver_ref"] == "lec"


def test_transform_laps_empty_timings():
    raw = [{"number": "1", "Timings": []}]
    assert transform_laps(raw) == []


def test_transform_laps_no_timings_key():
    raw = [{"number": "1"}]
    assert transform_laps(raw) == []
