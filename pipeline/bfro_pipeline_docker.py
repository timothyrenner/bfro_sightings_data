import typer
from prefect import flow, get_run_logger
from prefect_gcp import GcpCredentials, GcsBucket
from bfro_pipeline import main as bfro_pipeline
from pathlib import Path


@flow(name="BFRO Pipeline (Docker)")
def main(data_dir: Path = "data", test_run: bool = False):
    logger = get_run_logger()
    logger.info("Fetching credentials.")
    gcp_credentials = GcpCredentials.load("prefect-gcs-rw")
    logger.info(f"Downloading data to {data_dir}.")
    bigfoot_bucket = GcsBucket(
        bucket="trenner-datasets",
        gcp_credentials=gcp_credentials,
    )
    bigfoot_bucket.download_folder_to_path("bigfoot", data_dir)
    logger.info("Executing pipeline.")
    bfro_success = bfro_pipeline(test_run=test_run)
    logger.info(f"Uploading updated contents of {data_dir} to GCS.")
    if bfro_success:
        bigfoot_bucket.upload_from_folder(data_dir, "bigfoot")


if __name__ == "__main__":
    typer.run(main)
