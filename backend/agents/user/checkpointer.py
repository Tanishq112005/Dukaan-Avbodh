from langgraph.checkpoint.redis.aio import AsyncRedisSaver
from langgraph.checkpoint.mongodb import MongoDBSaver
import asyncio
import os 
from pymongo import MongoClient




class AgentCheckPointer: 
    
    def __init__(self): 
        self.redisCheckpointerString = os.getenv("REDIS_MEMORY_CHECKPOINTER_URL", "mongodb://localhost:27017")
        self.mongo_uri = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.mongodb_memory = None 
        self.redis_memory = None
      
    
    ### providing the redis as the memory checkpointer     
    ### Providing the same instance of the memory checkpointer 
    def getRedisCheckPointer(self):
        
        if(self.redis_memory != None):
            return self.redis_memory  
        
        self.redis_memory = AsyncRedisSaver.from_conn_string(redis_url=self.redisCheckpointerString)
        return self.redis_memory 
    
    
    
    ### providing the mongodb as the memory checkpointer 
    ### providing the same instance of the memory checkpointer 
    def getMongoDBCheckPointer(self): 
        
        if(self.mongodb_memory != None):
            return self.mongodb_memory 
        
        sync_client =  MongoClient(self.mongo_uri)
        self.mongodb_memory = MongoDBSaver(sync_client)
        
        
        return self.mongodb_memory 
    
    
    
    
    
    
    



checkPointer =  AgentCheckPointer() 


        
        
        
        
        