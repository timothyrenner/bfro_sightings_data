import typer
from loguru import logger
import duckdb


def main(first_csv: str, second_csv: str, output_csv: str):
    logger.info(
        f"Executing duckdb query to combine {first_csv} and {second_csv}."
    )
    duckdb.sql(
        f"""
        WITH all_rows AS (
            SELECT * FROM '{first_csv}'
            UNION ALL
            SELECT * FROM '{second_csv}'
        )
        SELECT * FROM all_rows 
        QUALIFY ROW_NUMBER() OVER(
            PARTITION BY number ORDER BY extraction_date DESC
        ) = 1
        """
    ).to_csv(output_csv)
    logger.info("👣 done 👣")


if __name__ == "__main__":
    typer.run(main)
