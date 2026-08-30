from agents.agentState import AgentState
from config.chatModel import chatModel
from config.embeddingModel import embeddingModel
from config.vectorDatabase import vectorDB
from services.behavior_scorer import behavior_scorer
from repositories.product_repository import ProductRepository

product_repo = ProductRepository()

async def search_node(state: AgentState):
    """
    Handles direct product searches combining explicit user queries and implicit behavior profiles.
    """
    
    
    last_message = state["messages"][-1].content
    user_id = state["user_id"]
    
    fast_llm = chatModel.get_chat_model()
    
    # 1. Get Behavior Profile (Implicit Suggestions)
    scores = await behavior_scorer.get_category_affinity(user_id)
    preferred_categories = []
    if scores:
        sorted_categories = sorted(scores, key=scores.get, reverse=True)
        preferred_categories = sorted_categories[:2] # User ki top 2 pasandida categories
        
    preferences_text = f"User style context: prefers {', '.join(preferred_categories)}" if preferred_categories else ""
    
    # 2. Extract Exact Search Intent
    extraction_prompt = f"""
    The user is searching for something: "{last_message}"
    Extract the core fashion/product keyword they want (e.g., "blue denim jacket", "party wear shirt").
    Return ONLY the keyword phrase. No markdown, no quotes, no extra words.
    """
    try:
        user_query = fast_llm.invoke(extraction_prompt).content.strip()
    except Exception:
        user_query = last_message
        
    # 3. Enhance Query: User Demand + User Behavior
    # Isse search engine automatically user ke style wali cheezein upar layega
    enhanced_query = f"{user_query}. {preferences_text}".strip()
    
    # 4. Generate Embeddings and Search Pinecone
    embedder = embeddingModel.getModel()
    query_vector = embedder.embed_query(enhanced_query)
    
    index = vectorDB.get_index("dukaan-products")
    try:
        search_results = index.query(
            vector=query_vector,
            top_k=3,
            include_metadata=True
        )
    except Exception as e:
        print(f"Vector search failed: {e}")
        search_results = None
        
    # 5. Fetch actual products and format response
    found_items = []
    if search_results and hasattr(search_results, 'matches') and search_results.matches:
        for match in search_results.matches:
            p = await product_repo.get_by_id(int(match.id))
            if p:
                found_items.append(f"- {p.name} (Rs. {p.price})")
                
    if not found_items:
        return {"final_response": "I couldn't find an exact match for that right now. Would you like to try looking for something else?"}
        
    results_text = "\n".join(found_items)
    
    # 6. Final LLM formatting
    final_prompt = f"""
    You are a friendly AI shopping assistant. The user explicitly asked for: "{last_message}".
    Based on their request and past styling preferences, you found these exact items in the store:
    
    {results_text}
    
    Write a short, engaging response presenting these options to the user ONLY IN ENGLISH.
    Do NOT mention that you looked at their past preferences, just make it sound like you naturally found the perfect items.
    """
    
    try:
        final_reply = fast_llm.invoke(final_prompt).content
    except Exception:
        final_reply = f"Here are some great options for you:\n{results_text}"
    
    return {"final_response": final_reply}