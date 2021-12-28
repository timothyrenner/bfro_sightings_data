import click
import json
import csv

from toolz import get, get_in


@click.command()
@click.argument('report_file', type=click.File('r'))
@click.argument('weather_file', type=click.File('r'))
@click.argument('weather_join_file', type=click.File('w'))
def main(report_file, weather_file, weather_join_file):

    weather_reader = csv.reader(weather_file)

    # Load the weather into a dictionary.
    weather_cache = {
        # Extract the dict with the weather information.
        (r[0], r[1]): get_in(["daily", "data", 0], json.loads(r[-1]), {})
        for r in weather_reader
    }

    report_reader = csv.DictReader(report_file)

    fieldnames = report_reader.fieldnames + [
        "temperature_high",
        "temperature_mid",
        "temperature_low",
        "dew_point",
        "humidity",
        "cloud_cover",
        "moon_phase",
        "precip_intensity",
        "precip_probability",
        "precip_type",
        "pressure",
        "summary",
        "uv_index",
        "visibility",
        "wind_bearing",
        "wind_speed"
    ]

    writer = csv.DictWriter(weather_join_file, fieldnames=fieldnames)
    writer.writeheader()

    for line in report_reader:

        weather = get((line["geohash"], line["date"]), weather_cache, {})

        temperature_high = get("temperatureHigh", weather, None)
        temperature_low = get("temperatureLow", weather, None)
        
        line["temperature_high"] = temperature_high
        line["temperature_mid"] = (
            temperature_low + (temperature_high - temperature_low)/2
        ) if temperature_high and temperature_low else None
        line["temperature_low"] = temperature_low
        line["dew_point"] = get("dewPoint", weather, None)
        line["humidity"] = get("humidity", weather, None)
        line["cloud_cover"] = get("cloudCover", weather, None)
        line["moon_phase"] = get("moonPhase", weather, None)
        line["precip_intensity"] = get("precipIntensity", weather, None)
        line["precip_probability"] = get("precipProbability", weather, None)
        line["precip_type"] = get("precipType", weather, None)
        line["pressure"] = get("pressure", weather, None)
        line["summary"] = get("summary", weather, None)
        line["uv_index"] = get("uvIndex", weather, None)
        line["visibility"] = get("visibility", weather, None)
        line["wind_bearing"] = get("windBearing", weather, None)
        line["wind_speed"] = get("windSpeed", weather, None)

        writer.writerow(line)

if __name__ == "__main__":
    main()