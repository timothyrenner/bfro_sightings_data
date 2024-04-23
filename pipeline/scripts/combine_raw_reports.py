import typer
from pathlib import Path
from loguru import logger
import duckdb
import polars as pl


def main(
    reports_orig_file: Path, reports_new_file: Path, reports_out_file: Path
):
    logger.info(f"reports_orig_file: {reports_orig_file.name}")
    logger.info(f"reports_new_file: {reports_new_file.name}")
    logger.info(f"reports_out_file: {reports_out_file.name}")

    if reports_orig_file.exists():
        combined_reports_frame = duckdb.sql(
            f"""
            WITH all_rows AS (
                SELECT * FROM '{reports_orig_file}'
                UNION ALL
                SELECT * FROM READ_NDJSON(
                    '{reports_new_file}',
                    columns={{
                        year: 'VARCHAR',
                        season: 'VARCHAR',
                        month: 'VARCHAR',
                        date: 'VARCHAR',
                        state: 'VARCHAR',
                        county: 'VARCHAR',
                        location_details: 'VARCHAR',
                        nearest_town: 'VARCHAR',
                        nearest_road: 'VARCHAR',
                        observed: 'VARCHAR',
                        also_noticed: 'VARCHAR',
                        other_witnesses: 'VARCHAR',
                        other_stories: 'VARCHAR',
                        time_and_conditions: 'VARCHAR',
                        environment: 'VARCHAR',
                        report_number: 'BIGINT',
                        report_class: 'VARCHAR',
                        "a_&_g_references": 'VARCHAR',
                        pulled_datetime: 'VARCHAR'
                    }}
                )
            )
            SELECT * FROM all_rows
            QUALIFY ROW_NUMBER() OVER(
                PARTITION BY report_number ORDER BY pulled_datetime DESC
            ) = 1
            """
        ).pl()
    else:
        combined_reports_frame = pl.read_ndjson(reports_new_file)

    combined_reports_frame.write_csv(reports_out_file)
    logger.info("Done!")


if __name__ == "__main__":
    typer.run(main)
