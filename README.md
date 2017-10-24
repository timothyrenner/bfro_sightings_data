# BFRO Sightings Data

The Bigfoot Field Researchers Organization ([BFRO](http://www.bfro.net/)) is an organization dedicated to studying the bigfoot / sasquatch mystery.
It has collected data on thousands of sightings throughout North America, many of which are geocoded.
This project contains code for downloading and extracting geocoded results, as well as full text reports on all data available on their site.

## Quickstart

To get started quickly, run the following commands:

```shell
# Optional, requires Anaconda python.
make create_environment
source activate bfro_sightings_data

# Install dependencies for python.
make requirements

# Download the data - takes about a half hour.
# Downloads geocoded reports and full reports.
make all
```

## Geocoded Reports

The geocoded reports are stored in a publicly available KML file that can be loaded into Google Earth (available directly [here](http://www.bfro.net/news/google_earth.asp), or downloadable through the Makefile).
This repository has a script for downloading and extracting the geocoded reports from that file.
To run it, execute the following Makefile target:

```shell
make data/bfro_report_locations.csv
```

This creates a file, `data/bfro_report_locations.csv`, with the following columns:

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

## Elasticsearch

I like Elasticsearch / Kibana for exploring data.
There's an optional script in the repo for it in `scripts/`.
It expects a local Elasticsearch instance running 5.x.

## Makefile Targets

Here's a reference of all targets in the Makefile.

| target                           | description                                                                  |
| -------------------------------- | ---------------------------------------------------------------------------- |
| `create_environment`             | Creates an Anaconda environment named `bfro_sightings_data`.                 |
| `requirements`                   | Installs the required dependencies.                                          |
| `freeze`                         | Freezes the environment into `requirements.txt`.                             |
| `data/doc.kml`                   | Downloads and extracts the KML file from the BFRO website.                   |
| `data/bfro_report_locations.csv` | Extracts the geocoded sighting reports from `data/doc.kml`.                  |
| `data/bfro_reports.json`         | Scrapes the full text reports from the BFRO website. Takes about 30 minutes. |
| `data/bfro_report_join.py`       | Joins the full text reports with the geocoded reports.                       |
| `all`                            | Executes `data/bfro_report_locations.csv` and `data/bfro_reports.json`.      |
| `clean`                          | Deletes all data.                                                            |