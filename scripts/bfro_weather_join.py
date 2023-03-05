import click
import json
import csv

from toolz import get, get_in


@click.command()
@click.argument("report_file", type=click.File("r"))
@click.argument("weather_file", type=click.File("r"))
@click.argument("weather_join_file", type=click.File("w"))
def main(report_file, weather_file, weather_join_file):
    weather_reader = csv.reader(weather_file)

    # Load the weather into a dictionary.
    weather_cache = {
        # Extract the dict with the weather information.
        (r[0], r[1]): get_in(["days", 0], json.loads(r[-1]), {})
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
        "conditions",
        "uv_index",
        "visibility",
        "wind_bearing",
        "wind_speed",
    ]

    writer = csv.DictWriter(weather_join_file, fieldnames=fieldnames)
    writer.writeheader()

    for line in report_reader:
        weather = get((line["geohash"], line["date"]), weather_cache, {})

        line["temperature_high"] = get("tempmax", weather, None)
        line["temperature_low"] = get("tempmin", weather, None)
        line["temperature_mid"] = get("temp", weather, None)
        line["dew_point"] = get("dew", weather, None)
        line["humidity"] = get("humidity", weather, None)
        line["cloud_cover"] = get("cloudcover", weather, None)
        line["moon_phase"] = get("moonphase", weather, None)
        line["precip_intensity"] = get("precip", weather, None)
        line["precip_probability"] = get("precipprob", weather, None)
        line["precip_type"] = get("preciptype", weather, None)
        line["pressure"] = get("pressure", weather, None)
        line["summary"] = get("description", weather, None)
        line["conditions"] = get("conditions", weather, None)
        line["uv_index"] = get("uvindex", weather, None)
        line["visibility"] = get("visibility", weather, None)
        line["wind_bearing"] = get("winddir", weather, None)
        line["wind_speed"] = get("windspeed", weather, None)

        writer.writerow(line)


if __name__ == "__main__":
    main()
