from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.core.logging_config import setup_logging
# from api.core.db import init_db
from fastapi.middleware.cors import CORSMiddleware
from api.router import IncludeAPIRouter
from starlette.middleware.base import BaseHTTPMiddleware
# from api.core.redis_client import redis_manager
import logging

logger = logging.getLogger(__name__)
origins = ["https://igenaiuat.icicibankltd.com"]
origins = ["*"]
csp_policy = (
    "default-src 'self';"
    "img-src 'self' data:;"
    "script-src 'self' https://igenaiuat.icicibankltd.com;"
    "style-src 'self' https://igenaiuat.icicibankltd.com"
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging()
    # init_db()
    # redis_manager.connect_sync()
    # await redis_manager.connect_async()
    yield
    # await redis_manager.disconnect_all()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains; preload"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), camera=(), microphone=()"
        )
        response.headers["Content-Security-Policy"] = csp_policy
        return response


def init_application():
    _app = FastAPI(
        title="Voice Bot Summarization",
        description="Analyze currency transaction calls",
        version="1.0.0",
        lifespan=lifespan,
    )
    _app.include_router(IncludeAPIRouter())
    _app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )
    # _app.add_middleware(SecurityHeadersMiddleware)
    return _app


logger.info("Inside main file")
app = init_application()
