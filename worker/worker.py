import os
import redis
from rq import Worker, Queue, Connection

listen = ["agentsentry"]
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

def main():
    conn = redis.from_url(redis_url)
    with Connection(conn):
        worker = Worker([Queue(n) for n in listen])
        worker.work(with_scheduler=False)

if __name__ == "__main__":
    main()