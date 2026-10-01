from agents.user.state import AgentState
from redis import Redis
from .connection import QueueProducerManager
from ..worker.chat_summarizer import ChatSummarizerWorker
from ..worker.mongodb import MongoDbWorker
from config.redis import redisClient


### function for saving the data in the async
class SendDataToQueue: 
    
    def __init__(self , redis_client : Redis):
        self.redis_client = redis_client 
        self.state_saving_queue_name = "state" 
        self.summarizer_queue_name = "summarizer"
        self.summarizer_queue = QueueProducerManager(redis_client=self.redis_client , queue_name=self.summarizer_queue_name)
        self.state_queue = QueueProducerManager(redis_client=self.redis_client , queue_name=self.state_saving_queue_name)
    
    
    
    async def sendData(self , state: AgentState): 
        message = state["messages"]
        thread_id = state["thread_id"]
        user_id = state["user_id"]
        last_seq = state["last_seq"]
        conversation_summary = state["conversation_summary"]
        
       
        
        data = {
            "thread_id" : thread_id , 
            "last_seq"  : last_seq
        }
        
        
        ## name of the worker function 
        self.summarizer_queue.push(ChatSummarizerWorker.run , data)
        self.state_queue.push(MongoDbWorker.run , data)
 
 
        
## add the redis client         
sendingResult = SendDataToQueue(redis_client=redisClient.get_redis_client())            
           
    
    