from lxml import etree
from lxml.etree import Element
import re
import typer
from pathlib import Path
from loguru import logger
import polars as pl
from datetime import date
import h3


def extract_geocoded_reports(report_xml: Element) -> pl.DataFrame:
    # Grab the relevant info we need.
    logger.info("Extracting report titles.")
    report_titles = [
        t.strip() for t in report_xml.xpath("//Placemark/description/b/text()")
    ]

    logger.info("Extracting report classifications.")
    report_classifications = report_xml.xpath(
        "//Placemark/description/a/text()"
    )

    # Make sure the lengths match.
    logger.info("Validating report classifications and titles.")
    if len(report_titles) != len(report_classifications):
        raise ValueError(
            "ERROR - len(titles): {}, len(classifications): {}".format(
                len(report_titles), len(report_classifications)
            )
        )

    logger.info("Extracting report timestamps.")
    report_timestamps = [
        ts.strip()
        for ts in report_xml.xpath("//Placemark[1]/TimeStamp/when/text()")
    ]

    # Make sure the lengths match.
    logger.info("Validating report timestamp length.")
    if len(report_titles) != len(report_timestamps):
        raise ValueError(
            "ERROR - len(titles): {}, len(timestamps): {}".format(
                len(report_titles), len(report_timestamps)
            )
        )

    logger.info("Extracting report latitudes.")
    report_latitudes = report_xml.xpath(
        "//Placemark[1]/LookAt/latitude/text()"
    )

    # Make sure the lengths match.
    logger.info("Validating report latitudes.")
    if len(report_titles) != len(report_latitudes):
        raise ValueError(
            "ERROR - len(titles): {}, len(latitudes): {}".format(
                len(report_titles), len(report_latitudes)
            )
        )

    logger.info("Extracting report longitudes.")
    report_longitudes = report_xml.xpath(
        "//Placemark[1]/LookAt/longitude/text()"
    )

    # Make sure the lengths match.
    logger.info("Validting report longitudes.")
    if len(report_titles) != len(report_longitudes):
        raise ValueError(
            "ERROR - len(titles): {}, len(longitudes): {}".format(
                len(report_titles), len(report_longitudes)
            )
        )

    # Now to extract the report numbers. This will be a join key against the
    # scraped data.
    logger.info("Extracting report numbers.")
    report_numbers = [
        re.search(r"Report (\d+):", t).group(1) for t in report_titles
    ]

    logger.info("Validating report numbers.")
    if len(report_titles) != len(report_numbers):
        raise ValueError(
            "ERROR - len(titles): {}, len(numbers): {}".format(
                len(report_titles), len(report_numbers)
            )
        )

    # Now consolidate into a data frame.
    return (
        pl.DataFrame(
            {
                "number": report_numbers,
                "title": report_titles,
                "classification": report_classifications,
                "timestamp": report_timestamps,
                "latitude": report_latitudes,
                "longitude": report_longitudes,
            }
        )
        .apply(
            lambda x: (
                x[0],  # number
                x[1],  # title
                x[2],  # classification
                x[3],  # timestamp
                float(x[4]),  # latitude
                float(x[5]),  # longitude
                h3.geo_to_h3(float(x[4]), float(x[5]), resolution=10),  # hexid
                f"{date.today():%Y-%m-%d}",  # extraction_date
            )
        )
        .rename(
            {
                "column_0": "number",
                "column_1": "title",
                "column_2": "classification",
                "column_3": "timestamp",
                "column_4": "latitude",
                "column_5": "longitude",
                "column_6": "hexid",
                "column_7": "extraction_date",
            }
        )
    )


def main(kml_file: Path, geocoded_out: Path):
    # Read the data into something that can be parsed.
    logger.info(f"Reading and parsing {kml_file.name}")
    report_xml = etree.fromstring(kml_file.read_bytes())

    geocoded_reports = extract_geocoded_reports(report_xml)

    # Now drop it into a CSV.
    logger.info(f"Writing results to {geocoded_out.name}.")
    geocoded_reports.write_csv(geocoded_out)
    logger.info("👣 all done 👣")


if __name__ == "__main__":
    typer.run(main)
