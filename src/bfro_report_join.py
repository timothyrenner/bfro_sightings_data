""" process_bfro_reports.py

    Joins the report locations to the full text reports and performs light 
    cleaning: removing invalid latitudes and longitudes, removing timestamps
    that occur in the future, and sets the timestamp granularity to days. Also
    adds a geohash column for the location for easy geospatial joins.
"""

import pandas as pd
import numpy as np
import click
import json
import pygeohash as pgh

from toolz import pluck

@click.command()
@click.argument("report_locations_file", type=click.File("r"))
@click.argument("report_file", type=click.File("r"))
@click.argument("report_join_file", type=click.File("w"))
@click.option("--precision", "-p", type=int, default=10)
def main(report_locations_file, report_file, report_join_file, precision):
    """ Joins the full text reports with the report locations.
    """

    report_locations = pd.read_csv(report_locations_file)

    # Valid latitudes and valid longitudes.
    valid_latitudes = \
        (report_locations.latitude >= -90.0) & \
        (report_locations.latitude <= 90.0)
    valid_longitudes = \
        (report_locations.longitude >= -180.0) & \
        (report_locations.longitude <= 180.0)
    valid_times = \
        pd.to_datetime(report_locations.timestamp) <= pd.datetime.now()

    report_locations = report_locations.loc[
        valid_latitudes & valid_longitudes & valid_times, :
    ]

    # Set the report timestamps to the correct period (date).
    report_locations.loc[:,'date'] = \
        pd.to_datetime(report_locations.timestamp).dt.to_period('d')

    # Make a generator that parses the json.
    report_dicts = filter(
        lambda x: x[0],
        pluck(
            [
                'REPORT_NUMBER', 
                'REPORT_CLASS', 
                'OBSERVED',
                'LOCATION_DETAILS', 
                'COUNTY', 
                'STATE'
            ],
            map(json.loads, report_file),
            default=None
        )
    )
    
    reports = pd.DataFrame(
        list(report_dicts),
        columns=[
            "number",
            "classification",
            "observed",
            "location_details",
            "county",
            "state"
        ]
    )
    reports.loc[:,'number'] = \
        reports.loc[:,'number'].astype(int)

    reports.index = reports.number
    report_locations.index = report_locations.number

    reports_joined = reports.join(
        report_locations, 
        how='left',
        lsuffix="_report",
        rsuffix="_report_location"
    )

    reports_joined.loc[:,'number'] = np.where(
        reports_joined.number_report.isnull(),
        reports_joined.number_report_location,
        reports_joined.number_report
    )

    reports_joined.loc[:,'classification'] = np.where(
        reports_joined.classification_report.isnull(),
        reports_joined.classification_report_location,
        reports_joined.classification_report
    )

    reports_joined.drop(
        [
            'number_report',
            'number_report_location',
            'classification_report',
            'classification_report_location',
            'timestamp'
        ],
        axis=1,
        inplace=True
    )

    # Add the geohash column.
    reports_joined.loc[:,'geohash'] = [
        pgh.encode(row.latitude, row.longitude, precision=precision)
        for _,row in reports_joined.iterrows()
    ]
    # A null location should result in a null geohash value.
    reports_joined.loc[:,'geohash'] = np.where(
        reports_joined.latitude.isnull(),
        np.NaN,
        reports_joined.geohash
    )

    reports_joined.to_csv(report_join_file, index=False)

if __name__ == "__main__":
    main()