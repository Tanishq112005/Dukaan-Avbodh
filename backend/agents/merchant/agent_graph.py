"""
Backward-compatibility bridge for `agents.merchant.agent_graph`.
Re-exports compile_agent_graph from `agents.merchant.graph`.
"""
from agents.merchant.graph import compile_agent_graph

__all__ = ["compile_agent_graph"]
