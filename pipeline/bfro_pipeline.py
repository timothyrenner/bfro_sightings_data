import typer
from prefect import flow, task, get_run_logger
from prefect_dbt.cli.commands import DbtCoreOperation
from update_reports import update_reports
from update_geocoder import pull_and_update_geocoded_reports
from update_weather import update_weather
from pathlib import Path
from typing import Optional


@flow(name="Update sources")
def set_up_sources(
    data_dir: Path = Path("data"),
    weather_limit: int = 900,
    test_run: bool = False,
    visual_crossing_key: Optional[str] = None,
) -> bool:
    reports_updated = update_reports(data_dir=data_dir, test_run=test_run)
    geocoder_updated = pull_and_update_geocoded_reports(data_dir=data_dir)
    weather_updated = False
    if geocoder_updated:
        weather_updated = update_weather(
            limit=weather_limit,
            data_dir=data_dir,
            visual_crossing_key=visual_crossing_key,
        )

    return reports_updated and geocoder_updated and weather_updated


@task(name="DBT test sources")
def dbt_test_sources(data_dir: Path = Path("data")) -> bool:
    logger = get_run_logger()
    logger.info("Testing sources.")
    DbtCoreOperation(
        commands=[
            "dbt test --select source:local_files "
            f'--vars \'{{"data_dir":"{data_dir.absolute()}"}}\''
        ],
        project_dir="bfro_mini_warehouse",
        profiles_dir="bfro_mini_warehouse",
    ).run()
    logger.info("Testing completed.")
    return True


@task(name="DBT run")
def dbt_run(data_dir: Path = Path("data")) -> bool:
    logger = get_run_logger()
    logger.info("Building csv files with DBT.")
    DbtCoreOperation(
        commands=[
            f'dbt run --vars \'{{"data_dir":"{data_dir.absolute()}"}}\''
        ],
        project_dir="bfro_mini_warehouse",
        profiles_dir="bfro_mini_warehouse",
    ).run()
    logger.info("DBT run completed.")

    return True


@task(name="DBT test")
def dbt_test(data_dir: Path = Path("data")) -> bool:
    logger = get_run_logger()
    logger.info("Testing DBT models.")
    DbtCoreOperation(
        commands=[
            "dbt test --exclude source:* "
            # Yikes that double escaping 😬
            f'--vars \'{{"data_dir":"{data_dir.absolute()}"}}\''
        ],
        project_dir="bfro_mini_warehouse",
        profiles_dir="bfro_mini_warehouse",
    ).run()
    logger.info("Testing completed.")
    return True


@flow(name="DBT")
def dbt(data_dir: Path = Path("data")) -> bool:
    sources_pass = dbt_test_sources(data_dir)
    if not sources_pass:
        return False
    run_completed = dbt_run(data_dir)
    if not run_completed:
        return False
    tests_pass = dbt_test(data_dir)
    return tests_pass


@flow(name="BFRO Pipeline")
def main(
    test_run: bool = False,
    dbt_only: bool = False,
    data_dir: Path = Path("data"),
    visual_crossing_key: Optional[str] = None,
) -> bool:
    logger = get_run_logger()
    weather_limit = 900
    if test_run:
        logger.info("Test run selected.")
        weather_limit = 25

    sources_updated = False
    if not dbt_only:
        sources_updated = set_up_sources(
            data_dir=data_dir,
            weather_limit=weather_limit,
            test_run=test_run,
            visual_crossing_key=visual_crossing_key,
        )

    if not sources_updated and not dbt_only:
        logger.info("Source update incomplete. Terminating flow.")
        return False
    dbt(data_dir=data_dir)

    return True


if __name__ == "__main__":
    typer.run(main)
