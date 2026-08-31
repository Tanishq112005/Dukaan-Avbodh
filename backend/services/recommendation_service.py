from config.embeddingModel import EmbeddingModel
from config.vectorDatabase import vectorDB
from services.behavior_scorer import behavior_scorer
from repositories.product_repository import ProductRepository

product_repo = ProductRepository()

class RecommendationService:
    def __init__(self):
        # Yahan par `EmbeddingModel()` object banana zaroori tha
        self.embedding_model = EmbeddingModel().getModel()
        self.vector_index = vectorDB.get_index("dukaan-products") 
        
    async def get_best_suggestion(self, user_id: int, cart_items: list[dict]):
        """
        Calculates the best possible product to suggest using:
        1. Behavior score (Category)
        2. Cart Items (Style/Context matching)
        3. Vector Embeddings (Semantic Search)
        """
        
        # --- 1. Get Sorted Categories from Behavior Score ---
        scores = await behavior_scorer.get_category_affinity(user_id)
        
        target_category = None
        if scores:
            # Sort categories by score in descending order
            sorted_categories = sorted(scores, key=scores.get, reverse=True)
            
            # Find categories already present in the cart to avoid suggesting the exact same type
            cart_categories = set(item.get("type", item.get("category", "")) for item in cart_items)
            
            # Try to find the highest scoring category that is NOT in the cart
            for category in sorted_categories:
                if category not in cart_categories:
                    target_category = category
                    break
            
            # If all top categories are already in the cart, fallback to SECOND highest
            if not target_category and sorted_categories:
                if len(sorted_categories) > 1:
                    target_category = sorted_categories[1]
                else:
                    target_category = sorted_categories[0]
                    
        # --- 1.5 The Cold-Start / Fallback Pattern ---
        # Agar behaviour se koi category nahi mili (naya user) ya sab 0 hai
        if not target_category:
            cart_categories = set(item.get("type", item.get("category", "")) for item in cart_items)
            
            # Fashion Logic: Tops vs Bottoms
            tops = {"shirt", "t-shirt", "hoodie"}
            bottoms = {"jeans", "short"}
            
            if not cart_categories:
                target_category = "jeans" # Khali cart, start with bottom
            else:
                # Agar sirf Top (Shirt/T-shirt) hai cart mein -> Jeans (Bottom) do
                if cart_categories.intersection(tops) and not cart_categories.intersection(bottoms):
                    target_category = "jeans" if "jeans" not in cart_categories else "short"
                    
                # Agar sirf Bottom (Jeans/Shorts) hai cart mein -> Shirt (Top) do
                elif cart_categories.intersection(bottoms) and not cart_categories.intersection(tops):
                    target_category = "shirt" if "shirt" not in cart_categories else "t-shirt"
                    
                # Agar outfit complete hai (dono hain), toh bachi hui cheezein do
                else:
                    FASHION_FLOW = ["hoodie", "t-shirt", "shirt", "short", "jeans"]
                    for category in FASHION_FLOW:
                        if category not in cart_categories:
                            target_category = category
                            break
                            
            if not target_category:
                target_category = "jeans" # Absolute fallback
                
        # --- 2. Build Context String for LLM/Embedder ---
        # Tumhare naye rule ke hisaab se: Yahan hum pehle ek "Fashion Theorist" LLM chalayenge
        cart_description = ", ".join([item.get("name", "") for item in cart_items]) if cart_items else "None"
        
        fashion_style_suggestion = ""
        if cart_description != "None" and target_category:
            # Apni custom ChatModel factory ka use kar rahe hain
            from config.chatModel import ChatModel
            fast_llm = ChatModel().get_chat_model()
            
            prompt = f"""
            You are a master fashion theorist.
            The user currently has these items in their cart: {cart_description}.
            We need to suggest an item from the category: '{target_category}'.
            What specific COLOR and STYLE would match best with their cart?
            For example, if they have 'Blue Pants' and category is 'Shirt', answer ONLY 'White casual'.
            Provide ONLY a 1-3 word answer containing the best color and fit/style.
            """
            try:
                llm_response = await fast_llm.ainvoke(prompt)
                fashion_style_suggestion = llm_response.content.strip()
            except Exception as e:
                print(f"Fashion Theorist LLM failed, using fallback. {e}")
                
        if fashion_style_suggestion:
            search_query = f"Category: {target_category}. Color and Style: {fashion_style_suggestion}"
        else:
            search_query = f"Category: {target_category}. Matches with: {cart_description}" if target_category else "Best trending stylish clothes"
            
        # --- 3. Generate Vector Embedding using HuggingFace ---
        import asyncio
        query_vector = await asyncio.to_thread(self.embedding_model.embed_query, search_query)
        
        # Determine Gender: pehle cart se try karo, warna current browsing session se
        # (cart khali hona normal hai jab tak user kuch add na kare — is case mein
        # bina gender-fallback ke, opposite-gender items suggest ho jaate the)
        cart_genders = [item.get("gender") for item in cart_items if item.get("gender")]
        if cart_genders:
            target_gender = max(set(cart_genders), key=cart_genders.count)
        else:
            target_gender = await behavior_scorer.get_current_gender_context(user_id)
        
        filter_dict = {}
        if target_category:
            filter_dict["category"] = target_category
        if target_gender and target_gender != "unisex":
            filter_dict["gender"] = {"$in": [target_gender, "unisex"]}

        
        try:
            import asyncio
            search_results = await asyncio.to_thread(
                self.vector_index.query,
                vector=query_vector,
                top_k=3, # Top 3 items la rahe hain
                include_metadata=True,
                filter=filter_dict
            )
            
            # --- 5. Return Best Matches ---
            if search_results and search_results.matches:
                suggested_products = []
                for match in search_results.matches:
                    product = await product_repo.get_by_id(int(match.id))
                    if product:
                        suggested_products.append(product)
                return suggested_products
                    
        except Exception as e:
            print(f"Error querying Vector DB: {e}")
            
        return []

# Export instance
recommendation_service = RecommendationService()
