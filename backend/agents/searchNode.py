from .agentState import AgentState

def search_node(state: AgentState):
    """Handles direct product searches quickly."""
    # MCP Tool calling removed as requested. Mocking the response for now.
    target_type = "t-shirt" # Mock target
    
    response = f"Yahan kuch {target_type} options hain jo aapne maange the. (Mock Search Results)"
    
    return {"final_response": response}