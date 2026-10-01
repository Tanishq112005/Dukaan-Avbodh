import os
import json
from pydantic import BaseModel, Field
from typing import Optional, List
from redis import Redis, WatchError

# Adjust this import path based on where you run the worker from
from ...queue.connection import QueueConsumerManager 


# ==========================================
# 1. PYDANTIC SCHEMAS
# ==========================================
class Budget(BaseModel):
    min_budget: Optional[float] = Field(default=None, description="Minimum budget if mentioned")
    max_budget: Optional[float] = Field(default=None, description="Maximum budget if mentioned")

class Sizes(BaseModel):
    jeans: Optional[str] = Field(default=None)
    shirts: Optional[str] = Field(default=None)
    hoodies: Optional[str] = Field(default=None)

class ImportantFacts(BaseModel):
    gender: Optional[str] = Field(default=None, description="'men', 'women', or null")
    budget: Budget
    emotion: List[str] = Field(default_factory=list, description="Reasons for buying, e.g., ['mom birthday']")
    size: Sizes

class SummarizerOutput(BaseModel):
    summary: str = Field(description="Updated conversation summary, max 500 characters")
    important_facts: ImportantFacts
    

# ==========================================
# 2. CHAT SUMMARIZER CLASS
# ==========================================
class ChatSummarizer: 
    def __init__(self, llm, redis_client: Redis): 
        self.llm = llm 
        self.redis_client = redis_client
        self.system_prompt = """You are an expert E-Commerce Memory Manager and Fact Extractor. Your job is to analyze the latest chat messages alongside the previous conversation summary, and output an updated JSON state.

        ### TASK 1: ROLLING SUMMARY
       Create an updated summary of the entire conversation.
        - Merge the new messages into the existing summary without losing important historical context.
        - Keep the final summary concise and STRICTLY under 500 characters.
        - Focus on the user's core intent, preferences, and the current state of their request.

        ### TASK 2: FACT EXTRACTION
        Extract or update the following user preferences from the conversation:
        1. Gender Preference: Who are they shopping for? (Valid values: "men", "women", or null if unknown).
        2. Budget: Identify any price constraints. Extract minimum and maximum budget as numbers (use null if not mentioned).
        3. Emotion / Reason: Identify why they are shopping (e.g., "mom's birthday", "going on vacation"). Store as an array of strings.
        4. Size: Extract mentioned sizes for specific clothing categories.

        ### STRICT JSON OUTPUT FORMAT
        You must return ONLY a valid JSON object matching the exact schema below. Do not include markdown formatting like ```json. Use standard JSON `null` for any unknown values.

        {
          "summary": "Updated summary text (max 500 chars)",
           "important_facts": {
              "gender": "men" | "women" | null,
              "budget": {
                  "min_budget": number | null,
                  "max_budget": number | null
        },
          "emotion": ["string"],
           "size": {
              "jeans": "string" | null,
               "shirts": "string" | null,
              "hoodies": "string" | null
          } }
          }"""

    def process_summary(self, data):
        """
        Worker method to be called by RQ.
        Expects `data` to have `.thread_id` and `.last_seq` 
        """
        thread_id = data.thread_id
        current_seq = data.last_seq
        state_key = f"agent_state:{thread_id}"
        
        # 1. READ STATE (No locks yet)
        state_data = self.redis_client.get(state_key)
        if not state_data:
            print(f"[ChatSummarizer] No state found for {thread_id}")
            return
            
        state = json.loads(state_data)
        summarized_upto_seq = state.get("summarized_upto_seq", 0)
        
        # Check condition early to save LLM calls
        if current_seq - summarized_upto_seq <= 8:
            print(f"[ChatSummarizer] Not enough messages to summarize for {thread_id}.")
            return 
            
        messages = state.get("messages", [])
        end_index = len(messages) - 4
        
        if end_index <= summarized_upto_seq:
            return
            
        messages_to_summarize = messages[summarized_upto_seq:end_index]
        
        # Format messages text
        messages_text = ""
        for msg in messages_to_summarize:
            role = msg.get("type", msg.get("role", "human"))
            content = msg.get("content", "")
            messages_text += f"{role}: {content}\n"
            
        old_summary = state.get("conversation_summary", "")
        old_facts = state.get("important_facts", {})
        if isinstance(old_facts, str):
            old_facts = json.loads(old_facts) if old_facts else {}

        # 2. CALL LLM (Outside the transaction - takes time)
        prompt = (
            f"{self.system_prompt}\n\n"
            f"### PREVIOUS SUMMARY:\n{old_summary}\n\n"
            f"### PREVIOUS FACTS:\n{json.dumps(old_facts)}\n\n"
            f"### NEW MESSAGES TO SUMMARIZE:\n{messages_text}"
        )
        
        llm_with_tools = self.llm.with_structured_output(SummarizerOutput)
        result: SummarizerOutput = llm_with_tools.invoke(prompt)
        new_facts = result.important_facts.model_dump()

        # 3. ATOMIC UPDATE (Lightning fast optimistic locking)
        with self.redis_client.pipeline() as pipe:
            while True:
                try:
                    pipe.watch(state_key)
                    
                    # RE-READ the latest state in case the user sent a message during the 5s LLM call
                    latest_state_data = pipe.get(state_key)
                    latest_state = json.loads(latest_state_data) if latest_state_data else state
                    
                    # Fetch the most recent facts from the latest state to merge into
                    latest_facts = latest_state.get("important_facts", {})
                    if isinstance(latest_facts, str):
                        latest_facts = json.loads(latest_facts) if latest_facts else {}

                    # Merge the newly generated facts into the latest_facts safely
                    if new_facts.get("gender") is not None:
                        latest_facts["gender"] = new_facts["gender"]
                        
                    if new_facts.get("budget"):
                        if new_facts["budget"].get("min_budget") is not None:
                            latest_facts.setdefault("budget", {})["min_budget"] = new_facts["budget"]["min_budget"]
                        if new_facts["budget"].get("max_budget") is not None:
                            latest_facts.setdefault("budget", {})["max_budget"] = new_facts["budget"]["max_budget"]
                            
                    if new_facts.get("emotion") and len(new_facts["emotion"]) > 0:
                        latest_facts["emotion"] = new_facts["emotion"]
                        
                    if new_facts.get("size"):
                        if new_facts["size"].get("jeans") is not None:
                            latest_facts.setdefault("size", {})["jeans"] = new_facts["size"]["jeans"]
                        if new_facts["size"].get("shirts") is not None:
                            latest_facts.setdefault("size", {})["shirts"] = new_facts["size"]["shirts"]
                        if new_facts["size"].get("hoodies") is not None:
                            latest_facts.setdefault("size", {})["hoodies"] = new_facts["size"]["hoodies"]
                    
                    # Apply updates to the latest state
                    latest_state["conversation_summary"] = result.summary
                    latest_state["important_facts"] = latest_facts
                    
                    # IMPORTANT: Only advance the summarized_upto_seq pointer to what we actually processed
                    latest_state["summarized_upto_seq"] = max(latest_state.get("summarized_upto_seq", 0), end_index)
                    
                    pipe.multi()
                    pipe.set(state_key, json.dumps(latest_state))
                    pipe.execute()
                    
                    print(f"[ChatSummarizer] Successfully processed and updated memory state for thread_id: {thread_id}")
                    break
                    
                except WatchError:
                    # If this hits, the retry will just execute the JSON merge instantly without calling the LLM again
                    print(f"[ChatSummarizer] State concurrently changed for thread {thread_id}. Retrying merge...")
                    continue
                except Exception as e:
                    print(f"[ChatSummarizer] Error during summarization for thread {thread_id}: {e}")
                    pipe.unwatch()
                    break


# ==========================================
# 3. INITIALIZATION & WORKER WRAPPER
# ==========================================

# Initialize Redis client
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = Redis.from_url(redis_url, decode_responses=True)

# Initialize LLM 
# (Replace this with however you configure your small/fast LLM in Dukaan)
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

# Instantiate the summarizer
chat_summarizer = ChatSummarizer(llm=llm, redis_client=redis_client)

def run_summary_task(data):
    """
    Top-level wrapper function executed by the RQ Worker.
    Pass THIS function reference when enqueuing the task in memory_saving_node.py.
    """
    print(f"Starting summary task for thread: {data.thread_id}")
    return chat_summarizer.process_summary(data)


# ==========================================
# 4. RUN WORKER SCRIPT
# ==========================================
if __name__ == "__main__":
    # Ensure this matches the queue_name used in QueueProducerManager ("summarizer")
    queue_name = "summarizer" 
    
    print(f"Initializing Queue Consumer for '{queue_name}'...")
    consumer = QueueConsumerManager(redis_client=redis_client, queue_name=queue_name)
    
    # This blocks and listens for tasks arriving in Redis
    consumer.start()
