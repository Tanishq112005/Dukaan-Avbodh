import asyncio
import json
import os
from motor.motor_asyncio import AsyncIOMotorClient
from config.redis import redisClient
from .base import BaseWorker

class MongoDbWorker(BaseWorker):
    
    @classmethod
    async def _async_save_state_to_mongodb(cls, data):
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
            
            # 2. Get the MongoDB collection using a LOCAL client
            uri = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
            local_client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
            
            db = local_client["dukaan_db"]
            collection = db["agent_states"]
            
            # 3. Upsert the state based on thread_id
            result = await collection.update_one(
                {"thread_id": thread_id}, 
                {"$set": state}, 
                upsert=True
            )
            print(f"[MongoDbTask] Data for thread {thread_id} saved to MongoDB successfully.")
            
            # 4. Close the local client to free up connections
            local_client.close()
            
        except Exception as e:
            print(f"[MongoDbTask] Error saving data to MongoDB: {e}")
            raise e

    @classmethod
    def run(cls, data: dict):
        """
        Synchronous wrapper for RQ worker to call.
        """
        print(f"Starting MongoDB save task for thread: {data.get('thread_id')}")
        asyncio.run(cls._async_save_state_to_mongodb(data))
