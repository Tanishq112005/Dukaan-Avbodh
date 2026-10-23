import sys
import os

# Add the backend root directory to sys.path before internal imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from task_queue.connection import QueueConsumerManager
from config.redis import redisClient


if __name__ == "__main__":
    # We pass a list of queues to listen to both state and summarizer
    queues = ["state", "summarizer"]
    
    print(f"Initializing Queue Consumer for {queues}...")
    consumer = QueueConsumerManager(redis_client=redisClient.get_redis_client(), queue_name=queues)
    
    # This blocks and listens for tasks arriving in Redis
    consumer.start()
