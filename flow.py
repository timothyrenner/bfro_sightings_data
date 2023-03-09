from prefect import flow, task
from prefect_shell import ShellOperation


@task(name="Extract geocoded reports")
def extract_geocoded_reports(kml_file: str, reports_out: str) -> str:
    ShellOperation(
        commands=[
            "python scripts/extract_geocoded_reports.py "
            f"{kml_file} {reports_out}"
        ]
    ).run()
    return reports_out


@task(name="Combine geocoded reports")
def combine_geocoded_reports(
    orig_report_file: str, new_report_file: str, combined_report_file: str
) -> str:
    ShellOperation(
        commands=[
            "python scripts/combine_geocoded_reports.py "
            f"{orig_report_file} {new_report_file} {combined_report_file}"
        ]
    ).run()
    return combined_report_file


@task(name="Copy combined reports back to raw")
def copy_combined_reports(combined_report_file: str, orig_report_file: str):
    ShellOperation(
        commands=[f"cp {combined_report_file} {orig_report_file}"]
    ).run()


@flow
def pull_and_update_geocoded_results():
    pass  # TODO: Implement.


pull_and_update_geocoded_results()
