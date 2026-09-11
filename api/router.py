from fastapi.routing import APIRouter

from api.core.logging_config import get_logger

logger = get_logger(__name__)


class IncludeAPIRouter:
    def __new__(cls):
        api_prefix = "/genai-dev/voice-bot/api/v1"
        logger.info("Inside voice bot router")
        from api.routes.get_files import router as router_get_files
        from api.routes.health_check import router as router_health_check
        from api.routes.upload_file import router as router_upload_file

        router = APIRouter(prefix=api_prefix)
        router.include_router(router_health_check, tags=["Health Check"])
        router.include_router(router_upload_file, tags=["Upload file"])
        router.include_router(router_get_files, tags=["Get Files"])
        return router
