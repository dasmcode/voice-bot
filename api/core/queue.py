import os

from redis import Redis
from rq import Queue

REDIS_QUEUE = os.getenv("REDIS_QUEUE", "")


def get_queue(redis_client: Redis | None)->Queue:  # pyright: ignore[reportReturnType]
    try:
        return Queue(name=REDIS_QUEUE, connection=redis_client)
    except Exception as e:  # noqa: BLE001
        print(f"Error in redis connection: {e}")
