# services/agent_service.py
from typing import TypedDict, Annotated, Sequence, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
import operator
import os
from agentState import AgentState
from routerNode import router_node , route_decision 
from searchNode import search_node
from ..config.chatModel import chatModel
from langgraph.checkpoint import memory
from generalNode import general_node 
from negotiateNode import negotiate_node 
from recomededNode import recommend_node 





workflow = StateGraph(AgentState)

workflow.add_node("router", router_node)
workflow.add_node("search", search_node)
workflow.add_node("negotiate", negotiate_node)
workflow.add_node("recommend", recommend_node)
workflow.add_node("general", general_node)

workflow.set_entry_point("router")

workflow.add_conditional_edges(
    "router",
    route_decision,
    {
        "SEARCH": "search",
        "NEGOTIATE": "negotiate",
        "RECOMMEND": "recommend",
        "GENERAL": "general"
    }
)

workflow.add_edge("search", END)
workflow.add_edge("negotiate", END)
workflow.add_edge("recommend", END)
workflow.add_edge("general", END)

# Compile the graph
checkout_agent = workflow.compile(memory()) 

