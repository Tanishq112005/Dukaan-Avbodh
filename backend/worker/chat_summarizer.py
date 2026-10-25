import os
import json
import re
from pydantic import BaseModel, Field
from typing import Optional, List
from redis import Redis, WatchError
from config.redis import redisClient
from config.chatModel import chatModel
from .base import BaseWorker


# ==========================================
# 1. PYDANTIC SCHEMAS
# ==========================================
class Budget(BaseModel):
    min_budget: Optional[float] = Field(
        default=None, description="Minimum budget if mentioned"
    )
    max_budget: Optional[float] = Field(
        default=None, description="Maximum budget if mentioned"
    )


class Sizes(BaseModel):
    jeans: Optional[str] = Field(default=None)
    shirts: Optional[str] = Field(default=None)
    hoodies: Optional[str] = Field(default=None)


class ImportantFacts(BaseModel):
    gender: Optional[str] = Field(default=None, description="'men', 'women', or null")
    budget: Optional[Budget] = Field(
        default_factory=Budget, description="Price constraints"
    )
    emotion: List[str] = Field(
        default_factory=list, description="Reasons for buying, e.g., ['mom birthday']"
    )
    size: Optional[Sizes] = Field(
        default_factory=Sizes, description="Known apparel sizes"
    )


class SummarizerOutput(BaseModel):
    summary: str = Field(description="Updated conversation summary, max 500 characters")
    important_facts: ImportantFacts


