import sys
import os
from ..queue.connection import QueueConsumerManager
from config.redis import redisClient

# Add the backend root to python path so it can be run directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


if __name__ == "__main__":
    # We pass a list of queues to listen to both state and summarizer
    queues = ["state", "summarizer"]
    
    print(f"Initializing Queue Consumer for {queues}...")
    consumer = QueueConsumerManager(redis_client=redisClient.get_redis_client(), queue_name=queues)
    
    # This blocks and listens for tasks arriving in Redis
    consumer.start()
