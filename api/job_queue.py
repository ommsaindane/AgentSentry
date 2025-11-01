import os
import redis
from rq import Queue

def get_queue() -> Queue:
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    conn = redis.from_url(url)
    return Queue("agentsentry", connection=conn, default_timeout=60)
