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
However, there's a shell script that will run it all for you.

```sh
# In project root.
./run-pipeline-local.sh False
```

To run a test run, use

```sh
./run-pipeline-local.sh True
```

## Deployment and Orchestration

There's a Dockerfile and docker make targets (set to push to a local registry).
If you want to run in a container you should wrap the `run-pipeline-local.sh` shell script into one that will pull down / push updated data before the container tears down, or execute with a bind mount or volume mount on the local project root.

## Data Dictionary

Is in DBT!
Including the sources.

`pipeline/bfro_mini_warehouse/models/sources/local_files.yml` for the local sources, and `pipeline/bfro_mini_warehouse/models/docs` for the others.
You can cd into the `pipeline/bfro_mini_warehouse` directory and build the docs the usual DBT way.