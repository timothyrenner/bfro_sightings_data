import click
import os
import pandas as pd
import csv

from dotenv import find_dotenv, load_dotenv
from toolz import curry


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
@click.option('--cache', '-c', type=click.File('r'), default=None)
@click.option('--output-file', '-o', type=click.File('w'), default='-')
def main(report_file, cache, output_file):

    # Load .env and grab the API key.
    load_dotenv(find_dotenv())
    dark_sky_key = os.environ.get("DARK_SKY_KEY")

    # Load the cache if present.
    # The cache maps a (geohash, date) pair to a dark sky payload.
    weather_cache = load_weather_cache(cache) if cache else {}

    reports = pd.read_csv(report_file)

    # Take out the nan values.
    reports = reports[~reports.latitude.isnull()].drop_duplicates()

    # Partially apply the key to the request.
    create_weather_request = curry(_create_weather_request)(key=dark_sky_key)

    writer = csv.writer(output_file)

    # Write the requests to the output file.
    for _,r in reports[['geohash','date','latitude','longitude']].iterrows():
        
        # Skip if it's in the cache already.
        if (r.geohash, r.date) in weather_cache: continue
        
        writer.writerow([
            r.geohash,
            r.date,
            create_weather_request(
                r.latitude,
                r.longitude,
                str(r.date)+"T00:00:00"
            )
        ])


if __name__ == "__main__":
    main()
