"""
Backward-compatibility bridge for `agents.merchant.agent_state`.
Re-exports AgentState from `agents.merchant.state`.
"""
from agents.merchant.state import AgentState

__all__ = ["AgentState"]
