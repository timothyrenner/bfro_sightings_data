import typer
from pathlib import Path
import duckdb


def main(
    orig_json_file: Path = "data_old/raw/bfro_reports.json",
    new_csv_file: Path = "data/raw/reports/bfro_reports.csv",
):
    duckdb.sql(
        f"""
        SELECT *, CURRENT_TIMESTAMP AS PULLED_DATETIME 
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
            "A_&_G_REFERENCES" IS NULL
        )
        """
    ).to_csv(str(new_csv_file), header=True)


if __name__ == "__main__":
    typer.run(main)
