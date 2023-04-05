import typer
from pathlib import Path
import duckdb


def main(
    orig_json_file: Path = "data_old/raw/bfro_reports.json",
    new_csv_file: Path = "data/raw/reports/bfro_reports.csv",
):
    duckdb.sql(
        f"""
        SELECT 
            YEAR AS year,
            SEASON AS season,
            MONTH AS month,
            DATE AS date,
            STATE AS state,
            COUNTY AS county,
            LOCATION_DETAILS AS location_details,
            NEAREST_TOWN AS nearest_town,
            NEAREST_ROAD AS nearest_road,
            OBSERVED AS observed,
            ALSO_NOTICED AS also_noticed,
            OTHER_WITNESSES AS other_witnesses,
            OTHER_STORIES AS other_stories,
            TIME_AND_CONDITIONS AS time_and_conditions,
            ENVIRONMENT AS environment,
            REPORT_NUMBER AS report_number,
            REPORT_CLASS AS report_class,
            "A_&_G_References" AS "a_&_g_references",
            CURRENT_TIMESTAMP AS pulled_datetime
        FROM '{orig_json_file}'
        WHERE NOT (
            year IS NULL AND
            season IS NULL AND
            month IS NULL AND
            date IS NULL AND
            state IS NULL AND
            county IS NULL AND
            location_details IS NULL AND
            nearest_town IS NULL AND
            nearest_road IS NULL AND
            observed IS NULL AND
            also_noticed IS NULL AND
            other_witnesses IS NULL AND
            other_stories IS NULL AND
            time_and_conditions IS NULL AND
            environment IS NULL AND
            report_number IS NULL AND
            report_class IS NULL AND
            "a_&_g_references" IS NULL
        )
        """
    ).to_csv(str(new_csv_file), header=True)


if __name__ == "__main__":
    typer.run(main)
