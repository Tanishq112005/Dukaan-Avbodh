import asyncio
import json
from config.mogodbconfig import nosql_client
from config.redis import redisClient
from connection import QueueConsumerManager
class QueueTasks:
    
    @staticmethod
    async def async_save_state_to_mongodb(data):
        """
        Async function to save state data to MongoDB.
        """
        try:
            thread_id = data.get("thread_id")
            
            # 1. Fetch the latest state from Redis
            redis_client = redisClient.get_redis_client()
            state_key = f"agent_state:{thread_id}"
            state_data = redis_client.get(state_key)
            
            if not state_data:
                print(f"[MongoDbTask] No state found in Redis for thread {thread_id}")
                return
                
            state = json.loads(state_data)
            state["thread_id"] = thread_id  # ensure thread_id is in the document
            
            # 2. Get the MongoDB collection
            db_name = "dukaan_db"
            collection_name = "agent_states"
            collection = nosql_client.get_client() 
            
            # 3. Upsert the state based on thread_id
            result = await collection.update_one(
                {"thread_id": thread_id}, 
                {"$set": state}, 
                upsert=True
            )
            print(f"[MongoDbTask] Data for thread {thread_id} saved to MongoDB successfully.")
            
        except Exception as e:
            print(f"[MongoDbTask] Error saving data to MongoDB: {e}")
            raise e

    @staticmethod
    def run_mongodb_saving_task(data):
        """
        Synchronous wrapper for RQ worker to call.
        """
        print(f"Starting MongoDB save task for thread: {data.get('thread_id')}")
        asyncio.run(QueueTasks.async_save_state_to_mongodb(data))

    @staticmethod
    def run_summary_task(data):
        """
        Synchronous wrapper for RQ worker to run the summarizer task.
        """
        from agents.user.chatSummarizer import chat_summarizer
        print(f"Starting summary task for thread: {data.get('thread_id')}")
        return chat_summarizer.process_summary(data)

if __name__ == "__main__":
   
    
    # We now pass a list of queues to listen to both state and summarizer
    queues = ["state", "summarizer"]
    
    print(f"Initializing Queue Consumer for {queues}...")
    consumer = QueueConsumerManager(redis_client=redisClient.get_redis_client(), queue_name=queues)
    
    # This blocks and listens for tasks arriving in Redis
    consumer.start()
