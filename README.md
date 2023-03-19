# BFRO Sightings Data

The Bigfoot Field Researchers Organization ([BFRO](http://www.bfro.net/)) is an organization dedicated to studying the bigfoot / sasquatch mystery.
It has collected data on thousands of sightings throughout North America, many of which are geocoded.
This project contains code for downloading and extracting geocoded results, as well as full text reports on all data available on their site.

## Quickstart

To get started quickly, run the following commands:

```shell
conda env create -f environment.yaml
conda activate bfro
dvc repro geocode-reports
```

This will get _most_ of the data, but not all of it - it runs all stages prior to the weather pull/merge.
The weather stuff is problematic because it expects there to be a Visual Crossing API key.
They are free for up to a thousand calls a day (and we have more calls than that, so you'd need to stagger them to fully hydrate the cache).
You can get the geocoded reports and json reports without that key.
## Geocoded Reports

The geocoded reports are stored in a publicly available KML file that can be loaded into Google Earth (available directly [here](http://www.bfro.net/news/google_earth.asp), or downloadable through the dvc command).
This repository has a script for downloading and extracting the geocoded reports from that file.
To run it, execute the following dvc targets:

```shell
dvc repro --single-item pull-kml
dvc repro --single-item extract-locations-from-kml
```

This creates a file, `data/raw/bfro_report_locations.csv`, with the following columns:

| column name      | description                                                                                    |
| ---------------- | ---------------------------------------------------------------------------------------------- |
| `number`         | The report number as an integer.                                                               |
| `title`          | The full title of the report.                                                                  |
| `classification` | The sighting classification for the report. More [here](http://www.bfro.net/GDB/classify.asp). |
| `timestamp`      | The time of the report in [ISO-8601](https://en.wikipedia.org/wiki/ISO_8601) format.           |
| `latitude`       | The latitude of the sighting.                                                                  |
| `longitude`      | The longitude of the sighting.                                                                 |

## Full Reports

The full reports have to be scraped from the site.
The scraper is built with the [Scrapy](https://scrapy.org/) framework.
It's intentionally throttled to avoid overloading the server.
As such it takes a little over 30 minutes to pull the data, which as of this writing is just under 5000 full text reports.

The reports are stored as line-delimited JSON objects with the following schema:

```javascript
{
    "ALSO_NOTICED": "Other interesting things the witness noticed.",
    "A_&_G_References": "Press references to the sighting.",
    "COUNTY": "The county of the sighting.",
    "DATE": "The actual day of the sighting, in no particular format.",
    "ENVIRONMENT": "A description of the environment for the sighting.",
    "LOCATION_DETAILS": "A detailed description of the location.",
    "MONTH": "The month of the sighting.",
    "NEAREST_ROAD": "A description of the nearest road to the sighting.",
    "NEAREST_TOWN": "A description of the nearest town.",
    "OBSERVED": "The contents of the report.",
    "OTHER_STORIES": "A description of other stories from the area.",
    "OTHER_WITNESSES": "A description of other witnesses present.",
    "REPORT_CLASS": "The report class (see description in geocoded values).",
    "REPORT_NUMBER": "The report number. Join key for the geocoded dataset.",
    "SEASON": "The season of the sighting.",
    "STATE": "The state or province of the sighting.",
    "TIME_AND_CONDITIONS": "The conditions and time of the sighting.",
    "YEAR": "The year of the sighting in no particular format."
}
```

Note that not all reports will have all of the fields, and it's possible more fields will be added for future reports.

## Geocoded Joined with Full Reports

This is a combined and cleaned dataset that joins the geocoded reports with information from the full report text.
It's built by joining the full text reports with the geocoded report titles.
Not all of the full text reports are geocoded - they have null values for the location.
This file is much cleaner and easier to work with, but is slightly opinionated.

| column             | description                                                                          |
| ------------------ | ------------------------------------------------------------------------------------ |
| `observed`         | The contents of the report.                                                          |
| `location_details` | A detailed description of the location.                                              |
| `county`           | The county of the sighting.                                                          |
| `state`            | The state or province of the sighting.                                               |
| `title`            | The full title of the report.                                                        |
| `date`             | The date of the report in [ISO-8601](https://en.wikipedia.org/wiki/ISO_8601) format. |
| `latitude`         | The latitude of the sighting.                                                        |
| `longitude`        | The longitude of the sighting.                                                       |
| `number`           | The report number.                                                                   |
| `classification`   | The report class (see description in geocoded values).                               |
| `geohash`          | The geohash of the sighting location.                                                |

## Weather

The weather data is [powered by Visual Crossing](https://www.visualcrossing.com/resources/blog/how-to-replace-the-dark-sky-api-using-the-visual-crossing-timeline-weather-api/), which is a still operating Dark Sky alternative.
You need an API key to get this dataset, and it does cost money, but not a lot.
As of this writing it's $1 per 10k requests.
The API key needs to be in the environment as `VISUAL_CROSSING_KEY`, or it can be in a `.env` file somewhere as well.

Since the times aren't recorded consistently in the dataset, all weather information is retrieved at the day level.
The weather data adds the following columns to the "full geocoded reports" table:

| column               | description                                                                                         |
| -------------------- | --------------------------------------------------------------------------------------------------- |
| `temperature_high`   | The high temperature.                                                                               |
| `temperature_mid`    | The midpoint between the high and low temperatures.                                                 |
| `temperature_low`    | The low temperature.                                                                                |
| `dew_point`          | The dew point.                                                                                      |
| `humidity`           | The relative humidity.                                                                              |
| `cloud_cover`        | The percentage of sky occluded by clouds.                                                           |
| `moon_phase`         | The fractional part of the lunation number. 0.5 is a full moon because I know what you're thinking. |
| `precip_intensity`   | The intensity of precipitation in inches per hour.                                                  |
| `precip_probability` | The probability of precipitation.                                                                   |
| `precip_type`        | The precipitation type.                                                                             |
| `pressure`           | The sea-level air pressure.                                                                         |
| `summary`            | A human readable text summary.                                                                      |
| `uv_index`           | The UV index.                                                                                       |
| `visibility`         | The average visibility in miles, capped at 10.                                                      |
| `wind_bearing`       | The direction the wind is coming from in degrees.                                                   |
| `wind_speed`         | The speed of the wind in miles per hour.                                                            |

For more information on the weather data, see the [Visual Crossing documentation](https://www.visualcrossing.com/resources/documentation/weather-api/timeline-weather-api/).

## Elasticsearch

I like Elasticsearch / Kibana for exploring data.
There's an optional script in the repo for it in `scripts/`.
It expects a local Elasticsearch instance running 5.x.