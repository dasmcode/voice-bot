import os
import time
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from google.auth.credentials import AnonymousCredentials
from google.cloud import storage

from api.core.db import SessionLocal
from api.core.logging_config import get_logger
from api.core.models import FileState, VoiceFile
from api.services.llm_processor import llm_pipeline

PROJECT_ID = os.getenv("PROJECT_ID", "")
ENV = os.getenv("ENV", "")


def process_file(transaction_id: str, bucket_name: str, blob_name: str):
    try:
        logger = get_logger(__name__, transaction_id)
        db = SessionLocal()
        file = (
            db.query(VoiceFile)
            .filter(VoiceFile.transaction_id == transaction_id)
            .first()
        )
        logger.info(f"File received with transaction id: {transaction_id}")
        logger.info("Changing file state to processing")
        file.status = FileState.processing
        db.commit()
        db.refresh(file)
        if ENV == "local":
            client = storage.Client(
                credentials=AnonymousCredentials(),
                project="local-dev",
                client_options={"api_endpoint": os.getenv("STORAGE_EMULATOR_HOST", "")},
            )
        else:
            client = storage.Client(project=PROJECT_ID)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        with TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)

            local_file = tmp_dir / Path(blob_name).name

            logger.info(f"Downloading to: {local_file}")
            blob.download_to_filename(local_file)

            if zipfile.is_zipfile(local_file):
                logger.info(f"File is a zip archive : {local_file}")

                extract_dir = tmp_dir / "extracted"
                extract_dir.mkdir()

                with zipfile.ZipFile(local_file, "r") as zip_ref:
                    zip_ref.extractall(extract_dir)

                for file_path in extract_dir.rglob("*"):
                    if file_path.is_file():
                        logger.info(f"Extracted file : {file_path}")
                        extension = file_path.suffix
                        if extension != ".wav":
                            logger.warning(f"File is not a .wav : {blob_name}")
                            continue
                        llm_pipeline(local_file)
            else:
                logger.info(
                    f"File is not a zip archive: {local_file};Proceeding with single file process..."
                )
                llm_pipeline(local_file)
        time.sleep(10)
        logger.info("Completed processing file, changing state to completed")
        file.status = FileState.completed
        db.commit()
    except Exception as e:
        logger.error(f"Error in process file worker: {e}")
        db.rollback()
        logger.info("Rolling back changes and marking file as failed...")
        file.status = FileState.failed
        db.commit()
    finally:
        db.close()
