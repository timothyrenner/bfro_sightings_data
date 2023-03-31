from prefect import flow, task, get_run_logger
import typer
from pathlib import Path
import polars as pl
from scripts.pull_weather import (
    get_missing_weather_keys,
    pull_missing_weather,
    merge_new_records_with_weather_cache,
)
from typing import Tuple


@task(name="Get missing weather keys")
def get_missing_weather_keys_task(
    geocoded_reports_file: Path, weather_cache_file: Path
) -> pl.DataFrame:
    return get_missing_weather_keys(geocoded_reports_file, weather_cache_file)


@task(name="Pull missing weather data")
def pull_weather_data(
    missing_weather_keys: pl.DataFrame,
    limit: int = 900,
) -> Tuple[pl.DataFrame, bool]:
    return pull_missing_weather(
        missing_weather_keys, limit=limit, logger=get_run_logger()
    )


@task(name="Merge weather data with cache.")
def merge_weather_data(
    weather_cache_file: Path, new_weather_data: pl.DataFrame
) -> pl.DataFrame:
    return merge_new_records_with_weather_cache(
        weather_cache_file, new_weather_data
    )


@flow(name="Update weather")
def update_weather(
    data_dir: Path = Path("data"),
    limit: int = 900,
) -> bool:
    logger = get_run_logger()

    weather_cache_file = data_dir / Path("raw/weather/weather_cache.csv")
    logger.info(f"weather_cache_file: {weather_cache_file}")

    geocoded_reports_file = data_dir / Path(
        "raw/geocoder/geocoded_reports.csv"
    )
    logger.info(f"geocoded_reports_file: {geocoded_reports_file}")

    source_weather_file = data_dir / Path("sources/weather_cache.csv")
    logger.info(f"source_weather_file: {source_weather_file}")

    logger.info("Getting missing weather keys.")
    missing_weather_keys = get_missing_weather_keys_task(
        geocoded_reports_file, weather_cache_file
    )
    if missing_weather_keys.is_empty():
        logger.info("Nothing new to pull. All done.")
        # Return false because the weather limit was not reached.
        # Signals to other flows we can proceed.
        return True

    logger.info(f"Total missing weather keys: {missing_weather_keys.shape[0]}")
    logger.info(f"Pulling {min(missing_weather_keys.shape[0], limit)}.")
    new_weather_data, weather_limit_reached = pull_weather_data(
        missing_weather_keys, limit=limit
    )
    logger.info(f"Pulled {new_weather_data.shape[0]} new weather records.")
    if not weather_cache_file.exists():
        logger.info(f"Weather cache file {weather_cache_file} does not exist.")
        logger.info("Saving what was just pulled.")
        weather_data_to_write = new_weather_data
    else:
        logger.info("Combining new weather data with existing weather data.")
        weather_data_to_write = merge_weather_data(
            weather_cache_file, new_weather_data
        )
    logger.info(f"Writing updated cache back to {weather_cache_file}.")
    weather_data_to_write.write_csv(weather_cache_file)
    logger.info(f"Writing updated cache to {source_weather_file}.")
    weather_data_to_write.write_csv(source_weather_file)
    logger.info("🌩️👣 All done with weather update 🌩️👣")
    # If we reach the weather limit, we cannot proceed downstream.
    return not weather_limit_reached


if __name__ == "__main__":
    typer.run(update_weather)
