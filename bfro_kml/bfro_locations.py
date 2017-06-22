from lxml import etree
import re
import sys
from csv import DictWriter
import click

@click.command()
@click.argument("input_file", type=click.File('r'))
@click.argument("output_file", type=click.File('w'))
def main(input_file, output_file):
    # Read the data into something that can be parsed.
    bfro = etree.fromstring(input_file.read())

    # Grab the relevant info we need.
    report_titles = \
        [t.strip() for t in bfro.xpath("//Placemark/description/b/text()")]

    report_classifications = \
        bfro.xpath('//Placemark/description/a/text()')

    # Make sure the lengths match.
    if len(report_titles) != len(report_classifications):
        print("ERROR - len(titles): {}, len(classifications): {}".format(
            len(report_titles), len(report_classifications)))
        sys.exit(1)

    report_timestamps = \
        [ts.strip() 
         for ts in bfro.xpath("//Placemark[1]/TimeStamp/when/text()")]

    # Make sure the lengths match.
    if len(report_titles) != len(report_timestamps):
        print("ERROR - len(titles): {}, len(timestamps): {}".format(
            len(report_titles), len(report_timestamps)))
        sys.exit(1)

    report_latitudes = \
        bfro.xpath("//Placemark[1]/LookAt/latitude/text()")

    # Make sure the lengths match.
    if len(report_titles) != len(report_latitudes):
        print("ERROR - len(titles): {}, len(latitudes): {}".format(
            len(report_titles), len(report_latitudes)))
        sys.exit(1)

    report_longitudes = \
        bfro.xpath("//Placemark[1]/LookAt/longitude/text()")

    # Make sure the lengths match.
    if len(report_titles) != len(report_longitudes):
        print("ERROR - len(titles): {}, len(longitudes): {}".format(
            len(report_titles), len(report_longitudes)))
        sys.exit(1)

    # Now to extract the report numbers. This will be a join key against the 
    # scraped data.
    report_numbers = \
        [re.search(r"Report (\d+):", t).group(1) for t in report_titles]

    if len(report_titles) != len(report_numbers):
        print("ERROR - len(titles): {}, len(numbers): {}".format(
            len(report_titles), len(report_numbers)))
        sys.exit(1)

    # Now drop it into a CSV.
    fieldnames = [
        "number",
        "title",
        "classification",
        "timestamp",
        "latitude",
        "longitude"
    ]

    writer = DictWriter(output_file, fieldnames=fieldnames)
    writer.writeheader()
    for ii in range(len(report_titles)):
        writer.writerow({
            "number": report_numbers[ii],
                "title": report_titles[ii],
                "classification": report_classifications[ii],
                "timestamp": report_timestamps[ii],
                "latitude": report_latitudes[ii],
                "longitude": report_longitudes[ii]
            })

if __name__ == "__main__":
    main()