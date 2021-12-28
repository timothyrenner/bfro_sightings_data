import click
import os
import pandas as pd
import csv
import json
import requests

from dotenv import find_dotenv, load_dotenv
from toolz import curry
from loguru import logger


def load_weather_cache(cache_file):
    return {
        (c[0], c[1])
        for c in csv.reader(cache_file)
    }


def _create_weather_request(lat, lon, time, key=None):
    return "https://api.darksky.net/forecast/{}/{},{},{}?exclude={}".format(
        key,
        lat,
        lon,
        time,
        "currently,hourly,minutely"
    )


@click.command()
@click.argument('report_file', type=click.File('r'))
@click.argument('cache', type=str)
def main(report_file, cache):

    # Load .env and grab the API key.
    load_dotenv(find_dotenv())
    dark_sky_key = os.environ.get("DARK_SKY_KEY")

    # Load the cache if present.
    # The cache maps a (geohash, date) pair to a dark sky payload.
    if os.path.exists(cache):
        with open(cache, "r") as f:
            weather_cache = load_weather_cache(f)
    else:
        weather_cache = {}

    reports = pd.read_csv(report_file)

    # Take out the nan values.
    reports = reports[~reports.latitude.isnull()].drop_duplicates()

    # Partially apply the key to the request.
    create_weather_request = curry(_create_weather_request)(key=dark_sky_key)

    # Write the requests to the output file.
    with open(cache, "a") as f:
        writer = csv.writer(f)
        for _, r in reports[
            ["geohash", "date", "latitude", "longitude"]
        ].iterrows():

            # Skip if it's in the cache already.
            if (r.geohash, r.date) in weather_cache:
                continue

            # Make the weather request and save it to the cache.
            request = create_weather_request(
                r.latitude,
                r.longitude,
                str(r.date)+"T00:00:00"
            )
            try:
                response = requests.get(request)
                weather_json = response.json()
            except Exception as e:
                logger.exception(
                    f"Encountered error with request {request}, {str(e)}."
                )

            writer.writerow((r.geohash, r.date, json.dumps(weather_json)))


if __name__ == "__main__":
    main()
