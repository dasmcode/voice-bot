from rq import Queue
from redis import Redis
import os

REDIS_QUEUE = os.getenv("REDIS_QUEUE")


def get_queue(redis_client: Redis):
    try:
        return Queue(name=REDIS_QUEUE, connection=redis_client)
    except Exception as e:
        print(f"Error in redis connection: {e}")
