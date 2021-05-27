ROOT=$(shell pwd)

create_environment:
	conda env create -f environment.yaml
	. activate bfro_sightings_data; \
	pip install -e git+https://github.com/timothyrenner/slamdring#egg=slamdring

destroy_environment:
	. activate bfro_sightings_data; pip uninstall slamdring
	conda remove --name bfro_sightings_data --all
	rm -rf src/

data/raw/doc.kml:
	wget http://www.bfro.net/app/AllReportsKMZ.aspx
	mv AllReportsKMZ.aspx data/raw/

	unzip data/raw/AllReportsKMZ.aspx -d data/raw

data/raw/bfro_report_locations.csv: data/raw/doc.kml
	python bfro/bfro_locations.py \
		   data/raw/doc.kml \
		   data/raw/bfro_report_locations.csv

data/raw/bfro_reports.json:
	mv $(ROOT)/data/raw/bfro_reports.json $(ROOT)/data/raw/bfro_reports_orig.json
	cd bfro/bfro_scrape;\
	scrapy crawl bfro_reports \
		   --output $(ROOT)/data/raw/bfro_reports.json \
		   --output-format jsonlines
	cd $(ROOT)
	
	# Union the old reports with the new reports.
	python bfro/bfro_union_reports.py \
		data/raw/bfro_reports_orig.json \
		data/raw/bfro_reports.json \
		data/raw/bfro_reports_merged.json
	
	# Move the unioned file to the main file, delete the interim orig file.
	mv data/raw/bfro_reports_merged.json data/raw/bfro_reports.json
	rm data/raw/bfro_reports_orig.json

data/interim/bfro_reports_geocoded.csv: data/raw/bfro_reports.json data/raw/bfro_report_locations.csv
	python bfro/bfro_report_join.py \
		data/raw/bfro_report_locations.csv \
		data/raw/bfro_reports.json \
		data/interim/bfro_reports_geocoded.csv

data/cache/weather_cache.csv: data/interim/bfro_reports_geocoded.csv
	python bfro/bfro_report_weather.py \
		data/interim/bfro_reports_geocoded.csv \
		--cache data/cache/weather_cache.csv | \
	slamdring --num-tasks 10 >> data/cache/weather_cache.csv

data/processed/bfro_reports_geocoded.csv: data/interim/bfro_reports_geocoded.csv data/cache/weather_cache.csv
	python bfro/bfro_weather_join.py \
		data/interim/bfro_reports_geocoded.csv \
		data/cache/weather_cache.csv \
		data/processed/bfro_reports_geocoded.csv

clean:
	rm -rf data/raw/*.aspx
	rm -rf data/raw/*.kml
	rm -rf data/raw/*.json
	rm -rf data/raw/*.csv
	rm -rf data/interim/*.csv
	rm -rf data/processed/*.csv