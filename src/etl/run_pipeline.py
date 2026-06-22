"""
ETL Pipeline Runner.

[EN] Orchestrates the full ETL (Extract, Transform, Load) pipeline for
the F1 Insights Engine. Extracts data from the Jolpica F1 API, transforms
it into the database schema format, and loads it into the database.
Supports command-line arguments for year selection and optional lap time
loading.

[PT-BR] Orquestra o pipeline ETL (Extração, Transformação, Carga) completo
do F1 Insights Engine. Extrai dados da API Jolpica F1, transforma-os no
formato do schema do banco de dados e carrega-os no banco. Suporta
argumentos de linha de comando para seleção de ano e carregamento opcional
de tempos de volta.

Author: Bruno Krieger
"""

import argparse
import asyncio
import logging
import time

from src.core.logging_config import configure_logging
from src.db.database import AsyncSessionLocal
from src.etl.extract import (
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
from src.etl.load import (
    _build_lookup_caches,
    create_tables,
    load_circuits,
    load_constructor_standings,
    load_constructors,
    load_driver_standings,
    load_drivers,
    load_laps,
    load_pit_stops,
    load_qualifying,
    load_races,
    load_results,
    load_seasons,
    load_sprint,
    load_statuses,
)
from src.etl.transform import (
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

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Pipeline Orchestration / Orquestração do Pipeline
# ─────────────────────────────────────────────────────────────────────────────


async def run_global_entities() -> None:
    """
    Load global (non-year-specific) entities.

    [EN] Extracts, transforms, and loads seasons, statuses, circuits,
    drivers, and constructors. These entities are shared across all
    seasons and must be loaded first to satisfy FK constraints.

    [PT-BR] Extrai, transforma e carrega temporadas, status, circuitos,
    pilotos e construtores. Essas entidades são compartilhadas entre
    todas as temporadas e devem ser carregadas primeiro para satisfazer
    restrições de FK.

    Author: Bruno Krieger
    """
    logger.info("\n" + "=" * 60)
    logger.info("STEP 1: Loading global entities")
    logger.info("=" * 60)

    # Seasons / Temporadas
    raw_seasons = extract_seasons()
    clean_seasons = transform_seasons(raw_seasons)
    await load_seasons(clean_seasons)

    # Statuses / Status
    raw_statuses = extract_statuses()
    clean_statuses = transform_statuses(raw_statuses)
    await load_statuses(clean_statuses)

    # Circuits / Circuitos
    raw_circuits = extract_circuits()
    clean_circuits = transform_circuits(raw_circuits)
    await load_circuits(clean_circuits)

    # Drivers / Pilotos
    raw_drivers = extract_drivers()
    clean_drivers = transform_drivers(raw_drivers)
    await load_drivers(clean_drivers)

    # Constructors / Construtores
    raw_constructors = extract_constructors()
    clean_constructors = transform_constructors(raw_constructors)
    await load_constructors(clean_constructors)


async def run_year_pipeline(year: int, include_laps: bool = False) -> None:
    """
    Run the ETL pipeline for a specific year.

    [EN] Extracts, transforms, and loads all year-specific entities:
    races, race results, qualifying, sprint results, standings,
    pit stops, and optionally lap times.

    [PT-BR] Extrai, transforma e carrega todas as entidades específicas
    de um ano: corridas, resultados, classificação, sprint, classificações
    de campeonato, pit stops e opcionalmente tempos de volta.

    Args:
        year: Season year to process.
        include_laps: Whether to load lap time data (very large volume).

    Author: Bruno Krieger
    """
    logger.info(f"\n{'=' * 60}")
    logger.info(f"STEP 2: Processing season {year}")
    logger.info(f"{'=' * 60}")

    # ── Races / Corridas ────────────────────────────────────────
    raw_races = extract_races(year)
    clean_races = transform_races(raw_races)
    await load_races(clean_races)

    # ── Per-race data / Dados por corrida ───────────────────────
    total_results = 0
    total_qualifying = 0
    total_sprint = 0
    total_pit_stops = 0
    total_laps = 0

    for race in clean_races:
        round_num = race["round"]
        race_name = race["race_name"]
        logger.info(f"\n  Processing R{round_num:02d}: {race_name}...")

        # Race Results / Resultados
        raw_results = extract_results(year, round_num)
        if raw_results:
            clean_results = transform_results(raw_results)
            count = await load_results(clean_results, year, round_num)
            total_results += count

        # Qualifying / Classificação
        raw_qualifying = extract_qualifying(year, round_num)
        if raw_qualifying:
            clean_qualifying = transform_qualifying(raw_qualifying)
            count = await load_qualifying(clean_qualifying, year, round_num)
            total_qualifying += count

        # Sprint (only 2021+) / Sprint (apenas 2021+)
        if year >= 2021:
            raw_sprint = extract_sprint(year, round_num)
            if raw_sprint:
                clean_sprint = transform_sprint(raw_sprint)
                count = await load_sprint(clean_sprint, year, round_num)
                total_sprint += count

        # Pit Stops / Pit Stops
        raw_pit_stops = extract_pit_stops(year, round_num)
        if raw_pit_stops:
            clean_pit_stops = transform_pit_stops(raw_pit_stops)
            count = await load_pit_stops(clean_pit_stops, year, round_num)
            total_pit_stops += count

        # Lap Times (optional) / Tempos de volta (opcional)
        if include_laps and year >= 1996:
            raw_laps = extract_laps(year, round_num)
            if raw_laps:
                clean_laps = transform_laps(raw_laps)
                count = await load_laps(clean_laps, year, round_num)
                total_laps += count

    logger.info(f"\n  Season {year} per-race totals:")
    logger.info(f"    Results:    {total_results} new")
    logger.info(f"    Qualifying: {total_qualifying} new")
    logger.info(f"    Sprint:     {total_sprint} new")
    logger.info(f"    Pit Stops:  {total_pit_stops} new")
    if include_laps:
        logger.info(f"    Lap Times:  {total_laps} new")

    # ── Standings / Classificações ──────────────────────────────
    logger.info(f"\n  Loading standings for {year}...")

    raw_driver_standings = extract_driver_standings(year)
    if raw_driver_standings:
        clean_driver_standings = transform_driver_standings(raw_driver_standings)
        await load_driver_standings(clean_driver_standings, year)

    raw_constructor_standings = extract_constructor_standings(year)
    if raw_constructor_standings:
        clean_constructor_standings = transform_constructor_standings(
            raw_constructor_standings
        )
        await load_constructor_standings(clean_constructor_standings, year)


async def main(years: list[int], include_laps: bool = False) -> None:
    """
    Execute the complete ETL pipeline.

    [EN] Runs the following stages in order:
    1. Create database tables
    2. Load global entities (seasons, statuses, circuits, drivers, constructors)
    3. Build FK lookup caches
    4. For each year: load races → results → qualifying → sprint → pit stops → laps → standings

    [PT-BR] Executa as seguintes etapas em ordem:
    1. Criar tabelas do banco
    2. Carregar entidades globais (temporadas, status, circuitos, pilotos, construtores)
    3. Construir caches de lookup FK
    4. Para cada ano: corridas → resultados → classificação → sprint → pit stops → voltas → classificações

    Args:
        years: List of season years to process.
        include_laps: Whether to include lap time data.

    Author: Bruno Krieger
    """
    start_time = time.time()

    logger.info("=" * 60)
    logger.info("F1 Insights Engine — ETL Pipeline")
    logger.info(f"Years: {years}")
    logger.info(f"Include laps: {include_laps}")
    logger.info("=" * 60)

    # Step 0: Create tables / Criar tabelas
    await create_tables()

    # Step 1: Global entities / Entidades globais
    await run_global_entities()

    # Build caches after loading globals
    # Construir caches após carregar globais
    async with AsyncSessionLocal() as session:
        await _build_lookup_caches(session)
    logger.info("  [OK] FK lookup caches built.")

    # Step 2: Year-specific data / Dados específicos por ano
    for year in years:
        await run_year_pipeline(year, include_laps=include_laps)

    elapsed = time.time() - start_time
    logger.info(f"\n{'=' * 60}")
    logger.info(f"ETL Pipeline completed in {elapsed:.1f}s")
    logger.info(f"{'=' * 60}")


def parse_args():
    """
    Parse command-line arguments.

    [EN] Supports --years (comma-separated list of years) and
    --include-laps flag.
    [PT-BR] Suporta --years (lista de anos separada por vírgula) e
    flag --include-laps.

    Author: Bruno Krieger
    """
    parser = argparse.ArgumentParser(
        description="F1 Insights Engine — ETL Pipeline Runner"
    )
    parser.add_argument(
        "--years",
        type=str,
        default="2023",
        help="Comma-separated list of years to process (default: 2023)",
    )
    parser.add_argument(
        "--include-laps",
        action="store_true",
        default=False,
        help="Include lap time data (very large volume, disabled by default)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    configure_logging()
    args = parse_args()
    year_list = [int(y.strip()) for y in args.years.split(",")]
    asyncio.run(main(year_list, include_laps=args.include_laps))
