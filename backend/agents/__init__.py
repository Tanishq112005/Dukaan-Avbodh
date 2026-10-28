"""
Dukaan Agents Package.
Houses user, merchant, and agent-to-agent (a2a) autonomous conversational agents.
"""

from . import user
from . import merchant
from . import a2a

# Convenient aliases
agent_to_agent = a2a

__all__ = ["user", "merchant", "a2a", "agent_to_agent"]
