import os
from langgraph.graph import StateGraph, END , START
from agents.user.agentState import AgentState
from agents.user.specialists.director import DirectorAgent
from agents.user.specialists.product import ProductAgent
from agents.user.specialists.cart import CartAgent
from agents.user.specialists.pricing import PricingAgent
from agents.user.specialists.payment import PaymentAgent
from agents.user.specialists.general import GeneralAgent
from agents.user.specialists.register import RegisterAgent
from agents.user.agent_nodes import create_tools_node
import re
from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient
from checkpointer import checkPointer 
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


def compile_agent_graph(fast_llm, small_llm, tools_dict):
    workflow = StateGraph(AgentState)
    
    # --- 1. Node Creation (Instantiate the Specialist Classes) ---
    # Helper function to safely pull multiple specific tools by their exact MCP function name
    def get_tools(*names):
        return [tools_dict[n] for n in names if n in tools_dict]
        
    director_agent = DirectorAgent(small_llm)
    
    product_agent = ProductAgent(fast_llm, tools=get_tools(
        "search_products", "recommend_products", "get_catalog", "list_product_types", "get_products_by_type"
    ))
    cart_agent = CartAgent(fast_llm, tools=get_tools(
        "add_to_cart", "remove_from_cart", "update_cart_item_quantity", "get_cart", "clear_cart"
    ))
    pricing_agent = PricingAgent(fast_llm, tools=get_tools(
        "calculate_combo_offer", "negotiate_discount", "decline_combo_offer"
    ))
    payment_agent = PaymentAgent(fast_llm, tools=get_tools(
        "create_order", "check_payment_status"
    ))
    register_agent = RegisterAgent(fast_llm, tools=get_tools(
        "register_buyer", "get_user_details", "update_user_details"
    ))
    general_agent = GeneralAgent(small_llm, tools=[])
    
    tools_node = create_tools_node(tools_dict)
    
    def post_process_node(state: AgentState):
        messages = state.get("messages", [])
        if not messages: return {}
        last_msg = messages[-1]
        final_text = last_msg.content if not last_msg.tool_calls else ""
        if isinstance(final_text, list):
            final_text = "\n".join([str(x) if isinstance(x, str) else x.get("text", "") for x in final_text if isinstance(x, (str, dict))])
        elif not isinstance(final_text, str):
            final_text = str(final_text)
        if final_text:
            final_text = re.sub(r'<thought>.*?</thought>', '', final_text, flags=re.DOTALL).strip()
        return {"final_response": final_text}
    
    # --- 2. Add Nodes to Graph (Using the `.run` method as the LangGraph node) ---
    workflow.add_node("director", director_agent.run) 
    workflow.add_node("product_search", product_agent.run)
    workflow.add_node("cart_editing", cart_agent.run)
    workflow.add_node("pricing_negotiation", pricing_agent.run)
    workflow.add_node("payment", payment_agent.run)
    workflow.add_node("register", register_agent.run)
    workflow.add_node("general_query", general_agent.run)
    workflow.add_node("tools", tools_node)
    workflow.add_node("post_process", post_process_node)
    
    # --- 3. Routing Logic ---
    def route_from_director(state: AgentState):
        # We read the intent string saved by the Director node
        return state.get("intent", "general_query")
        
    def route_specialist(state: AgentState):
        messages = state.get("messages", [])
        if messages and messages[-1].tool_calls:
            return "tools"
        return "post_process"
        
    def route_from_tools(state: AgentState):
        intent = state.get("intent")
        mapping = {
            "product": "product_search",
            "cart": "cart_editing",
            "pricing": "pricing_negotiation",
            "payment": "payment",
            "register": "register",
            "general": "general_query"
        }
        return mapping.get(intent, "general_query")

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
            "register": "register",
            "general_query": "general_query"
        }
    )
    
    # Each specialist routes either to 'tools' or 'post_process'
    for node in ["product_search", "cart_editing", "pricing_negotiation", "payment", "register", "general_query"]:
        workflow.add_conditional_edges(node, route_specialist, {"tools": "tools", "post_process": "post_process"})
        
    # Tools route back to the appropriate specialist
    workflow.add_conditional_edges("tools", route_from_tools, {
        "product_search": "product_search",
        "cart_editing": "cart_editing",
        "pricing_negotiation": "pricing_negotiation",
        "payment": "payment",
        "register": "register",
        "general_query": "general_query"
    })
    
    # End graph after post-processing
    workflow.add_edge("post_process", END)

    
    ### Getting the redis checkpointer ### 
    checkpointer = checkPointer.getRedisCheckPointer() 
    
    # Returns the pre-compiled graph
    return workflow.compile(checkpointer=checkPointer)
