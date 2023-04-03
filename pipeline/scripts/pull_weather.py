import typer
from pathlib import Path
import polars as pl
import h3
import duckdb
from typing import Dict, List, Tuple
from dotenv import load_dotenv, find_dotenv
import os
import requests
import loguru
from loguru import logger
from datetime import date, datetime


def get_visual_crossing_key_from_env() -> str:
    load_dotenv(find_dotenv())
    visual_crossing_key = os.getenv("VISUAL_CROSSING_KEY")
    if not visual_crossing_key:
        raise ValueError(
            "Unable to find VISUAL_CROSSING_KEY in .env or environment."
        )
    return visual_crossing_key


def get_missing_weather_keys(
    geocoded_reports: Path, weather_cache: Path
) -> pl.DataFrame:
    if weather_cache.exists():
        return duckdb.sql(
            f"""
            SELECT
                gr.hexid,
                gr.timestamp
            FROM
                '{geocoded_reports}' AS gr
            LEFT JOIN
                '{weather_cache}' AS wc
                ON gr.hexid = wc.hexid AND gr.timestamp = wc.timestamp
            WHERE
                (wc.timestamp IS NULL OR wc.hexid IS NULL) AND
                gr.hexid IS NOT NULL AND
                gr.timestamp IS NOT NULL
            """
        ).pl()
    else:
        return duckdb.sql(
            f"""
            SELECT
                hexid,
                timestamp
            FROM '{geocoded_reports}'
            """
        ).pl()


def create_weather_request(
    latitude: float, longitude: float, timestamp: datetime
) -> str:
    # Note - timestamp comes in as a datetime because duckdb's csv parser
    # recognizes the format.
    return (
        "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/"
        f"services/timeline/{latitude},{longitude}/"
        f"{timestamp.strftime('%Y-%m-%dT%H:%M:%S')}"
    )


def pull_missing_weather(
    missing_weather_keys: pl.DataFrame,
    visual_crossing_key: str,
    limit: int = 900,
    logger=loguru.logger,
) -> Tuple[pl.DataFrame, bool]:
    weather_data: List[Dict[str, str]] = []
    total_calls = 0
    for row in missing_weather_keys.iter_rows(named=True):
        latitude, longitude = h3.h3_to_geo(row["hexid"])
        weather_request = create_weather_request(
            latitude, longitude, row["timestamp"]
        )
        logger.info(f"Making weather request: {weather_request}")
        response = requests.get(
            weather_request,
            params={"key": visual_crossing_key, "include": "days"},
        )
        if response.ok:
            weather_response = response.text
            logger.info("Weather request successful.")
        else:
            logger.warning(
                f"Encountered error with request {weather_request}."
            )
            # Set the weather data to None here so we don't just pile up bad
            # pulls from run to run.
            weather_response = None
        total_calls += 1
        weather_data.append(
            {
                **row,
                "date_pulled": f"{date.today():%Y-%m-%d}",
                "data": weather_response,
            }
        )
        if total_calls > limit:
            logger.info("Call limit reached. Terminating.")
            break
    return pl.from_dicts(weather_data), (total_calls > limit)


def merge_new_records_with_weather_cache(
    weather_cache_file: Path, new_weather_data: pl.DataFrame
) -> pl.DataFrame:
    # Theoretically this should be a straight union but it doesn't hurt to have
    # a little extra security.
    return duckdb.sql(
        f"""
        WITH all_rows AS (
            SELECT * FROM '{weather_cache_file}'
            UNION ALL
            SELECT * FROM new_weather_data
        )
        SELECT * FROM all_rows
        QUALIFY ROW_NUMBER() OVER(
            PARTITION BY hexid, timestamp ORDER BY date_pulled
        ) = 1
        """
    ).pl()


def main(
    weather_cache_file: Path, geocoded_reports_file: Path, limit: int = 900
):
    visual_crossing_key = get_visual_crossing_key_from_env()
    logger.info(f"Getting missing weather keys from {geocoded_reports_file}.")
    missing_weather_keys = get_missing_weather_keys(
        geocoded_reports_file, weather_cache_file
    )
    if missing_weather_keys.is_empty():
        logger.info("Nothing new to pull. All done.")
        return
    logger.info("Pulling missing weather data.")
    new_weather_data, _ = pull_missing_weather(
        missing_weather_keys, visual_crossing_key, limit
    )

    if not weather_cache_file.exists():
        logger.info(f"Weather cache file {weather_cache_file} does not exist.")
        logger.info("Saving what was just pulled.")
        new_weather_data.write_csv(weather_cache_file)
    else:
        logger.info("Combining new weather data with existing weather data.")
        merge_new_records_with_weather_cache(
            weather_cache_file, new_weather_data
        ).write_csv(weather_cache_file)


if __name__ == "__main__":
    typer.run(main)
