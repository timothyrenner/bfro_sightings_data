from prefect import flow, task, get_run_logger
from prefect_shell import ShellOperation
import typer
from pathlib import Path
import polars as pl
from lxml import etree
from scripts.extract_locations_from_kml import extract_geocoded_reports
from scripts.combine_geocoded_reports import combine_geocoded_reports


@task(name="Unzip aspx file")
def download_and_unzip_aspx_file(aspx_file: Path) -> Path:
    ShellOperation(
        commands=[
            "wget http://www.bfro.net/app/AllReportsKMZ.aspx",
            f"mv {aspx_file.name} {aspx_file.parent}",
            f"unzip -o {aspx_file} -d {aspx_file.parent}",
        ]
    ).run()
    return aspx_file.parent / "doc.kml"


@task(name="Extract geocoded reports")
def extract_geocoded_reports_task(kml_file: Path) -> pl.DataFrame:
    logger = get_run_logger()
    logger.info(f"Reading and parsing {kml_file.name}")
    report_xml = etree.fromstring(kml_file.read_bytes())
    logger.info(f"Extracting geocoded reports from {kml_file.name}")
    return extract_geocoded_reports(report_xml)


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
    aspx_file: Path = Path("./data_new/raw/geocoder/AllReportsKMZ.aspx"),
    orig_report_file: Path = Path(
        "./data_new/raw/geocoder/geocoded_reports.csv"
    ),
    source_report_file: Path = Path("./data_new/sources/geocoded_reports.csv"),
) -> bool:
    kml_file = download_and_unzip_aspx_file(aspx_file)
    new_geocoded_reports = extract_geocoded_reports_task(kml_file)
    if orig_report_file.exists():
        combined_geocoded_reports = combine_geocoded_reports_task(
            orig_report_file, new_geocoded_reports
        )
    else:
        combined_geocoded_reports = new_geocoded_reports
    save_combined_reports(combined_geocoded_reports, orig_report_file)
    save_combined_reports(combined_geocoded_reports, source_report_file)
    # Signals to downstream flows that the source is ready.
    return True


if __name__ == "__main__":
    typer.run(pull_and_update_geocoded_reports)
