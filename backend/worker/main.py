import sys
import os
import threading
from redis.exceptions import ConnectionError as RedisConnectionError

# Add the backend root directory to sys.path before internal imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from task_queue.connection import QueueConsumerManager
from config.redis import redisClient
from worker.event_consumer import event_consumer


if __name__ == "__main__":
    print("=" * 60)
    print("Dukaan Unified Background Worker")
    print("=" * 60)

    try:
        r_client = redisClient.get_redis_client()
        r_client.ping()
        print("[UnifiedWorker] Successfully connected to Redis.")
    except RedisConnectionError as redis_err:
        print(f"[UnifiedWorker] ERROR: Redis is offline or unreachable: {redis_err}")
        print("[UnifiedWorker] To run the background workers, please start Redis:")
        print("  - Via Docker: docker run -d -p 6379:6379 --name dukaan-redis redis:alpine")
        print("  - Or update REDIS_URL in your backend/.env to a cloud Redis instance (e.g., Upstash / Redis Cloud)")
        sys.exit(1)

    # Start the 30-minute periodic ProbabilityOfShowingItems consumer in a background thread
    print("[Periodic Worker] Starting 30-minute event consumer for ProbabilityOfShowingItems...")
    event_thread = threading.Thread(
        target=event_consumer.start_periodic_loop,
        kwargs={"interval_seconds": 1800, "max_items": 100},
        daemon=True,
    )
    event_thread.start()
    print("[Periodic Worker] 30-minute event consumer loop running in background.")

    # Listen to RQ queues
    queues = ["state", "summarizer", "probability_queue"]
    print(f"Initializing Queue Consumer for {queues}...")
    consumer = QueueConsumerManager(
        redis_client=redisClient.get_redis_client(),
        queue_name=queues,
    )

    # This blocks and listens for tasks arriving in Redis
    consumer.start()
