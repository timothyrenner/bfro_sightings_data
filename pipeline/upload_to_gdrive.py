import typer
from prefect import flow, task, get_run_logger
from pathlib import Path
from typing import Optional, List
from googleapiclient import discovery
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
import os
from dotenv import load_dotenv, find_dotenv


@task(name="Upload")
def upload_to_gdrive_task(
    google_drive_service,
    file: Path,
    destination_folder_id: str,
    owner_emails: List[str] = [],
):
    logger = get_run_logger()
    logger.info("Determining if file exists.")
    file_id: Optional[str] = None
    file_search_response = (
        google_drive_service.files()
        .list(
            q=f"name='{file.name}' and '{destination_folder_id}' in parents",
            fields="files(id, name)",
        )
        .execute()
    )

    if file_search_response.get("files", []):
        logger.info("File exists.")
        file_id = file_search_response["files"][0].get("id", None)

    metadata = {
        "name": file.name,
        "mimeType": "text/csv",
    }
    media = MediaFileUpload(file, mimetype="text/csv", resumable=True)
    logger.info("Uploading file.")
    if file_id:
        google_drive_service.files().update(
            fileId=file_id, body=metadata, media_body=media
        ).execute()
    else:
        metadata["parents"] = [destination_folder_id]
        file_response = (
            google_drive_service.files()
            .create(body=metadata, media_body=media, fields="id")
            .execute()
        )
        file_id = file_response["id"]
    logger.info("Setting file permissions.")
    for owner_email in owner_emails:
        try:
            permission = {
                "type": "user",
                "role": "reader",
                "emailAddress": owner_email,
            }
            google_drive_service.permissions().create(
                fileId=file_id,
                body=permission,
            ).execute()
        except Exception:
            logger.exception("Encountered error with sharing.")


@flow(name="Save to GDrive")
def upload_to_gdrive(
    file: Path,
    sa_credentials_location: Optional[str] = None,
    gdrive_folder_id: Optional[str] = None,
    owner_email: Optional[str] = None,
):
    logger = get_run_logger()
    if sa_credentials_location is None:
        logger.info(
            "Service account credentials location not passed, "
            "retrieving from env."
        )
        load_dotenv(find_dotenv())
        sa_credentials_location = os.getenv("SA_CREDENTIALS_LOCATION")
        if sa_credentials_location is None:
            raise ValueError("SA_CREDENTIALS_LOCATION not in .env or env.")

    if gdrive_folder_id is None:
        logger.info("GDrive folder ID not passed, retrieving from env.")
        load_dotenv(find_dotenv())
        gdrive_folder_id = os.getenv("GDRIVE_FOLDER_ID")
        if gdrive_folder_id is None:
            raise ValueError("GDRIVE_FOLDER_ID not in .env or env.")

    if owner_email is None:
        logger.info("Owner email not passed, retrieving from env.")
        load_dotenv(find_dotenv())
        owner_email = os.getenv("OWNER_EMAIL")
        if owner_email is None:
            raise ValueError("OWNER_EMAIL not in .env or env.")

    scopes = ["https://www.googleapis.com/auth/drive.file"]
    creds = service_account.Credentials.from_service_account_file(
        sa_credentials_location, scopes=scopes
    )
    logger.info("Authenticating to google cloud.")
    google_drive_service = discovery.build(
        "drive",
        "v3",
        credentials=creds,
    )

    logger.info("Performing upload task.")
    upload_to_gdrive_task(
        google_drive_service, file, gdrive_folder_id, [owner_email]
    )


if __name__ == "__main__":
    typer.run(upload_to_gdrive)
