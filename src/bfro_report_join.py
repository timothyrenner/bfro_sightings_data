import pandas as pd
import numpy as np
import click
import json

from toolz import pluck

@click.command()
@click.argument("report_locations_file", type=click.File("r"))
@click.argument("report_file", type=click.File("r"))
@click.argument("report_join_file", type=click.File("w"))
def main(report_locations_file, report_file, report_join_file):
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
        valid_latitudes & valid_longitudes & valid_times,
        :
    ]

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
            'classification_report_location'
        ],
        axis=1,
        inplace=True
    )

    reports_joined.to_csv(report_join_file, index=False)

if __name__ == "__main__":
    main()