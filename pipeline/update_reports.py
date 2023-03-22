from prefect import flow, task, get_run_logger
import typer
from pathlib import Path
import polars as pl
import duckdb
from prefect_shell import ShellOperation


@task(name="Run scraper")
def run_scraper_task(reports_new_file: Path, test_run: bool = False) -> bool:
    logger = get_run_logger()
    logger.info("Firing up the scraper.")
    try:
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
        return True
    except Exception:
        logger.exception("Error running scraper.")
        return False


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
            SELECT * FROM '{reports_new_file}'
        )
        SELECT * FROM all_rows
        QUALIFY ROW_NUMBER() OVER(
            PARTITION BY report_number ORDER BY pulled_datetime DESC
        ) = 1
        """
    ).pl()


@flow(name="Update reports")
def update_reports(
    reports_orig_file: Path = Path("data_new/raw/reports/bfro_reports.csv"),
    reports_new_file: Path = Path(
        "data_new/raw/reports/bfro_reports_new.json"
    ),
    reports_source_file: Path = Path("data_new/sources/bfro_reports.csv"),
    test_run: bool = False,
) -> bool:
    logger = get_run_logger()
    scraper_successful = run_scraper_task(reports_new_file, test_run=test_run)

    if not scraper_successful:
        logger.error("Scraper failed.")
        return False

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


if __name__ == "__main__":
    typer.run(update_reports)
