import json
import logging
from typing import List, Optional, Dict, Any
from redis import Redis

from config.redis import redisClient
from task_queue.connection import QueueProducerManager

logger = logging.getLogger(__name__)

EVENT_QUEUE_KEY = "queue:user_events"


class EventQueue:
    """
    Queue system for buffering user events (viewed, add_to_cart, purchased,
    remove_from_cart) before processing by background workers.
    """

    def __init__(
        self,
        redis_client: Optional[Redis] = None,
        queue_key: str = EVENT_QUEUE_KEY,
    ):
        self._redis = redis_client
        self.queue_key = queue_key

    @property
    def redis(self) -> Redis:
        if self._redis is None:
            self._redis = redisClient.get_redis_client()
        return self._redis

    def push(self, event_data: dict) -> int:
        """
        Pushes a single event into the queue.
        Returns the new length of the queue.
        """
        try:
            payload = json.dumps(event_data)
            new_len = self.redis.rpush(self.queue_key, payload)
            logger.info("Event pushed to %s (queue length: %d)", self.queue_key, new_len)
            return new_len
        except Exception:
            logger.exception("Failed to push event into queue %s", self.queue_key)
            raise

    def pop_batch(self, max_items: int = 100) -> List[dict]:
        """
        Atomically pops up to `max_items` (maximum 100) events from the queue.
        """
        try:
            queue_len = self.redis.llen(self.queue_key)
            if queue_len == 0:
                return []

            count = min(max_items, queue_len)
            pipe = self.redis.pipeline()
            for _ in range(count):
                pipe.lpop(self.queue_key)
            raw_items = pipe.execute()

            events = []
            for item in raw_items:
                if item:
                    if isinstance(item, bytes):
                        item = item.decode("utf-8")
                    events.append(json.loads(item))

            logger.info("Popped %d events from queue %s", len(events), self.queue_key)
            return events

        except Exception:
            logger.exception("Failed to pop batch from %s", self.queue_key)
            return []

    def length(self) -> int:
        """Returns the number of waiting events in the queue."""
        try:
            return self.redis.llen(self.queue_key)
        except Exception:
            return 0


# Shared singleton instance
event_queue = EventQueue()
