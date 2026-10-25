import os
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from rq import Queue, Worker, SimpleWorker


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
        worker_function : function reference
        *args, **kwargs : arguments to be passed directly to worker_function
        job_options     : RQ settings (job_timeout, retry, result_ttl, ...)
        """
        options = dict(job_options or {})
        try:
            job = self.queue.enqueue(
                worker_function,
                *args,
                **options,
                **kwargs,
            )
            print(f"Task assigned! Job ID {job.id} added to {self.queue_name}")
            return job.id
        except RedisConnectionError as r_err:
            print(f"[QueueProducerManager] Warning: Cannot enqueue task to {self.queue_name} (Redis unreachable): {r_err}")
            return None


### for the class for creating the consumer or worker
### parameters
### for initilization -> redis_client , queue_name
### for start -> no parameters only , run it
class QueueConsumerManager:
    def __init__(self, redis_client: Redis, queue_name: str | list):
        self.redis_client = redis_client
        self.queues = [queue_name] if isinstance(queue_name, str) else queue_name

    def start(self):
        # On Windows (nt) or environments without os.fork, RQ requires SimpleWorker
        is_windows = os.name == "nt" or not hasattr(os, "fork")
        worker_cls = SimpleWorker if is_windows else Worker

        # Check Redis connectivity first with friendly message
        try:
            self.redis_client.ping()
        except RedisConnectionError as r_err:
            print(f"[QueueConsumerManager] ERROR: Redis is offline or unreachable: {r_err}")
            print("[QueueConsumerManager] To run the background workers, please start Redis:")
            print("  - Via Docker: docker run -d -p 6379:6379 --name dukaan-redis redis:alpine")
            print("  - Or update REDIS_URL in your backend/.env to a cloud Redis instance (e.g., Upstash / Redis Cloud)")
            return

        print(f"Starting RQ {worker_cls.__name__} on queues: {self.queues}...")
        try:
            worker = worker_cls(self.queues, connection=self.redis_client)
            print(f"Worker is Started ({worker_cls.__name__})")
            worker.work()
        except Exception as err:
            print(f"[QueueConsumerManager] Worker stopped: {err}")
