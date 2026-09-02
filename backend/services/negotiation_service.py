from repositories.discount_policy_repository import DiscountPolicyRepository
from services.behavior_scorer import behavior_scorer
from models import Product
from repositories.cart_repository import cart_repository
from repositories.product_repository import ProductRepository
        
policy_repo = DiscountPolicyRepository()

class NegotiationService:
    """
    Handles haggling logic by enforcing the Discount Policy and checking User Behavior scores.
    """
    
    async def evaluate_negotiation(self, user_id: int, product: Product, requested_discount: float, current_discount: float) -> dict:
        # 1. Fetch Product specific policy
        # Assume repo has this method or similar. Using try-except to mock if missing.
        try:
            policy = await policy_repo.get_by_product_id(product.id)
        except AttributeError:
            policy = None # Fallback if method not implemented
            
        from utils.pricing_math import calculate_absolute_max, calculate_next_offer, AGENT_MAX_DISCOUNT_PERCENT
        max_discount = min(policy.max_discount_percent, AGENT_MAX_DISCOUNT_PERCENT) if policy else AGENT_MAX_DISCOUNT_PERCENT
        agent_step = policy.agent_step_percent if policy else 2.5
        min_loyalty = policy.min_loyalty_score if policy else 5.0
        
        # 3. Security Check
        absolute_max = min(calculate_absolute_max(product, max_discount), AGENT_MAX_DISCOUNT_PERCENT)
        
        # 4. Check User Loyalty — better shoppers get a larger step toward the 5% cap
        scores = await behavior_scorer.get_category_affinity(user_id)
        user_loyalty_score = sum(scores.values()) if scores else 0.0
        
        if user_loyalty_score < min_loyalty:
            absolute_max = round(absolute_max * 0.75, 2)
            step = min(agent_step, 1.0)
        elif user_loyalty_score >= min_loyalty * 1.5:
            step = min(max(agent_step, 2.0), 2.5)
        else:
            step = min(max(agent_step, 1.5), 2.0)
            
        # 5. Negotiation Logic — each call only steps once; next ask requires another tool call
        res = calculate_next_offer(requested_discount, current_discount, absolute_max, step)
        return {
            "accepted": res["accepted"], 
            "counter_offer_percent": res["counter"], 
            "agent_internal_reasoning": res["reason"]
        }

    async def evaluate_combo_negotiation(self, user_id: int, requested_discount: float, current_discount: float) -> dict:
        """
        Backend directly fetches the cart using user_id. 
        Agent does not need to provide product lists.
        """
     
        product_repo = ProductRepository()
        cart_items = await cart_repository.get_cart_items(user_id)
        
        if not cart_items:
            return {"accepted": False, "counter_offer_percent": 0.0, "agent_internal_reasoning": "Cart is empty.", "products": []}
            
        cart_products = []
        for item in cart_items:
            p = await product_repo.get_by_id(item["product_id"])
            if p:
                cart_products.append(p)
                
        if not cart_products:
            return {"accepted": False, "counter_offer_percent": 0.0, "agent_internal_reasoning": "No valid products found in cart.", "products": []}

        # 1. Safely use the ComboPricingEngine to get the hidden mathematical ceiling
        from services.combo_pricing_engine import combo_pricing_engine
        limits = combo_pricing_engine.get_negotiation_limits(cart_products)
        
        if limits["total_price"] == 0:
            return {"accepted": False, "counter_offer_percent": 0.0, "agent_internal_reasoning": "Total price is 0.", "products": cart_products}
            
        absolute_max = limits["absolute_max_discount_percent"]
        
        # 2. Fetch Average Minimum Loyalty from Policies
        avg_min_loyalty = 0.0
        valid_policies = 0
        
        for p in cart_products:
            try:
                policy = await policy_repo.get_for_product(p.id)
                if policy:
                    avg_min_loyalty += policy.min_loyalty_score
                    valid_policies += 1
            except AttributeError:
                pass
                
        if valid_policies > 0:
            avg_min_loyalty /= valid_policies
        else:
            avg_min_loyalty = 5.0
            
        # 3. Loyalty Check
        scores = await behavior_scorer.get_category_affinity(user_id)
        user_loyalty_score = sum(scores.values()) if scores else 0.0
        
        if user_loyalty_score < avg_min_loyalty:
            absolute_max = absolute_max * 0.70  # Only loyal users get the full max pool
            step = 1.0
        elif user_loyalty_score >= avg_min_loyalty * 1.5:
            step = 2.0
        else:
            step = 1.5
            
        from utils.pricing_math import calculate_next_offer, AGENT_MAX_DISCOUNT_PERCENT
        absolute_max = round(min(absolute_max, AGENT_MAX_DISCOUNT_PERCENT), 2)
        
        # Each user ask must call this tool again to get the next step (never jump 5% in one go)
        res = calculate_next_offer(requested_discount, current_discount, absolute_max, step)
        return {
            "accepted": res["accepted"], 
            "counter_offer_percent": res["counter"], 
            "agent_internal_reasoning": res["reason"],
            "products": cart_products
        }

negotiation_service = NegotiationService()
