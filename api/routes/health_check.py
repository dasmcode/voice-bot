from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter

from api.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/health-check")
async def health_check():
    """Route to health_check application"""
    logger.info("Health Check")
    return JSONResponse(content="OK", status_code=200)
