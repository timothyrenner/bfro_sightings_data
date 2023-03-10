import typer
from loguru import logger
import duckdb
import polars as pl
from pathlib import Path


def combine_geocoded_reports(
    orig_reports: pl.DataFrame, new_reports: pl.DataFrame
) -> pl.DataFrame:
    return duckdb.sql(
        """
        WITH all_rows AS (
            SELECT * FROM orig_reports
            UNION ALL
            SELECT * FROM new_reports
        )
        SELECT * FROM all_rows 
        QUALIFY ROW_NUMBER() OVER(
            PARTITION BY number ORDER BY extraction_date DESC
        ) = 1
        """
    ).pl()


def main(
    orig_reports_file: Path,
    new_reports_file: Path,
    combined_reports_file: Path,
):
    logger.info(f"Reading {orig_reports_file.name}")
    orig_reports = pl.read_csv(orig_reports_file)
    logger.info(f"Reading {new_reports_file.name}")
    new_reports = pl.read_csv(new_reports_file)
    logger.info(
        f"Executing duckdb query to combine {orig_reports_file.name} "
        f"and {new_reports_file.name}."
    )
    combined_reports = combine_geocoded_reports(orig_reports, new_reports)
    logger.info(f"Saving combined reports to {combined_reports_file.name}")
    combined_reports.write_csv(combined_reports_file)
    logger.info("👣 done 👣")


if __name__ == "__main__":
    typer.run(main)
