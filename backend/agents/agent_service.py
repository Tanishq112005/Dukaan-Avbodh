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




# --- NEGOTIATE NODE (Pure Python) ---
def negotiate_node(state: AgentState):
    """Handles discount requests securely."""
    # TODO: Connect to MCP `calculate_combo_offer`
    response = "Main is order par maximum 15% discount de sakta hu, isse zyada policy allow nahi karti."
    return {"final_response": response}

# --- RECOMMENDATION PIPELINE (Candidate Gen + Stylist + Pricing combined for low latency) ---
def recommend_node(state: AgentState):
    """End-to-end recommendation node to minimize state transitions."""
    # 1. Fetch Candidates (Pure DB/Vector Logic)
    # TODO: Call MCP `get_user_affinity` and DB `get_vector_recommendation`
    mock_candidates = [{"id": 10, "name": "Grey Skinny Jeans", "match_score": 92}]
    
    # 2. Stylist LLM Call
    prompt = f"""You are a fashion stylist. 
    The user has these items in their cart: {state.get('cart', [])}.
    The database recommends these complementary items: {mock_candidates}.
    Pick the best item and explain to the user in 1-2 friendly sentences why it matches perfectly. 
    Write in Roman Hindi/Hinglish."""
    
    stylist_response = stylist_llm.invoke(prompt)
    
    # 3. Pricing Safety Check (Pure Python)
    # TODO: Call MCP `calculate_combo_offer`
    final_text = stylist_response.content + "\n(Add this now for a special 15% combo discount!)"
    
    return {"recommended_product_id": 10, "final_response": final_text}

# --- GENERAL CHAT NODE ---
def general_node(state: AgentState):
    response = llm.invoke(state["messages"]).content
    return {"final_response": response}

# --- BUILD THE GRAPH ---
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
checkout_agent = workflow.compile()
