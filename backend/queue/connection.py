from redis import Redis
from rq import Queue , Worker


### for the class for creating the producer  
### parameters 
### for initilization -> redis_client , queue_name 
### for push -> function (or the worker function name ) , import the worker and the thread_id 
class QueueProducerManager:
    def __init__(self, redis_client: Redis, queue_name: str):
        self.redis_client = redis_client
        self.queue_name = queue_name
        self.queue = Queue(name=queue_name, connection=self.redis_client)

    def push(self, worker_function, *args, job_options: dict | None = None, **kwargs):
        """
        worker_function : function ka reference (import kiya hua)
        *args, **kwargs : jo bhi function ko chahiye
        job_options     : RQ ki apni settings (job_timeout, retry, result_ttl, ...)
        """
        job = self.queue.enqueue(
            worker_function,
            args=args,          # tuple
            kwargs=kwargs,      # dict
            **(job_options or {}),
        )
        print(f"Task assigned! Job ID {job.id} added to {self.queue_name}")
        return job.id

### for the class for creating the consumer or worker 
### parameters 
### for initilization -> redis_client , queue_name 
### for start -> no parameters only , run it  
class QueueConsumerManager: 
    def __init__(self, redis_client: Redis, queue_name: str): 
        self.redis_client = redis_client 
        self.queue_name = queue_name 
    
    def start(self): 
        print(f"Starting RQ worker on queue: '{self.queue_name}'...")
        # The Worker connects to Redis and blocks forever, executing tasks as they arrive
        worker = Worker([self.queue_name], connection=self.redis_client)
        print("Worker is Started") 
        worker.work()         
        
        
    