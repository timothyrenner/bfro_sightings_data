import typer
from dotenv import load_dotenv, find_dotenv
from prefect.infrastructure.process import Process
from prefect.blocks.system import Secret
from prefect.filesystems import GCS
from loguru import logger
import os
import sys
import json


def main():
    logger.info("Loading .env file.")
    load_dotenv(find_dotenv())

    logger.info("Loading secrets from environment.")
    visual_crossing_key = os.getenv("VISUAL_CROSSING_KEY")
    if visual_crossing_key is None:
        logger.error("VISUAL_CROSSING_KEY not in environment or .env")
        sys.exit(1)

    bfro_gdrive_service_account_location = os.getenv(
        "BFRO_GDRIVE_SERVICE_ACCOUNT_LOCATION"
    )
    if bfro_gdrive_service_account_location is None:
        logger.error(
            "BFRO_GDRIVE_SERVICE_ACCOUNT_LOCATION not in environment or .env"
        )
        sys.exit(1)

    bfro_prod_editor_email = os.getenv("BFRO_PROD_EDITOR_EMAIL")
    if bfro_prod_editor_email is None:
        logger.error("BFRO_PROD_EDITOR_EMAIL not in environment or .env")
        sys.exit(1)

    bfro_prod_gdrive_folder_id = os.getenv("BFRO_PROD_GDRIVE_FOLDER_ID")
    if bfro_prod_gdrive_folder_id is None:
        logger.error("BFRO_PROD_GDRIVE_FOLDER_ID not in environment or .env")
        sys.exit(1)

    bfro_test_editor_email = os.getenv("BFRO_TEST_EDITOR_EMAIL")
    if bfro_test_editor_email is None:
        logger.error("BFRO_TEST_EDITOR_EMAIL not in environment or .env")
        sys.exit(1)

    bfro_test_gdrive_folder_id = os.getenv("BFRO_TEST_GDRIVE_FOLDER_ID")
    if bfro_test_gdrive_folder_id is None:
        logger.error("BFRO_TEST_GDRIVE_FOLDER_ID not in environment or .env")
        sys.exit(1)

    prefect_gcs_rw_service_account_location = os.getenv(
        "PREFECT_GCS_RW_SERVICE_ACCOUNT_LOCATION"
    )
    if prefect_gcs_rw_service_account_location is None:
        logger.error(
            "PREFECT_GCS_RW_SERVICE_ACCOUNT_LOCATION not in "
            "environment or .env"
        )
        sys.exit(1)

    logger.info("Creating visual-crossing-key secret block")
    Secret(value=visual_crossing_key).save(
        name="visual-crossing-key", overwrite=True
    )

    logger.info("Creating bfro-gdrive-service-account-location secret block.")
    Secret(value=bfro_gdrive_service_account_location).save(
        name="bfro-gdrive-service-account-location", overwrite=True
    )

    logger.info("Creating bfro-prod-editor-email secret block.")
    Secret(value=bfro_prod_editor_email).save(
        name="bfro-prod-editor-email", overwrite=True
    )

    logger.info("Creating bfro-prod-gdrive-folder-id secret block.")
    Secret(value=bfro_prod_gdrive_folder_id).save(
        name="bfro-prod-gdrive-folder-id", overwrite=True
    )

    logger.info("Creating bfro-test-editor-email secret block.")
    Secret(value=bfro_test_editor_email).save(
        name="bfro-test-editor-email", overwrite=True
    )

    logger.info("Creating bfro-test-gdrive-folder-id secret block.")
    Secret(value=bfro_test_gdrive_folder_id).save(
        name="bfro-test-gdrive-folder-id", overwrite=True
    )

    logger.info("Creating local process block.")
    Process().save(name="bfro-local", overwrite=True)

    logger.info("Creating storage block.")
    with open(prefect_gcs_rw_service_account_location, "r") as f:
        prefect_gcs_rw_creds = json.load(f)

    GCS(
        bucket_path="trenner-datasets/bfro-pipeline",
        service_account_info=prefect_gcs_rw_creds,
    ).save(name="bfro-pipeline-storage", overwrite=True)


if __name__ == "__main__":
    typer.run(main)