# ==========================================
# 2. CHAT SUMMARIZER WORKER
# ==========================================
class ChatSummarizerWorker(BaseWorker):
    _instance = None

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

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls(
                llm=chatModel.get_large_chat_model(),
                redis_client=redisClient.get_redis_client(),
            )
        return cls._instance

    @classmethod
    def run(cls, data: dict):
        """
        Worker method to be called by RQ.
        Expects `data` to have `thread_id` and optional `last_seq`.
        """
        instance = cls.get_instance()
        return instance.process_summary(data)

    def process_summary(self, data):
        """
        Internal method for processing the summary.
        """
        thread_id = data.get("thread_id")
        current_seq = data.get("last_seq")
        state_key = f"agent_state:{thread_id}"

        # 1. READ STATE (No locks yet)
        state_data = self.redis_client.get(state_key)
        if not state_data:
            print(f"[ChatSummarizer] No state found for {thread_id}")
            return

        state = json.loads(state_data)
        summarized_upto_seq = state.get("summarized_upto_seq", 0)
        messages = state.get("messages", [])

        # If current_seq was not passed, derive from messages count
        if current_seq is None or current_seq <= 0:
            current_seq = len(messages)

        # Check condition early to save LLM calls
        trigger_threshold = int(os.getenv("SUMMARIZER_TRIGGER_THRESHOLD", "8"))
        if current_seq - summarized_upto_seq <= trigger_threshold:
            print(
                f"[ChatSummarizer] Not enough messages to summarize for {thread_id} ({current_seq - summarized_upto_seq} new, threshold {trigger_threshold})."
            )
            return None

        end_index = len(messages) - 4

        if end_index <= summarized_upto_seq:
            return None

        messages_to_summarize = messages[summarized_upto_seq:end_index]

        # Robustly format message texts across various object/dict formats
        messages_text = ""
        for msg in messages_to_summarize:
            if isinstance(msg, dict):
                role = (
                    msg.get("type") or msg.get("role") or msg.get("sender") or "human"
                )
                content = msg.get("content") or msg.get("message") or ""
                if not content and "data" in msg and isinstance(msg["data"], dict):
                    content = msg["data"].get("content", "")
            elif hasattr(msg, "content"):
                role = getattr(msg, "type", "human")
                content = msg.content
            else:
                role = "user"
                content = str(msg)

            if isinstance(content, list):
                content = " ".join(
                    item.get("text", "") if isinstance(item, dict) else str(item)
                    for item in content
                )

            if role in ("tool", "function"):
                content = "[Tool output processed]"

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

        result: Optional[SummarizerOutput] = None
        # Attempt structured output first
        try:
            llm_with_tools = self.llm.with_structured_output(SummarizerOutput)
            res = llm_with_tools.invoke(prompt)
            if isinstance(res, SummarizerOutput):
                result = res
            elif isinstance(res, dict):
                result = SummarizerOutput(**res)
        except Exception as structured_err:
            print(
                f"[ChatSummarizer] with_structured_output fallback needed: {structured_err}"
            )

        # Fallback for reasoning models emitting thought tags or standard text
        if result is None:
            try:
                raw_response = self.llm.invoke(prompt)
                raw_text = (
                    raw_response.content
                    if hasattr(raw_response, "content")
                    else str(raw_response)
                )
                # Strip reasoning / thoughts
                cleaned_text = re.sub(
                    r"<thought>.*?</thought>", "", raw_text, flags=re.DOTALL
                ).strip()
                json_match = re.search(
                    r"```(?:json)?\s*(\{.*?\})\s*```", cleaned_text, flags=re.DOTALL
                )
                if json_match:
                    cleaned_text = json_match.group(1)
                else:
                    start_idx = cleaned_text.find("{")
                    end_idx = cleaned_text.rfind("}")
                    if start_idx != -1 and end_idx != -1:
                        cleaned_text = cleaned_text[start_idx : end_idx + 1]

                parsed_json = json.loads(cleaned_text)
                result = SummarizerOutput(**parsed_json)
            except Exception as parse_err:
                print(
                    f"[ChatSummarizer] Failed to parse LLM summarizer output: {parse_err}"
                )
                return

        new_facts = result.important_facts.model_dump()

        # 3. ATOMIC UPDATE (Lightning fast optimistic locking)
        with self.redis_client.pipeline() as pipe:
            while True:
                try:
                    pipe.watch(state_key)

                    # RE-READ the latest state in case the user sent a message during the 5s LLM call
                    latest_state_data = pipe.get(state_key)
                    latest_state = (
                        json.loads(latest_state_data) if latest_state_data else state
                    )

                    # Fetch the most recent facts from the latest state to merge into
                    latest_facts = latest_state.get("important_facts", {})
                    if isinstance(latest_facts, str):
                        latest_facts = json.loads(latest_facts) if latest_facts else {}

                    # Merge the newly generated facts into the latest_facts safely
                    if new_facts.get("gender") is not None:
                        latest_facts["gender"] = new_facts["gender"]

                    if new_facts.get("budget"):
                        if new_facts["budget"].get("min_budget") is not None:
                            latest_facts.setdefault("budget", {})["min_budget"] = (
                                new_facts["budget"]["min_budget"]
                            )
                        if new_facts["budget"].get("max_budget") is not None:
                            latest_facts.setdefault("budget", {})["max_budget"] = (
                                new_facts["budget"]["max_budget"]
                            )

                    if new_facts.get("emotion") and len(new_facts["emotion"]) > 0:
                        latest_facts["emotion"] = new_facts["emotion"]

                    if new_facts.get("size"):
                        if new_facts["size"].get("jeans") is not None:
                            latest_facts.setdefault("size", {})["jeans"] = new_facts[
                                "size"
                            ]["jeans"]
                        if new_facts["size"].get("shirts") is not None:
                            latest_facts.setdefault("size", {})["shirts"] = new_facts[
                                "size"
                            ]["shirts"]
                        if new_facts["size"].get("hoodies") is not None:
                            latest_facts.setdefault("size", {})["hoodies"] = new_facts[
                                "size"
                            ]["hoodies"]

                    # Apply updates to the latest state
                    latest_state["conversation_summary"] = result.summary
                    latest_state["important_facts"] = latest_facts

                    # IMPORTANT: Only advance the summarized_upto_seq pointer to what we actually processed
                    latest_state["summarized_upto_seq"] = max(
                        latest_state.get("summarized_upto_seq", 0), end_index
                    )

                    pipe.multi()
                    pipe.set(state_key, json.dumps(latest_state))
                    pipe.execute()

                    print(
                        f"[ChatSummarizer] Successfully processed and updated memory state for thread_id: {thread_id}"
                    )
                    return result

                except WatchError:
                    # If this hits, the retry will just execute the JSON merge instantly without calling the LLM again
                    print(
                        f"[ChatSummarizer] State concurrently changed for thread {thread_id}. Retrying merge..."
                    )
                    continue
                except Exception as e:
                    print(
                        f"[ChatSummarizer] Error during summarization for thread {thread_id}: {e}"
                    )
                    pipe.unwatch()
                    return None
        return None
