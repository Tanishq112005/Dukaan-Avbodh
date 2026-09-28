from langgraph.checkpoint.redis.aio import AsyncRedisSaver

import os 



class AgentCheckPointer: 
    
    def __init__(self): 
        self.checkpointerString = os.getenv("REDIS_MEMORY_CHECKPOINTER_URL", "mongodb://localhost:27017")
        self.redis_memory = None
    
    
    ### providing the redis as the memory checkpointer     
    ### Providing the same instance of the memory checkpointer 
    def getRedisCheckPointer(self):
        
        if(self.redis_memory != None):
            return self.redis_memory  
        
        self.redis_memory = AsyncRedisSaver.from_conn_string(redis_url=self.checkpointerString)
        return self.redis_memory 
    
    
    
    
    
    
    



checkPointer =  AgentCheckPointer() 


        
        
        
        
        