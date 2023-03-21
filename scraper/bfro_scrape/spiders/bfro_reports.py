import scrapy
from datetime import datetime


class BfroReportSpider(scrapy.Spider):
    name = "bfro_reports"

    start_urls = ["http://www.bfro.net/GDB/"]

    def parse(self, response):
        # Grab the state report pages from the main GDB page.
        state_pages = response.css("table.countytbl td.cs a")
        if self.test_run.lower() == "true":
            state_pages = state_pages[:1]
        for s in state_pages:
            if s is not None:
                yield response.follow(s, self.parse_state_page)

    def parse_state_page(self, response):
        # This grabs all of the county reports.
        county_pages = response.css("table.countytbl td.cs a")
        if self.test_run.lower() == "true":
            county_pages = county_pages[1:]
        for c in county_pages:
            if c is not None:
                yield response.follow(c, self.parse_county_page)

    def parse_county_page(self, response):
        for c in response.css("span.reportcaption a"):
            if c is not None:
                yield response.follow(c, self.parse_report)

    def parse_report(self, response):
        # Get the report number.
        report_number = response.css("span.reportheader::text").re(
            r"Report # (\d+)"
        )
        # Get the report classification.
        report_class = response.css("span.reportclassification::text").re(
            r"\((.*)\)"
        )

        # Now we need to get each field. For that we're going to use
        # XPath selectors.
        raw_keys = response.xpath("//p/span[@class='field']/text()").extract()
        keys = [k.replace(":", "").replace(" ", "_") for k in raw_keys]

        # Now if scrapy had XPath 2.0 this would be pretty simple. Unfortunately
        # it doesn't so we need to use a mixture of Python and XPath. This
        # XPath query grabs all "p" elements containing a 'span.field' with
        # text matching the key.
        value_query = (
            "//p[span[@class = 'field' and contains(text(), '{}')]]/text()"
        )

        # This is almost right: we need to grab text out of a couple of 'a'
        # tags. The " ".join( ... ) business is because some of the value
        # queries return multiple nodes thanks to some <BR> tags. This query
        # joins all of the text matching each field key into a single string.
        values = [
            " ".join(
                [
                    s.strip()
                    for s in response.xpath(value_query.format(k)).extract()
                ]
            )
            for k in raw_keys
        ]

        data = dict(zip(keys, values))

        # Add the report number and class.
        data["REPORT_NUMBER"] = (
            report_number[0] if len(report_number) > 0 else None
        )
        data["REPORT_CLASS"] = (
            report_class[0] if len(report_class) > 0 else None
        )

        # Add the datetime of the extraction.
        data["PULLED_DATETIME"] = datetime.today().isoformat(
            timespec="seconds"
        )

        # The empty keys have their text hiding out in some 'a' tags. This
        # fetches them.
        empty_keys = [k for k in keys if len(data[k]) == 0]

        for k in empty_keys:
            data[k] = response.xpath(
                "//p[span[@class='field' and contains(text(), '{}')]]/a/text()".format(
                    k
                )
            ).extract_first()

        yield data
