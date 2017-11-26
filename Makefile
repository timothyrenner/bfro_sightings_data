ROOT=$(shell pwd)

create_environment:
	conda-env create --name bfro_sightings_data python=3.5

requirements:
	pip install -r requirements.txt

freeze:
	pip freeze > requirements.txt

data/raw/doc.kml:
	wget http://www.bfro.net/app/AllReportsKMZ.aspx
	mv AllReportsKMZ.aspx data/raw/

	unzip data/raw/AllReportsKMZ.aspx -d data/raw

data/raw/bfro_report_locations.csv: data/raw/doc.kml
	python bfro/bfro_locations.py \
		   data/raw/doc.kml \
		   data/raw/bfro_report_locations.csv

data/raw/bfro_reports.json:
	cd bfro/bfro_scrape;\
	scrapy crawl bfro_reports \
		   --output $(ROOT)/data/raw/bfro_reports.json \
		   --output-format jsonlines

data/interim/bfro_reports_geocoded.csv: data/raw/bfro_reports.json data/raw/bfro_report_locations.csv
	python bfro/bfro_report_join.py \
		data/raw/bfro_report_locations.csv \
		data/raw/bfro_reports.json \
		data/interim/bfro_reports_geocoded.csv

data/interim/weather_cache.csv: data/interim/bfro_reports_geocoded.csv
	python bfro/bfro_report_weather.py \
		data/interim/bfro_reports_geocoded.csv \
		--cache data/imterim/weather_cache.csv | \
	slamdring --num-tasks 10 >> data/interim/weather_cache.csv

clean:
	rm -rf data/raw/*.aspx
	rm -rf data/raw/*.kml
	rm -rf data/raw/*.json
	rm -rf data/raw/*.csv
	rm -rf data/interim/*.csv
	rm -rf data/processed/*.csv