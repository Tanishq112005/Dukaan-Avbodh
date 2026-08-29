from agents.agentState import AgentState
from config.chatModel import chatModel
from services.upsell_service import upsell_service

async def recommend_node(state: AgentState):
    """End-to-end recommendation node to minimize state transitions."""
    user_id = state.get("user_id")
    cart = state.get("cart", [])
    
    # 1. Fetch Candidates (Pure DB/Vector Logic via Upsell Service)
    result = await upsell_service.generate_upsell_offer(user_id, cart)
    
    if not result.get("success"):
        return {"final_response": "Abhi aapke cart ke liye koi perfect match nahi hai, please kuch aur try karein!"}
        
    suggested_item = result["suggested_product"]
    combo_offer = result["combo_offer"]
    
    # 2. Stylist LLM Call
    prompt = f"""You are a friendly AI fashion stylist on an e-commerce store. 
    The user is checking out with these items: {[c.get('name') for c in cart]}.
    You analyzed their style and found this perfect match: {suggested_item['name']}.
    The store is offering a {combo_offer['effective_discount_percent']}% discount if they add it right now.
    
    Write 2 short, enthusiastic sentences in Hinglish pitching this item and the discount. 
    Make it sound like a personal stylist recommendation. Do not use markdown or emojis heavily."""
    
    fast_llm = chatModel.get_chat_model()
    try:
        stylist_response = fast_llm.invoke(prompt).content
    except Exception:
        stylist_response = f"Aapke cart items ke saath {suggested_item['name']} perfect lagega! Abhi add karein aur {combo_offer['effective_discount_percent']}% discount payein."
    
    return {
        "recommended_product_id": suggested_item["id"], 
        "combo_offer": combo_offer,
        "final_response": stylist_response
    }