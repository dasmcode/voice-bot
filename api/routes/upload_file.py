from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from api.core.request_models import GCSPath
from api.core.logging_config import get_logger
from api.core.models import VoiceFile
from api.core.db import get_db
from sqlalchemy.orm import Session
from api.core.redis_client import redis_manager
from api.core.queue import get_queue
from api.workers.process_file import process_file

router = APIRouter()
logger = get_logger(__name__)
@router.post("/submit")
def submit_gcs_path(gcs_path : GCSPath, db:Session = Depends(get_db)):
    try:
        gcs_path = gcs_path.gcs_path
        logger.info(f"Received file path: {gcs_path}")
        file_name = gcs_path.split("/")[-1]
        file = VoiceFile(file_name=file_name,upload_path=gcs_path)
        db.add(file)
        db.commit()
        db.refresh(file)
        transaction_id = str(file.transaction_id)
        queue = get_queue(redis_manager.sync_client)
        queue.enqueue(process_file, transaction_id, job_id=transaction_id, job_timeout=-1)
        return JSONResponse(
            content={
                "transaction_id": transaction_id,
                "file_path": gcs_path,
                "status": "queued"
            },
            status_code=200
        )
    except Exception as e:
        error =f"Error in submit gcs path: {e}"
        logger.error(error)
        return HTTPException(status_code=500, detail=error)