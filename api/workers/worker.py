import asyncio

from rq import Worker

from api.core.logging_config import get_logger, setup_logging
from api.core.queue import get_queue
from api.core.redis_client import redis_manager


async def main():
    setup_logging()
    logger = get_logger(__name__)
    redis_manager.connect_sync()
    await redis_manager.connect_async()

    try:
        queue = get_queue(redis_manager.sync_client)
        worker = Worker([queue], connection=redis_manager.sync_client)
        logger.info("Worker starting...")
        worker.work()
    except Exception as e:
        logger.error(f"Worker encountered an error: {e}")
    finally:
        logger.info("Worker shutting down, closing Redis connection...")
        await redis_manager.disconnect_all()


if __name__ == "__main__":
    asyncio.run(main())
