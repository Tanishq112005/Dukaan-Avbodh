from abc import ABC, abstractmethod
from typing import Any
from agents.merchant.state import AgentState


class IAgentInterface(ABC):
    """
    Standard interface contract for the Dukaan Merchant AI Agent,
    mirroring the unified User Agent architecture.
    """

    @abstractmethod
    def _build_prompt(self, state: AgentState) -> Any:
        """Constructs the prompt messages including system instructions and context."""
        pass

    @abstractmethod
    def run(self, state: AgentState) -> dict:
        """Executes synchronous reasoning."""
        pass

    @abstractmethod
    async def arun(self, state: AgentState) -> dict:
        """Executes asynchronous reasoning."""
        pass
