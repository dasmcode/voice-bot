import os

from redis import Redis
from rq import Queue

REDIS_QUEUE = os.getenv("REDIS_QUEUE", "")


def get_queue(redis_client: Redis | None)->Queue:
    try:
        return Queue(name=REDIS_QUEUE, connection=redis_client)
    except Exception as e:
        print(f"Error in redis connection: {e}")
