import elasticsearch
import json
import click

from csv import DictReader
from toolz import pluck
from elasticsearch.helpers import streaming_bulk

bfro_index_name = 'bfro'
bfro_report_type_name = 'bfro_report'

bfro_index_body = {
    "mappings": {
        bfro_report_type_name: {
            "properties": {
                "observed": {
                    "type": "text"
                },
                "location_details": {
                    "type": "text"
                },
                "county": {
                    "type": "keyword"
                },
                "state": {
                    "type": "keyword"
                },
                "title": {
                    "type": "text"
                },
                "date": {
                    "type": "date",
                    "ignore_malformed": True
                },
                "latitude": {
                    "type": "float"
                },
                "longitude": {
                    "type": "float"
                },
                "number": {
                    "type": "integer"
                },
                "classification": {
                    "type": "keyword"
                },
                "location": {
                    "type": "geo_point"
                },
                "temperature_high": {
                    "type": "float"
                },
                "temperature_mid": {
                    "type": "float"
                },
                "temperature_low": {
                    "type": "float"
                },
                "dew_point": {
                    "type": "float"
                },
                "humidity": {
                    "type": "float"
                },
                "cloud_cover": {
                    "type": "float"
                },
                "moon_phase": {
                    "type": "float"
                },
                "precip_intensity": {
                    "type": "float"
                },
                "precip_probability": {
                    "type": "float"
                },
                "precip_type": {
                    "type": "keyword"
                },
                "pressure": {
                    "type": "float"
                },
                "summary": {
                    "type": "text"
                },
                "uv_index": {
                    "type": "integer"
                },
                "visibility": {
                    "type": "float"
                },
                "wind_bearing": {
                    "type": "float"
                },
                "wind_speed": {
                    "type": "float"
                }
            }
        }
    }
}

def bfro_bulk_action(doc):
    return {
        "_op_type": "index",
        "_index": bfro_index_name,
        "_type": bfro_report_type_name,
        "_id": doc["number"],
        "_source": {
            "location": {
                "lat": float(doc["latitude"]),
                "lon": float(doc["longitude"])
            } if doc["latitude"] and doc["longitude"] else None,
            **doc
        }
    }

@click.command()
@click.argument("report_file", type=click.File('r'))
def main(report_file):

    client = elasticsearch.Elasticsearch()
    index_client = elasticsearch.client.IndicesClient(client)

    # Drop the index if it already exists; it will be replaced. This is the
    # most efficient way to delete the data from an index according to the ES
    # documentation.
    if index_client.exists(bfro_index_name):
        index_client.delete(bfro_index_name)
    
    # Create the index again.
    index_client.create(
        bfro_index_name,
        bfro_index_body
    )

    reports = DictReader(report_file)

    # Zip the reports with the report numbers.
    report_actions = map(
        bfro_bulk_action,
        reports
    )

    for ok,resp in streaming_bulk(client, report_actions):
        if not ok:
            print(resp)

if __name__ == "__main__":
    main()