import os
from langgraph.graph import StateGraph, END , START
from agents.user.agentState import AgentState
from agents.user.specialists.director import DirectorAgent
from agents.user.specialists.product import ProductAgent
from agents.user.specialists.cart import CartAgent
from agents.user.specialists.pricing import PricingAgent
from agents.user.specialists.payment import PaymentAgent
from agents.user.specialists.general import GeneralAgent
from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
import asyncio

# --- Monkey-patch MongoDBSaver for async support ---
async def _aget_tuple(self, config):
    return await asyncio.to_thread(self.get_tuple, config)

async def _aput(self, config, checkpoint, metadata, new_versions):
    return await asyncio.to_thread(self.put, config, checkpoint, metadata, new_versions)

async def _aput_writes(self, config, writes, task_id):
    return await asyncio.to_thread(self.put_writes, config, writes, task_id)

MongoDBSaver.aget_tuple = _aget_tuple
MongoDBSaver.aput = _aput
MongoDBSaver.aput_writes = _aput_writes




if not hasattr(JsonPlusSerializer, "dumps"):
    JsonPlusSerializer.dumps = JsonPlusSerializer.dumps_typed
if not hasattr(JsonPlusSerializer, "loads"):
    JsonPlusSerializer.loads = JsonPlusSerializer.loads_typed


def compile_agent_graph(fast_llm, tools_dict):
    workflow = StateGraph(AgentState)
    
    # --- 1. Node Creation (Instantiate the Specialist Classes) ---
    director_agent = DirectorAgent(fast_llm)
    product_agent = ProductAgent(fast_llm, tools=tools_dict.get("product_search", []))
    cart_agent = CartAgent(fast_llm, tools=tools_dict.get("cart_editing", []))
    pricing_agent = PricingAgent(fast_llm, tools=tools_dict.get("pricing_negotiation", []))
    payment_agent = PaymentAgent(fast_llm, tools=tools_dict.get("payment", []))
    general_agent = GeneralAgent(fast_llm, tools=tools_dict.get("general_query", []))
    
    # --- 2. Add Nodes to Graph (Using the `.run` method as the LangGraph node) ---
    workflow.add_node("director", director_agent.run) 
    workflow.add_node("product_search", product_agent.run)
    workflow.add_node("cart_editing", cart_agent.run)
    workflow.add_node("pricing_negotiation", pricing_agent.run)
    workflow.add_node("payment", payment_agent.run)
    workflow.add_node("general_query", general_agent.run)
    
    # --- 3. Routing Logic (Prompt logic omitted as requested) ---
    def route_from_director(state: AgentState):
        # Placeholder for your routing logic (to be written later)
        return END

    # --- 4. Define Edges ---
    workflow.set_entry_point("director")
    workflow.add_conditional_edges(
        "director", 
        route_from_director, 
        {
            "product_search": "product_search",
            "cart_editing": "cart_editing",
            "pricing_negotiation": "pricing_negotiation",
            "payment": "payment",
            "general_query": "general_query",
            END: END
        }
    )
    
    # Loop back edges to director
    workflow.add_edge("product_search", "director")
    workflow.add_edge("cart_editing", "director")
    workflow.add_edge("pricing_negotiation", "director")
    workflow.add_edge("payment", "director")
    workflow.add_edge("general_query", "director")

    # --- 5. MongoDB Checkpointer (Untouched) ---
    mongo_uri = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    sync_client = MongoClient(mongo_uri)
    memory = MongoDBSaver(sync_client)
    
    # Returns the pre-compiled graph
    return workflow.compile(checkpointer=memory)
