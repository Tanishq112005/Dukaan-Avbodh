import os
import re
import asyncio
from langgraph.graph import StateGraph, END, START
from agents.user.state import AgentState
from agents.user.specialists.director import DirectorAgent
from agents.user.specialists.product import ProductAgent
from agents.user.specialists.cart import CartAgent
from agents.user.specialists.pricing import PricingAgent
from agents.user.specialists.payment import PaymentAgent
from agents.user.specialists.general import GeneralAgent
from agents.user.specialists.register import RegisterAgent
from agents.user.toolCalling import create_tools_node
from langgraph.checkpoint.mongodb import MongoDBSaver
from agents.user.checkpointer import checkPointer 
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer



## helper functions for routing and post-processing
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


## graph setup functions

def initialize_agents(fast_llm, medium_llm, small_llm, tools_dict):
    """Initializes and returns all agents and tools."""
    def get_tools(*names):
        return [tools_dict[n] for n in names if n in tools_dict]
        
    agents = {
        "director": DirectorAgent(small_llm),
        "product": ProductAgent(fast_llm, tools=get_tools("search_products", "recommend_products", "get_catalog", "list_product_types", "get_products_by_type")),
        "cart": CartAgent(fast_llm, tools=get_tools("add_to_cart", "remove_from_cart", "update_cart_item_quantity", "get_cart", "clear_cart")),
        "pricing": PricingAgent(fast_llm, tools=get_tools("calculate_combo_offer", "negotiate_discount", "decline_combo_offer")),
        "payment": PaymentAgent(fast_llm, tools=get_tools("create_order", "check_payment_status")),
        "register": RegisterAgent(fast_llm, tools=get_tools("register_buyer", "get_user_details", "update_user_details")),
        "general": GeneralAgent(small_llm, tools=[])
    }
    
    tools_node = create_tools_node(tools_dict)
    
    return agents, tools_node

def setup_nodes(workflow: StateGraph, agents: dict, tools_node):
    """Registers all nodes to the StateGraph."""
    workflow.add_node("director", agents["director"].run) 
    workflow.add_node("product_search", agents["product"].run)
    workflow.add_node("cart_editing", agents["cart"].run)
    workflow.add_node("pricing_negotiation", agents["pricing"].run)
    workflow.add_node("payment", agents["payment"].run)
    workflow.add_node("register", agents["register"].run)
    workflow.add_node("general_query", agents["general"].run)
    workflow.add_node("tools", tools_node)
    workflow.add_node("post_process", post_process_node)

def setup_edges(workflow: StateGraph):
    """Registers all edges and conditional routings to the StateGraph."""
    workflow.set_entry_point("director")
    
    # 1. Route from Director
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
    
    # 2. Route from Specialists (Tools or Post Process)
    specialist_nodes = ["product_search", "cart_editing", "pricing_negotiation", "payment", "register", "general_query"]
    for node in specialist_nodes:
        workflow.add_conditional_edges(
            node, 
            route_specialist, 
            {"tools": "tools", "post_process": "post_process"}
        )
        
    # 3. Route from Tools back to the correct Specialist
    workflow.add_conditional_edges("tools", route_from_tools, {
        "product_search": "product_search",
        "cart_editing": "cart_editing",
        "pricing_negotiation": "pricing_negotiation",
        "payment": "payment",
        "register": "register",
        "general_query": "general_query"
    })
    
    # 4. Final step
    workflow.add_edge("post_process", END)


## compilation function 

def compile_agent_graph(fast_llm, medium_llm, small_llm, tools_dict):
    """Main orchestrator function that compiles the entire graph."""
    # Initialize state graph
    workflow = StateGraph(AgentState)
    
    # Setup components
    agents, tools_node = initialize_agents(fast_llm, medium_llm, small_llm, tools_dict)
    
    # Build Graph
    setup_nodes(workflow, agents, tools_node)
    setup_edges(workflow)
    
    # Get Checkpointer
    checkpointer_instance = checkPointer.getMongoDBCheckPointer()
    
    # Compile and return
    return workflow.compile(checkpointer=checkpointer_instance)