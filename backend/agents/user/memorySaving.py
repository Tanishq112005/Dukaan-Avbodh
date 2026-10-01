from agents.user.state import AgentState
from redis import Redis
from ...queue.connection import QueueProducerManager
from ...queue.schemas import DataInputForSavingForMessage
from agents.user.chatSummarizer import run_summary_task

### function for saving the data in the asyn
class SavingNode: 
    
    def __init__(self , redis_client : Redis):
        self.redis_client = redis_client 
        self.state_saving_queue_name = "state" 
        self.summarizer_queue_name = "summarizer"
        self.summarizer_queue = QueueProducerManager(redis_client=self.redis_client , queue_name=self.summarizer_queue_name)
        self.state_queue = QueueProducerManager(redis_client=redis_client , queue_name=self.state_saving_queue_name)
    
    async def sendData(self , state: AgentState): 
        message = state["messages"]
        thread_id = state["thread_id"]
        user_id = state["user_id"]
        last_seq = state["last_seq"]
        conversation_summary = state["conversation_summary"]
        
       
        
        data : DataInputForSavingForMessage = {
            "thread_id" : thread_id , 
            "last_seq"  : last_seq
        }
        
        
        ## name of the worker function 
        await self.summarizer_queue.push(run_summary_task , data)
        
        await self.summarizer_queue.push("" , data)  
 
 
        
## add the redis client         
savingNode = SavingNode(redis_client=)            
           
    
    