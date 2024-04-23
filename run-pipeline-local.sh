# Runs the pipeline end to end for development and ad-hoc runs.
# Not designed for deployments.
set -e
cd pipeline # working dir for the whole script.

############# PULL NEW REPORTS ###############
echo "Pulling new reports, test_run=$1 ."
cd scraper/bfro_scrape # working dir for the scraper
scrapy crawl bfro_reports \
    -a test_run=$1 \
    --overwrite-output new_reports.json:jsonlines
cd ../.. # should be back in pipeline/
# Combines new reports with existing reports, as some reports will drop off
# the BFRO website.
# Move from the scraper into the raw data directory.
cp scraper/bfro_scrape/new_reports.json data/raw/bfro_reports_new.json
# Combine the reports.
python scripts/combine_raw_reports.py \
    data/raw/bfro_reports.csv \
    data/raw/bfro_reports_new.json \
    data/raw/bfro_reports_combined.csv
# Set the combined reports as the new reports csv
cp data/raw/bfro_reports_combined.csv data/raw/bfro_reports.csv
# Copy the reports to the DBT source directory.
cp data/raw/bfro_reports.csv data/sources/bfro_reports.csv

############# PULL KML REPORTS ###############
echo "Pulling kml file and extracting geocoded reports."
wget http://www.bfro.net/app/AllReportsKMZ.aspx
mv AllReportsKMZ.aspx data/raw/geocoder/
unzip -o data/geocoder/AllReportsKMZ.aspx -d data/raw/geocoder/
# Extract the lat / lon / report id / etc from the kml file.
python scripts/extract_locations_from_kml.py \
    data/raw/geocoder/doc.kml \
    data/raw/geocoded_reports_new.csv
# Combine the newly extracted reports with any existing KML sourced reports,
# in case any are removed from the KML file.
python scripts/combine_geocoded_reports.py \
    data/raw/geocoded_reports.csv \
    data/raw/geocoded_reports_new.csv \
    data/raw/geocoded_reports_combined.csv
# The combined reports are now current.
cp data/raw/geocoded_reports_combined.csv data/raw/geocoded_reports.csv
# Copy to the source file for dbt.
cp data/raw/geocoded_reports.csv data/sources/geocoded_reports.csv

############# PULL WEATHER ###############
echo "Pulling weather."
python scripts/pull_weather.py \
    data/raw/weather/weather_cache.csv \
    data/raw/geocoder/geocoded_reports.csv
# Copy to the source file for dbt.
cp data/raw/weather_cache.csv data/sources/weather_cache.csv

############# RUN DBT ###############
echo "Building mini warehouse."
cd bfro_mini_warehouse
dbt build --vars '{"data_dir":"../data"}'
# Hop back into pipeline.
cd ..
# Hop back onto project root, we are done.
cd ..