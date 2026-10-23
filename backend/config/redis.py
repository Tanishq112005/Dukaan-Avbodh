import redis
import os


class RedisClient:

    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL") or "redis://localhost:6379"
        self.redis_client = None

    def get_redis_client(self):

        if self.redis_client != None:
            return self.redis_client

        self.redis_client = redis.Redis.from_url(self.redis_url)
        return self.redis_client


redisClient = RedisClient()
