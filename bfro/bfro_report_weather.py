import click
import os
import pandas as pd
import csv
import json
import requests

from dotenv import find_dotenv, load_dotenv
from loguru import logger

# Load .env and grab the API key.
load_dotenv(find_dotenv())
VISUAL_CROSSING_KEY = os.environ.get("VISUAL_CROSSING_KEY")


def load_weather_cache(cache_file):
    return {(c[0], c[1]) for c in csv.reader(cache_file)}


def create_weather_request_url(lat, lon, time):
    return (
        "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/"
        f"services/timeline/{lat},{lon}/{time}"
    )


@click.command()
@click.argument("report_file", type=click.File("r"))
@click.argument("cache", type=str)
@click.option("-l", "--limit", default=900, type=int)
def main(report_file, cache, limit):
    # Load the cache if present.
    # The cache maps a (geohash, date) pair to a dark sky payload.
    if os.path.exists(cache):
        logger.info("Found cache, loading.")
        with open(cache, "r") as f:
            weather_cache = load_weather_cache(f)
    else:
        weather_cache = {}

    logger.info("Loading reports.")
    reports = pd.read_csv(report_file)

    # Take out the nan values.
    reports = reports[~reports.latitude.isnull()].drop_duplicates()

    # Write the requests to the output file.
    with open(cache, "a") as f:
        writer = csv.writer(f)
        total_requests = 0
        for _, r in reports[
            ["geohash", "date", "latitude", "longitude"]
        ].iterrows():
            # Skip if it's in the cache already.
            if (r.geohash, r.date) in weather_cache:
                continue
            if total_requests > limit:
                logger.info("Request limit reached. Stopping.")
                break

            # Make the weather request and save it to the cache.
            logger.info(f"Calling Visual Crossing - request {total_requests}")
            request_url = create_weather_request_url(
                r.latitude, r.longitude, r.date + "T00:00:00"
            )
            try:
                response = requests.get(
                    request_url,
                    params={
                        "key": VISUAL_CROSSING_KEY,
                        "include": "days",
                    },
                )
                weather_json = response.json()
            except Exception as e:
                logger.exception(
                    f"Encountered error with request {request_url}, {str(e)}."
                )
            finally:
                total_requests += 1

            writer.writerow(
                (r.geohash, r.date, request_url, json.dumps(weather_json))
            )


if __name__ == "__main__":
    main()
