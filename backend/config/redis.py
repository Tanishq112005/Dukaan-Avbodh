import os
import redis
from dotenv import load_dotenv

load_dotenv()


class RedisClient:
    def __init__(self):
        load_dotenv()
        self.redis_url = os.getenv("REDIS_URL") or "redis://localhost:6379"
        self.redis_client = None

    def get_redis_client(self):
        if self.redis_client is not None:
            return self.redis_client

        url = os.getenv("REDIS_URL") or self.redis_url
        self.redis_url = url
        self.redis_client = redis.Redis.from_url(self.redis_url)
        return self.redis_client


redisClient = RedisClient()
