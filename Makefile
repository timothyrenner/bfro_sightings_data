ROOT=$(shell pwd)

create_environment:
	conda-env create --name bfro_sightings_data python=3.5

requirements:
	pip install -r requirements.txt

freeze:
	pip freeze > requirements.txt

data/doc.kml:
	wget http://www.bfro.net/app/AllReportsKMZ.aspx
	mv AllReportsKMZ.aspx data/

	unzip data/AllReportsKMZ.aspx -d data/

data/bfro_report_locations.csv: data/doc.kml
	python src/bfro_locations.py \
		   data/doc.kml \
		   data/bfro_report_locations.csv

data/bfro_reports.json:
	cd src/bfro_scrape;\
	scrapy crawl bfro_reports \
		   --output $(ROOT)/data/bfro_reports.json \
		   --output-format jsonlines

data/bfro_reports_geocoded.csv: data/bfro_reports.json data/bfro_report_locations.csv
	python src/bfro_report_join.py \
		data/bfro_report_locations.csv \
		data/bfro_reports.json \
		data/bfro_reports_geocoded.csv

clean:
	rm -rf data/*.aspx
	rm -rf data/*.kml
	rm -rf data/*.json
	rm -rf data/*.csv