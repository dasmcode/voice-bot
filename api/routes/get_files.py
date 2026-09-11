from fastapi import Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from sqlalchemy.orm import Session

from api.core.db import get_db
from api.core.logging_config import get_logger
from api.core.models import VoiceFile

router = APIRouter()
logger = get_logger(__name__)


@router.get("/files")
async def get_files(db: Session = Depends(get_db)): # noqa: B008
    """Route to fetch all files currently in db"""
    logger.info("Get all files")
    try:
        files = db.query(VoiceFile).all()
        return JSONResponse(
            content=[
                {
                    "transaction_id": str(file.transaction_id),
                    "file_name": file.file_name,
                    "status": file.status.value,
                    "created_at": str(file.created_at),
                    "processed_at": str(file.processed_at),
                    "upload_path": file.upload_path,
                    "processed_path": file.processed_path,
                }
                for file in files
            ],
            status_code=200,
        )
    except Exception as e:
        logger.exception(f"Error while fetching files: {e}") # noqa: TRY401
        raise HTTPException(status_code=500, detail=str(e))
