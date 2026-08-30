from agents.agentState import AgentState
from config.chatModel import chatModel
from services.upsell_service import upsell_service

async def recommend_node(state: AgentState):
    """End-to-end recommendation node to minimize state transitions."""
    user_id = state.get("user_id")
    cart = state.get("cart", [])
    
    # 1. Fetch Candidates (Pure DB/Vector Logic via Upsell Service)
    result = await upsell_service.generate_upsell_offer(user_id, cart)
    
    if not result.get("success") or not result.get("suggested_products"):
        return {"final_response": "I couldn't find a perfect match for your cart right now. Feel free to explore more items!"}
        
    suggested_items = result["suggested_products"]
    # Provide up to 3 items
    suggested_names = [item['name'] for item in suggested_items[:3]]
    
    # We purposefully do NOT send combo_offer immediately based on new requirements.
    # We will wait for user's positive response.
    
    # 2. Stylist LLM Call
    prompt = f"""You are a friendly AI fashion stylist on an e-commerce store. 
    The user is checking out with these items: {[c.get('name') for c in cart]}.
    You analyzed their style and found these perfect matches: {', '.join(suggested_names)}.
    
    Write 2-3 short sentences in English. Pitch these {len(suggested_names)} items as great additions to their cart. 
    Then, ASK the user if they like any of these suggestions and would like to see an exclusive combo offer. 
    DO NOT mention any discount percentages yet. Do not use markdown or emojis heavily."""
    
    fast_llm = chatModel.get_chat_model()
    try:
        stylist_response = fast_llm.invoke(prompt).content
    except Exception:
        stylist_response = f"I think {', '.join(suggested_names)} would look perfect with your cart items! Do you like any of these suggestions?"
    
    return {
        "recommended_product_id": suggested_items[0]["id"] if suggested_items else None, 
        "final_response": stylist_response
    }