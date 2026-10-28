from .service import merchant_agent_service, init_merchant_agent, get_merchant_agent
from .controller import merchantAgentController, MerchantAgentController
from .routes import router
from .agent import MerchantAgent
from .graph import compile_agent_graph

# Backward-compatible alias
agent_service = merchant_agent_service

__all__ = [
    "service",
    "agent_service",
    "merchant_agent_service",
    "init_merchant_agent",
    "get_merchant_agent",
    "merchantAgentController",
    "MerchantAgentController",
    "router",
    "MerchantAgent",
    "compile_agent_graph",
]
