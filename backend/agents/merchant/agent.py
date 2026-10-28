import json
import asyncio
import logging
from typing import List, Optional, Any, Dict
from langchain_core.messages import BaseMessage, SystemMessage

from agents.merchant.interfaces import IAgentInterface
from agents.merchant.state import AgentState
from agents.merchant.prompts import (
    get_merchant_system_prompt,
    get_merchant_reminder,
)
from utils.text_cleaning import clean_ai_output

logger = logging.getLogger(__name__)


class MerchantAgent(IAgentInterface):
    """
    Unified Executive Merchant AI Agent for Dukaan Store Operations.
    Equipped with native function calling across all 7 store administration and analytics tools:
      1. merchant_get_store_analytics
      2. merchant_get_top_selling_products
      3. merchant_get_inventory_health_and_reorder_alerts
      4. merchant_lookup_order_details
      5. merchant_update_product_pricing_and_margin
      6. merchant_get_customer_negotiation_insights
      7. merchant_publish_catalog_item
    Operates directly on AgentState within a unified LangGraph workflow.
    """

    def __init__(self, llm, tools: Optional[List[Any]] = None):
        self.intent = "merchant_agent"

        # 1. Resolve merchant domain tools if not explicitly supplied
        if tools is not None:
            self.tools = list(tools)
        else:
            self.tools = []
            try:
                from Merchant.tools import get_merchant_langchain_tools
                self.tools.extend(get_merchant_langchain_tools())
            except Exception as e:
                logger.warning("Could not load native merchant tools: %s", e)

        # 2. Deduplicate tools by name
        unique_tools = {}
        for t in self.tools:
            name = getattr(t, "name", None) or getattr(t, "__name__", str(t))
            if name:
                unique_tools[name] = t
        self.tools = list(unique_tools.values())

        # 3. Bind tools directly to LLM for function calling
        if self.tools:
            self.llm = llm.bind_tools(self.tools)
        else:
            self.llm = llm

    def _detect_intent(self, response: Any) -> str:
        """Determines the active operational intent from LLM tool calls or output."""
        tool_calls = getattr(response, "tool_calls", None) or []
        if tool_calls:
            first_tool = tool_calls[0].get("name", "")
            if "analytics" in first_tool:
                return "analytics_inquiry"
            elif "top_selling" in first_tool:
                return "top_products_inquiry"
            elif "inventory" in first_tool:
                return "inventory_health_check"
            elif "order" in first_tool:
                return "order_lookup"
            elif "pricing" in first_tool:
                return "pricing_margin_update"
            elif "negotiation" in first_tool:
                return "negotiation_insights"
            elif "publish" in first_tool:
                return "publish_catalog_item"

        return "general_inquiry"

    def _build_prompt(self, state: AgentState) -> List[BaseMessage]:
        """Constructs prompt sequence with dynamic executive system instructions and reminder."""
        messages = list(state.get("messages", []))
        merchant_id = state.get("merchant_id") or state.get("user_id") or 1
        summary = state.get("conversation_summary")
        facts = state.get("important_facts")

        sys_msg = SystemMessage(
            content=get_merchant_system_prompt(
                merchant_id=merchant_id,
                conversation_summary=summary,
                important_facts=facts,
            )
        )
        reminder_msg = SystemMessage(content=get_merchant_reminder())

        return [sys_msg] + messages + [reminder_msg]

    def _extract_content(self, response: Any) -> str:
        """Extracts and sanitizes text content from LLM response."""
        content = getattr(response, "content", "")
        if isinstance(content, list):
            text = "\n".join(
                [
                    str(x) if isinstance(x, str) else x.get("text", "")
                    for x in content
                    if isinstance(x, (str, dict))
                ]
            )
        else:
            text = str(content or "")

        return clean_ai_output(text) if text else ""

    def run(self, state: AgentState) -> dict:
        """Executes synchronous reasoning turn."""
        prompt = self._build_prompt(state)
        response = self.llm.invoke(prompt)

        if not hasattr(response, "additional_kwargs") or response.additional_kwargs is None:
            response.additional_kwargs = {}
        response.additional_kwargs["intent"] = self.intent

        final_text = self._extract_content(response) if not getattr(response, "tool_calls", None) else ""
        intent = self._detect_intent(response)
        merchant_id = state.get("merchant_id") or state.get("user_id") or 1

        return {
            "messages": [response],
            "final_response": final_text,
            "intent": intent,
            "current_intent": intent,
            "merchant_id": merchant_id,
            "user_id": merchant_id,
        }

    async def arun(self, state: AgentState) -> dict:
        """Executes asynchronous reasoning turn."""
        prompt = self._build_prompt(state)

        if hasattr(self.llm, "ainvoke"):
            response = await self.llm.ainvoke(prompt)
        else:
            response = await asyncio.to_thread(self.llm.invoke, prompt)

        if not hasattr(response, "additional_kwargs") or response.additional_kwargs is None:
            response.additional_kwargs = {}
        response.additional_kwargs["intent"] = self.intent

        final_text = self._extract_content(response) if not getattr(response, "tool_calls", None) else ""
        intent = self._detect_intent(response)
        merchant_id = state.get("merchant_id") or state.get("user_id") or 1

        return {
            "messages": [response],
            "final_response": final_text,
            "intent": intent,
            "current_intent": intent,
            "merchant_id": merchant_id,
            "user_id": merchant_id,
        }
