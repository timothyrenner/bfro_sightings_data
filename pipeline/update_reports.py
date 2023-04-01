from prefect import flow, task, get_run_logger
import typer
from pathlib import Path
import polars as pl
import duckdb
from prefect_shell import ShellOperation


@task(name="Run scraper")
def run_scraper_task(reports_new_file: Path, test_run: bool = False) -> Path:
    logger = get_run_logger()
    logger.info("Firing up the scraper.")
    scraper_working_dir = "scraper/bfro_scrape"
    scraper = ShellOperation(
        commands=[
            "scrapy crawl bfro_reports "
            f"-a test_run={test_run} "
            f"--overwrite-output new_reports.json:jsonlines"
        ],
        working_dir=scraper_working_dir,
    ).trigger()

    scraper.wait_for_completion()
    logger.info(
        "Scraper completed. "
        f"Saved to {scraper_working_dir}/new_reports.json"
    )

    ShellOperation(
        commands=[
            f"cp {scraper_working_dir}/new_reports.json {reports_new_file}"
        ]
    ).run()
    return reports_new_file


@task(name="Combine reports")
def combine_reports_task(
    reports_orig_file: Path, reports_new_file: Path
) -> pl.DataFrame:
    logger = get_run_logger()
    logger.info(
        f"Combining reports in {reports_orig_file} with {reports_new_file}."
    )
    return duckdb.sql(
        f"""
        WITH all_rows AS (
            SELECT * FROM '{reports_orig_file}'
            UNION ALL
            SELECT * FROM READ_NDJSON(
                '{reports_new_file}',
                columns={{
                    YEAR: 'VARCHAR',
                    SEASON: 'VARCHAR',
                    MONTH: 'VARCHAR',
                    DATE: 'VARCHAR',
                    STATE: 'VARCHAR',
                    COUNTY: 'VARCHAR',
                    LOCATION_DETAILS: 'VARCHAR',
                    NEAREST_TOWN: 'VARCHAR',
                    NEAREST_ROAD: 'VARCHAR',
                    OBSERVED: 'VARCHAR',
                    ALSO_NOTICED: 'VARCHAR',
                    OTHER_WITNESSES: 'VARCHAR',
                    OTHER_STORIES: 'VARCHAR',
                    TIME_AND_CONDITIONS: 'VARCHAR',
                    ENVIRONMENT: 'VARCHAR',
                    REPORT_NUMBER: 'BIGINT',
                    REPORT_CLASS: 'VARCHAR',
                    "A_&_G_References": 'VARCHAR',
                    PULLED_DATETIME: 'VARCHAR'
                }}
            )
        )
        SELECT * FROM all_rows
        QUALIFY ROW_NUMBER() OVER(
            PARTITION BY report_number ORDER BY pulled_datetime DESC
        ) = 1
        """
    ).pl()


@flow(name="Update reports")
def update_reports(
    data_dir: Path = Path("data"),
    test_run: bool = False,
) -> bool:
    logger = get_run_logger()
    reports_orig_file = data_dir / Path("raw/reports/bfro_reports.csv")
    logger.info(f"reports_orig_file: {reports_orig_file}")

    reports_new_file = data_dir / Path("raw/reports/bfro_reports_new.json")
    logger.info(f"reports_new_file: {reports_new_file}")

    reports_source_file = data_dir / Path("sources/bfro_reports.csv")
    logger.info(f"reports_source_file: {reports_source_file}")

    # Mostly the output is a signal that the task completed, and establishes
    # the data dependency between this and the combining reports task.
    reports_new_file = run_scraper_task(reports_new_file, test_run=test_run)

    if reports_orig_file.exists():
        logger.info(f"{reports_orig_file} exists, combining with new data.")
        combined_reports = combine_reports_task(
            reports_orig_file, reports_new_file
        )
    else:
        combined_reports = pl.read_csv(reports_new_file)

    logger.info(f"Writing combined reports back to {reports_orig_file}.")
    combined_reports.write_csv(reports_orig_file)
    logger.info(f"Writing combined reports to {reports_source_file}.")
    combined_reports.write_csv(reports_source_file)
    return True


if __name__ == "__main__":
    typer.run(update_reports)
