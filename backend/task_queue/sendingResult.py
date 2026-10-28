import json
from typing import Any
from redis import Redis
from task_queue.connection import QueueProducerManager
from worker.chat_summarizer import ChatSummarizerWorker
from worker.mongodb import MongoDbWorker
from config.redis import redisClient


def _serialize_message(msg: Any) -> dict:
    if isinstance(msg, dict):
        return msg
    if hasattr(msg, "content"):
        return {
            "type": getattr(msg, "type", "message"),
            "role": getattr(msg, "type", "message"),
            "content": msg.content,
        }
    return {"type": "message", "content": str(msg)}


class SendDataToQueue:
    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client
        self.state_saving_queue_name = "state"
        self.summarizer_queue_name = "summarizer"
        self.summarizer_queue = QueueProducerManager(
            redis_client=self.redis_client, queue_name=self.summarizer_queue_name
        )
        self.state_queue = QueueProducerManager(
            redis_client=self.redis_client, queue_name=self.state_saving_queue_name
        )

    async def sendData(self, state: dict):
        thread_id = str(state.get("thread_id", ""))
        user_id = state.get("user_id")
        raw_messages = state.get("messages", [])

        if not thread_id:
            return

        state_key = f"agent_state:{thread_id}"

        # Load or initialize the thread state in Redis
        existing_data = self.redis_client.get(state_key)
        saved_state = json.loads(existing_data) if existing_data else {}

        # Merge messages and state fields safely
        saved_messages = saved_state.get("messages", [])
        new_serialized = [_serialize_message(m) for m in raw_messages]

        if len(new_serialized) >= len(saved_messages):
            saved_state["messages"] = new_serialized
        else:
            saved_state["messages"] = saved_messages + new_serialized

        saved_state["thread_id"] = thread_id
        if user_id:
            saved_state["user_id"] = user_id
        if "conversation_summary" in state and state["conversation_summary"]:
            saved_state["conversation_summary"] = state["conversation_summary"]
        if "important_facts" in state and state["important_facts"]:
            saved_state["important_facts"] = state["important_facts"]
        if "negotiated_products" in state and state["negotiated_products"]:
            saved_state["negotiated_products"] = state["negotiated_products"]
        if "cart_global_discount_percent" in state and state["cart_global_discount_percent"] is not None:
            saved_state["cart_global_discount_percent"] = state["cart_global_discount_percent"]
        if "negotiation_log" in state and state["negotiation_log"]:
            saved_state["negotiation_log"] = state["negotiation_log"]
        if "current_discount_percent" in state and state["current_discount_percent"] is not None:
            saved_state["current_discount_percent"] = state["current_discount_percent"]

        last_seq = len(saved_state["messages"])
        saved_state["last_seq"] = last_seq
        if "summarized_upto_seq" not in saved_state:
            saved_state["summarized_upto_seq"] = 0

        # Persist updated state to Redis so worker tasks can access it
        self.redis_client.set(state_key, json.dumps(saved_state))

        data = {"thread_id": thread_id, "last_seq": last_seq}

        # Enqueue background summarization and MongoDB archival
        self.summarizer_queue.push(ChatSummarizerWorker.run, data)
        self.state_queue.push(MongoDbWorker.run, data)


# Shared instance
sendingResult = SendDataToQueue(redis_client=redisClient.get_redis_client())
