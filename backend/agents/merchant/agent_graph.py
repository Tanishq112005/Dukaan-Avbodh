import os
from langgraph.graph import StateGraph, END
from agents.merchant.agent_state import AgentState
from agents.merchant.agent_node import create_agent_node, create_tools_node
from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient

def compile_agent_graph(fast_llm, tools_dict):
    workflow = StateGraph(AgentState)
    
    agent_node = create_agent_node(fast_llm)
    tools_node = create_tools_node(tools_dict)
    
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tools_node)

    def should_continue(state: AgentState):
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "tools"
        return END

    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    workflow.add_edge("tools", "agent")

    mongo_uri = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    sync_client = MongoClient(mongo_uri)
    memory = MongoDBSaver(sync_client)
    
    return workflow.compile(checkpointer=memory)
