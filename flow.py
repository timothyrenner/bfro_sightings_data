from prefect import flow, task, get_run_logger
import typer
from pathlib import Path
import polars as pl
from lxml import etree
from scripts.extract_locations_from_kml import extract_geocoded_reports
from scripts.combine_geocoded_reports import combine_geocoded_reports
from datetime import date


@task(name="Extract geocoded reports")
def extract_geocoded_reports_task(kml_file: Path) -> pl.DataFrame:
    logger = get_run_logger()
    logger.info(f"Reading and parsing {kml_file.name}")
    report_xml = etree.fromstring(kml_file.read_bytes())
    logger.info(f"Extracting geocoded reports from {kml_file.name}")
    return extract_geocoded_reports(report_xml).with_columns(
        pl.lot(date.today()).alias("extraction_date")
    )


@task(name="Combine geocoded reports")
def combine_geocoded_reports_task(
    orig_report_file: Path, new_reports: pl.DataFrame
) -> pl.DataFrame:
    logger = get_run_logger()
    logger.info(f"Reading original reports from {orig_report_file.name}")
    orig_reports = pl.read_csv(orig_report_file)
    logger.info("Combining original and new reports.")
    combined_reports = combine_geocoded_reports(orig_reports, new_reports)
    return combined_reports


@task(name="Save combined reports back to raw")
def save_combined_reports(
    combined_reports: pl.DataFrame, orig_report_file: Path
):
    logger = get_run_logger()
    logger.info(f"Saving combined reports back into {orig_report_file.name}")
    combined_reports.write_csv(orig_report_file)


@flow(name="Update geocoded reports")
def pull_and_update_geocoded_reports(
    kml_file: Path, orig_report_file: Path
) -> pl.DataFrame:
    new_geocoded_reports = extract_geocoded_reports_task(kml_file)
    combined_geocoded_reports = combine_geocoded_reports_task(
        orig_report_file, new_geocoded_reports
    )
    save_combined_reports(combined_geocoded_reports, orig_report_file)
    return combined_geocoded_reports


if __name__ == "__main__":
    typer.run(pull_and_update_geocoded_reports)
