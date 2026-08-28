from agentState import AgentState
from ..config.chatModel import chatModel 


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
    
    stylist_response = chatModel.get_chat_model().invoke(prompt)
    
    # 3. Pricing Safety Check (Pure Python)
    # TODO: Call MCP `calculate_combo_offer`
    final_text = stylist_response.content + "\n(Add this now for a special 15% combo discount!)"
    
    return {"recommended_product_id": 10, "final_response": final_text}