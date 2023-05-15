import typer
from prefect import flow, get_run_logger
from prefect.blocks.system import Secret
from prefect_gcp import GcpCredentials, GcsBucket
from bfro_pipeline import main as bfro_pipeline
from upload_to_gdrive import upload_to_gdrive
from pathlib import Path


@flow(name="BFRO Pipeline (Docker)")
def main(data_dir: Path = Path("data"), test_run: bool = False):
    logger = get_run_logger()

    logger.info("Fetching credentials.")
    gcp_credentials = GcpCredentials.load("prefect-gcs-rw")

    logger.info("Fetching visual crossing key.")
    visual_crossing_block = Secret.load("visual-crossing-key")
    visual_crossing_key = visual_crossing_block.get()

    logger.info("Fetching service account location for GDrive upload.")
    sa_credentials_location = Secret.load(
        "bfro-gdrive-service-account-location"
    ).get()

    logger.info("Fetching GDrive folder ID for test.")
    bfro_test_gdrive_folder_id = Secret.load(
        "bfro-test-gdrive-folder-id"
    ).get()

    logger.info("Fetching editor email for test.")
    bfro_test_editor_email = Secret.load("bfro-test-editor-email").get()

    logger.info("Fetching GDrive folder ID for prod.")
    bfro_prod_gdrive_folder_id = Secret.load(
        "bfro-prod-gdrive-folder-id"
    ).get()

    logger.info("Fetching GDrive editor email for prod.")
    bfro_prod_editor_email = Secret.load("bfro-prod-editor-email").get()

    logger.info(f"Downloading data to {data_dir}.")
    bigfoot_bucket = GcsBucket(
        bucket="trenner-datasets",
        gcp_credentials=gcp_credentials,
    )
    bigfoot_bucket.download_folder_to_path("bigfoot", data_dir)

    logger.info("Executing pipeline.")
    bfro_success = bfro_pipeline(
        test_run=test_run, visual_crossing_key=visual_crossing_key
    )

    logger.info("Uploading to gdrive (test).")
    upload_to_gdrive(
        data_dir / "processed" / "bfro_reports_geocoded.csv",
        sa_credentials_location=sa_credentials_location,
        gdrive_folder_id=bfro_test_gdrive_folder_id,
        owner_email=bfro_test_editor_email,
    )

    logger.info("Uploading to gdrive (prod).")
    upload_to_gdrive(
        data_dir / "processed" / "bfro_reports_geocoded.csv",
        sa_credentials_location=sa_credentials_location,
        gdrive_folder_id=bfro_prod_gdrive_folder_id,
        owner_email=bfro_prod_editor_email,
    )

    logger.info(f"Uploading updated contents of {data_dir} to GCS.")
    if bfro_success:
        bigfoot_bucket.upload_from_folder(data_dir, "bigfoot")


if __name__ == "__main__":
    typer.run(main)
