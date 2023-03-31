import typer
from prefect import flow, task, get_run_logger
from prefect_dbt.cli.commands import DbtCoreOperation
from update_reports import update_reports
from update_geocoder import pull_and_update_geocoded_reports
from update_weather import update_weather
from pathlib import Path


@flow(name="Update sources")
def set_up_sources(
    data_dir: Path = Path("data"),
    weather_limit: int = 900,
    test_run: bool = False,
) -> bool:
    reports_updated = update_reports(data_dir=data_dir, test_run=test_run)
    geocoder_updated = pull_and_update_geocoded_reports(data_dir=data_dir)
    weather_updated = False
    if geocoder_updated:
        weather_updated = update_weather(
            limit=weather_limit, data_dir=data_dir
        )

    return reports_updated and geocoder_updated and weather_updated


@task(name="DBT test sources")
def dbt_test_sources() -> bool:
    logger = get_run_logger()
    logger.info("Testing sources.")
    DbtCoreOperation(
        commands=["dbt test --select local_files"],
        project_dir="bfro_mini_warehouse",
        profiles_dir="bfro_mini_warehouse",
    ).run()
    logger.info("Testing completed.")
    return True


@task(name="DBT run")
def dbt_run() -> bool:
    logger = get_run_logger()
    logger.info("Building csv files with DBT.")
    DbtCoreOperation(
        commands=["dbt run"],
        project_dir="bfro_mini_warehouse",
        profiles_dir="bfro_mini_warehouse",
    ).run()
    logger.info("DBT run completed.")

    return True


@task(name="DBT test")
def dbt_test() -> bool:
    logger = get_run_logger()
    logger.info("Testing DBT models.")
    DbtCoreOperation(
        commands=["dbt test --exclude source:*"],
        project_dir="bfro_mini_warehouse",
        profiles_dir="bfro_mini_warehouse",
    ).run()
    logger.info("Testing completed.")
    return True


@flow(name="DBT")
def dbt() -> bool:
    sources_pass = dbt_test_sources()
    if not sources_pass:
        return False
    run_completed = dbt_run()
    if not run_completed:
        return False
    tests_pass = dbt_test()
    return tests_pass


@flow(name="BFRO Pipeline")
def main(
    test_run: bool = True,
    dbt_only: bool = False,
) -> bool:
    logger = get_run_logger()
    weather_limit = 900
    if test_run:
        logger.info("Test run selected.")
        weather_limit = 25

    # data_dir needs to be hard coded to what DBT expects to see.
    # NOTE could make data dir a var, and template that in potentially,
    # depending on whether we can pass vars in to the dbt task or not.
    data_dir = Path("data")
    sources_updated = False
    if not dbt_only:
        sources_updated = set_up_sources(
            data_dir=data_dir, weather_limit=weather_limit, test_run=test_run
        )

    if not sources_updated and not dbt_only:
        logger.info("Source update incomplete. Terminating flow.")
        return False
    dbt()

    return True


if __name__ == "__main__":
    typer.run(main)