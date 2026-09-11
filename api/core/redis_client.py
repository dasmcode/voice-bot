import os

import redis
import redis.asyncio as async_redis

from api.core.logging_config import get_logger

logger = get_logger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "")
REDIS_USER = os.getenv("REDIS_USER", "redis")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_SSL_CERT = os.getenv("REDIS_SSL_CERT", "")


class RedisManager:
    def __init__(self):
        self.sync_client = None
        self.async_client = None
        self.REDIS_URL = (
            f"rediss://{REDIS_USER}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"
        )

    def connect_sync(self):
        if not self.sync_client:
            self.sync_client = redis.from_url(
                self.REDIS_URL,
                ssl_ca_certs=REDIS_SSL_CERT,
                socket_keepalive=True,
                health_check_interval=30,
            )
        if self.sync_client.ping():
            logger.info("Redis sync client connected")
        else:
            logger.error("Redis sync client connection failed")

    async def connect_async(self):
        if not self.async_client:
            self.async_client = async_redis.from_url(
                self.REDIS_URL,
                ssl_ca_certs=REDIS_SSL_CERT,
                socket_keepalive=True,
                health_check_interval=30,
            )
        if await self.async_client.ping():
            logger.info("Redis async client connected")
        else:
            logger.error("Redis async client connection failed")

    async def disconnect_all(self):
        if self.async_client:
            await self.async_client.close()
        if self.sync_client:
            self.sync_client.close()
        logger.info("Redis clients disconnected")


redis_manager = RedisManager()
