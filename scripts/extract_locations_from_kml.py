from lxml import etree
import re
import sys
from csv import DictWriter
import typer
from pathlib import Path
from loguru import logger


def main(kml_file: Path, geocoded_out: Path):
    # Read the data into something that can be parsed.
    logger.info(f"Reading and parsing {kml_file.name}")
    report_xml = etree.fromstring(kml_file.read_bytes())

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
        print(
            "ERROR - len(titles): {}, len(classifications): {}".format(
                len(report_titles), len(report_classifications)
            )
        )
        sys.exit(1)

    logger.info("Extracting report timestamps.")
    report_timestamps = [
        ts.strip()
        for ts in report_xml.xpath("//Placemark[1]/TimeStamp/when/text()")
    ]

    # Make sure the lengths match.
    logger.info("Validating report timestamp length.")
    if len(report_titles) != len(report_timestamps):
        print(
            "ERROR - len(titles): {}, len(timestamps): {}".format(
                len(report_titles), len(report_timestamps)
            )
        )
        sys.exit(1)

    logger.info("Extracting report latitudes.")
    report_latitudes = report_xml.xpath(
        "//Placemark[1]/LookAt/latitude/text()"
    )

    # Make sure the lengths match.
    logger.info("Validating report latitudes.")
    if len(report_titles) != len(report_latitudes):
        print(
            "ERROR - len(titles): {}, len(latitudes): {}".format(
                len(report_titles), len(report_latitudes)
            )
        )
        sys.exit(1)

    logger.info("Extracting report longitudes.")
    report_longitudes = report_xml.xpath(
        "//Placemark[1]/LookAt/longitude/text()"
    )

    # Make sure the lengths match.
    logger.info("Validting report longitudes.")
    if len(report_titles) != len(report_longitudes):
        print(
            "ERROR - len(titles): {}, len(longitudes): {}".format(
                len(report_titles), len(report_longitudes)
            )
        )
        sys.exit(1)

    # Now to extract the report numbers. This will be a join key against the
    # scraped data.
    logger.info("Extracting report numbers.")
    report_numbers = [
        re.search(r"Report (\d+):", t).group(1) for t in report_titles
    ]

    logger.info("Validating report numbers.")
    if len(report_titles) != len(report_numbers):
        print(
            "ERROR - len(titles): {}, len(numbers): {}".format(
                len(report_titles), len(report_numbers)
            )
        )
        sys.exit(1)

    # Now drop it into a CSV.
    fieldnames = [
        "number",
        "title",
        "classification",
        "timestamp",
        "latitude",
        "longitude",
    ]

    logger.info(f"Writing results to {geocoded_out.name}.")
    with open(geocoded_out, "w") as f:
        writer = DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for ii in range(len(report_titles)):
            writer.writerow(
                {
                    "number": report_numbers[ii],
                    "title": report_titles[ii],
                    "classification": report_classifications[ii],
                    "timestamp": report_timestamps[ii],
                    "latitude": report_latitudes[ii],
                    "longitude": report_longitudes[ii],
                }
            )


if __name__ == "__main__":
    typer.run(main)
