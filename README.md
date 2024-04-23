# BFRO Sightings Data

The Bigfoot Field Researchers Organization ([BFRO](http://www.bfro.net/)) is an organization dedicated to studying the bigfoot / sasquatch mystery.
It has collected data on thousands of sightings throughout North America, many of which are geocoded.
This project contains code for downloading and extracting geocoded results, as well as full text reports on all data available on their site.

## A quick update

This repo has undergone some significant changes recently.
These changes all support automating what I used to do manually once a year.
They include refactoring a lot of the customized python code I wrote 7+ years ago.
Over time I'll be adding more documentation, analysis examples, and maybe example apps with streamlit, datapane, or dash too.
This refactor is just the first step.

## Setup 

To get started, run the following commands to set up the environment.

```shell
conda env create -f environment.yaml
conda activate bfro-sightings-data
make dev-env
```

This creates a conda environment with all the dependencies.

The weather stuff is a tad problematic because it expects there to be a Visual Crossing API key.
They are free for up to a thousand calls a day (and we have more calls than that, so you'd need to stagger them to fully hydrate the cache).
To use it, add `VISUAL_CROSSING_KEY` to the environment or a local `.env` file.

For more information on the weather data, see the [Visual Crossing documentation](https://www.visualcrossing.com/resources/documentation/weather-api/timeline-weather-api/).

## Full Pipeline

The pipeline (including scraper, weather, and the DBT project), is in the `pipeline/` directory.
Everything assumes relative paths from that directory, rather than the project root (which is just for setup and deployment operations).

```
cd pipeline/
python bfro_pipeline.py
```

For a test run (which runs the scraper on a small set of pages, and pulls a small set of weather data), use `--test-run`.

```
python bfro_pipeline.py --test-run
```

Once the sources are in place (however you decide to run them), you can run dbt directly from within the `pipeline/bfro_mini_warehouse` directory, or use the script.

```
python bfro_pipeline.py --dbt-only
```

The pipeline command runs the source tests first, builds the csv files, then runs the rest of the data tests.

## Deployment and Orchestration

The pipelines are [Prefect](https://www.prefect.io/) flows, and they can be deployed but require some setup.
The `pipeline/bfro_pipeline_docker.py` file has the blocks you need (basically `prefect-gcs-rw` as GCP credentials, and `visual-crossing-key` as a Secret).
I assume if you're messing with deployments you probably know how that stuff works.
It's not _super_ hard to self host Prefect, but it's not super easy either.

Also worth noting - while the thing says `_docker` in the file name and pipeline name, I don't actually have the dockerized version working yet 😬 .

It will still deploy and run, as is, with a process infrastructure block on an agent within the conda env provided in this repo though.
When I get docker working, you'll be able to launch it with a docker container infrastructure block and no code change to the flow.

## Data Dictionary

Is in DBT!
Including the sources.

`pipeline/bfro_mini_warehouse/models/sources/local_files.yml` for the local sources, and `pipeline/bfro_mini_warehouse/models/docs` for the others.
You can cd into the `pipeline/bfro_mini_warehouse` directory and build the docs the usual DBT way.