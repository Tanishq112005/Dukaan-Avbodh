from abc import ABC, abstractmethod  
from ..agentState import AgentState


class IAgentInterface(ABC): 
    
    @abstractmethod
    def _build_prompt(self , messages):
        pass 
    
    
    @abstractmethod
    def run(self, state: AgentState):
        pass 
    
    
    
    