from agents.agentState import AgentState
from config.chatModel import chatModel
from services.negotiation_service import negotiation_service
from repositories.product_repository import ProductRepository
import re
import json

product_repo = ProductRepository()

async def negotiate_node(state: AgentState):
    """
    Handles discount requests securely by:
    1. Extracting mood and requested discount via LLM
    2. Enforcing boundaries via NegotiationService
    3. Generating a polite response via LLM
    """
    last_message = state["messages"][-1].content
    
    # 1. Use Fast LLM to extract Intent and Mood
    fast_llm = chatModel.get_chat_model()
    extraction_prompt = f"""
    Analyze this message from a customer bargaining on an e-commerce store: "{last_message}"
    1. Extract the requested discount percentage (float). If they just say "give me a discount", assume 5.0. If they don't specify, return 5.0.
    2. Is the user angry/frustrated/impatient? (true/false)
    Return exactly in JSON format: {{"requested_discount": float, "is_angry": bool}}
    """
    
    try:
        extraction_response = fast_llm.invoke(extraction_prompt).content
        # Extract JSON from potential markdown blocks
        json_match = re.search(r'\{.*\}', extraction_response, re.DOTALL)
        extracted_data = json.loads(json_match.group(0))
        requested_discount = float(extracted_data.get("requested_discount", 5.0))
        is_angry = bool(extracted_data.get("is_angry", False))
    except Exception as e:
        print(f"Failed to extract intent: {e}")
        requested_discount = 5.0
        is_angry = False

    # 2. Prepare Cart Data
    cart_products = []
    if state.get("cart"):
        for item in state["cart"]:
            p_id = item.get("id")
            if p_id:
                p = await product_repo.get_by_id(p_id)
                if p:
                    cart_products.append(p)
                    
    rec_id = state.get("recommended_product_id")
    if rec_id:
        p = await product_repo.get_by_id(rec_id)
        if p and p.id not in [cp.id for cp in cart_products]:
            cart_products.append(p)
            
    # Assume 0 current discount if not tracked in state
    current_discount = 0.0 
    
    # 3. Call Negotiation Service
    result = await negotiation_service.evaluate_combo_negotiation(
        user_id=state.get("user_id", 0),
        cart_products=cart_products,
        requested_discount=requested_discount,
        current_discount=current_discount,
        is_angry=is_angry
    )
    
    # 4. Generate Final Polite Response via LLM
    reasoning = result["agent_internal_reasoning"]
    offered = result["counter_offer_percent"]
    
    response_prompt = f"""
    You are an AI sales assistant. 
    The user asked: "{last_message}"
    The backend negotiation engine returned this result: 
    Accepted: {result['accepted']}, Counter Offer: {offered}%, Internal Reason: {reasoning}.
    
    Write a short, conversational response to the user IN ENGLISH ONLY. 
    If they are just agreeing to a previous suggestion (e.g., "Yes I like it"), say something like: "Great! Let's talk about a discount. I can offer you {offered}% off if you buy them together!"
    If they asked for a specific discount and it was accepted, be happy. 
    If not accepted, politely offer {offered}% and explain you can't go lower.
    (Do NOT mention the internal reason directly).
    """
    
    final_reply = fast_llm.invoke(response_prompt).content
    
    # Generate Combo Offer to send to UI
    from services.combo_pricing_engine import combo_pricing_engine
    combo_offer = None
    if len(cart_products) > 0:
        base_combo = combo_pricing_engine.calculate_combo_price(cart_products)
        # Override with negotiated discount
        base_combo["effective_discount_percent"] = offered
        base_combo["final_price"] = round(base_combo["subtotal"] * (1 - offered / 100), 2)
        combo_offer = base_combo
    
    return {
        "final_response": final_reply,
        "combo_offer": combo_offer
    }