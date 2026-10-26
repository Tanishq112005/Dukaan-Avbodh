import os
from pathlib import Path
import redis
from redis.retry import Retry
from redis.backoff import ExponentialBackoff
from dotenv import load_dotenv

# Ensure .env is loaded reliably whether executing from project root or backend directory
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


class RedisClient:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL") or "redis://localhost:6379"
        self.redis_client = None

    def get_redis_client(self):
        if self.redis_client is not None:
            return self.redis_client

        url = os.getenv("REDIS_URL") or self.redis_url
        self.redis_url = url
        self.redis_client = redis.Redis.from_url(
            self.redis_url,
            health_check_interval=30,
            socket_keepalive=True,
            retry_on_timeout=True,
            socket_connect_timeout=15,
            retry=Retry(ExponentialBackoff(cap=5, base=1), 3),
        )
        return self.redis_client


redisClient = RedisClient()
