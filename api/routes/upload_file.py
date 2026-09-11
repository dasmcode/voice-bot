import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from google.auth.credentials import AnonymousCredentials
from google.cloud import storage
from rq import Queue
from sqlalchemy.orm import Session

from api.core.db import get_db
from api.core.logging_config import get_logger
from api.core.models import VoiceFile
from api.core.queue import get_queue
from api.core.redis_client import redis_manager
from api.core.request_models import GCSPath
from api.workers.process_file import process_file

router = APIRouter()
logger = get_logger(__name__)

ENV = os.getenv("ENV", "")
PROJECT_ID = os.getenv("PROJECT_ID", "")


def parse_gcs_path(gcs_path: str) -> tuple[str, str]:
    """
    Convert:
        gs://my-bucket/path/to/file.zip
        my-bucket/path/to/file.zip

    into:
        ("my-bucket", "path/to/file.zip")
    """
    gcs_path = gcs_path.strip()

    if gcs_path.startswith("gs://"):
        gcs_path = gcs_path.removeprefix("gs://")

    parts = gcs_path.split("/", 1)

    if len(parts) != 2:
        raise ValueError(
            f"Invalid GCS path: {gcs_path!r}. "
            "Expected 'gs://bucket/path' or 'bucket/path'."
        )

    bucket_name, blob_name = parts
    return bucket_name, blob_name


@router.post("/submit")
def submit_gcs_path(gcs_path: GCSPath, db: Session = Depends(get_db)):
    try:
        gcs_file = gcs_path.gcs_path
        logger.info(f"Received file path: {gcs_file}")
        if ENV == "local":
            client = storage.Client(
                credentials=AnonymousCredentials(),
                project="local-dev",
                client_options={"api_endpoint": os.getenv("STORAGE_EMULATOR_HOST", "")},
            )
        else:
            client = storage.Client(project=PROJECT_ID)
        bucket_name, blob_name = parse_gcs_path(gcs_path=gcs_file)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        if not blob.exists(client):
            return JSONResponse(
                content={
                    "error": "Specified file does not exist in Google Cloud Storage"
                },
                status_code=401,
            )
        logger.info("Found file in GCS")
        file_name = gcs_file.split("/")[-1]
        file = VoiceFile(file_name=file_name, upload_path=gcs_file)
        db.add(file)
        db.commit()
        db.refresh(file)
        transaction_id = str(file.transaction_id)
        queue: Queue = get_queue(redis_manager.sync_client)
        queue.enqueue(
            process_file,
            transaction_id,
            bucket_name,
            blob_name,
            job_id=transaction_id,
            job_timeout=-1,
        )
        return JSONResponse(
            content={
                "transaction_id": transaction_id,
                "file_path": gcs_file,
                "status": "queued",
            },
            status_code=200,
        )
    except Exception as e:
        error = f"Error in submit gcs path: {e}"
        logger.error(error)
        return HTTPException(status_code=500, detail=error)
