"""
Backward-compatibility bridge for `agents.merchant.agent_node`.
Provides legacy agent_node and tools_node helpers while delegating to `agents.merchant.graph`.
"""
from typing import Dict, Any
from agents.merchant.agent import MerchantAgent
from agents.merchant.graph import create_tools_node, resolve_all_merchant_tools


def create_agent_node(fast_llm):
    """Legacy helper returning a callable agent node function."""
    agent = MerchantAgent(fast_llm)

    async def agent_node(state):
        return await agent.arun(state)

    return agent_node


__all__ = ["create_agent_node", "create_tools_node", "resolve_all_merchant_tools"]
