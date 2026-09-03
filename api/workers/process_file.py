from api.core.logging_config import get_logger
from api.core.db import SessionLocal
from api.core.models import VoiceFile, FileState
import time

def process_file(transaction_id: str):
    try:
        logger = get_logger(__name__, transaction_id)
        db = SessionLocal()
        file = (
            db.query(VoiceFile).filter(VoiceFile.transaction_id == transaction_id).first()
        )
        logger.info(f"File received with transaction id: {transaction_id}")
        logger.info(f"Changing file state to processing")
        file.status = FileState.processing
        db.commit()
        db.refresh(file)
        time.sleep(10)
        logger.info(f"Completed processing file, changing state to completed")
        file.status = FileState.completed
        db.commit()
    except Exception as e:
        logger.error(f"Error in process file worker: {e}")
        db.rollback()
    finally:
        db.close()
