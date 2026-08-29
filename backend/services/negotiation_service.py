from repositories.discount_policy_repository import DiscountPolicyRepository
from services.behavior_scorer import behavior_scorer
from models import Product

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
            
        # 2. Extract Policy Rules or Apply Defaults
        max_discount = policy.max_discount_percent if policy else 15.0
        agent_step = policy.agent_step_percent if policy else 2.5
        min_loyalty = policy.min_loyalty_score if policy else 5.0
        
        # 3. Security Check: Never exceed merchant's strict minimum profit limit
        # Even if policy says 30%, if cost_price prevents it, we cap it.
        profit_cap = ((product.price - (product.cost_price * (1 + product.min_profit_margin_percent / 100))) / product.price) * 100
        absolute_max = min(max_discount, profit_cap)
        
        # 4. Check User Loyalty
        scores = await behavior_scorer.get_category_affinity(user_id)
        user_loyalty_score = sum(scores.values()) if scores else 0.0
        
        # If user is a guest/new, shrink their max allowable discount
        if user_loyalty_score < min_loyalty:
            absolute_max = absolute_max * 0.75  # Sirf loyal customers ko pura discount milega
            
        absolute_max = round(absolute_max, 2)
            
        # 5. Negotiation Logic
        # User requested less than what we are already giving
        if requested_discount <= current_discount:
            return {
                "accepted": True, 
                "counter_offer_percent": current_discount, 
                "agent_internal_reasoning": "User asked for less/same discount. Accept current."
            }
            
        # User asked for more than our absolute maximum
        if requested_discount > absolute_max:
            # We step up from our current offer, but cap it at absolute_max
            next_offer = min(current_discount + agent_step, absolute_max)
            next_offer = round(next_offer, 2)
            
            if next_offer <= current_discount:
                return {
                    "accepted": False, 
                    "counter_offer_percent": current_discount, 
                    "agent_internal_reasoning": f"Hit strict margin limit. Cannot exceed {absolute_max}%."
                }
                
            return {
                "accepted": False, 
                "counter_offer_percent": next_offer, 
                "agent_internal_reasoning": f"Requested {requested_discount}% is too high. Countering with {next_offer}%."
            }
            
        # User requested an amount within our safe limits
        return {
            "accepted": True, 
            "counter_offer_percent": requested_discount, 
            "agent_internal_reasoning": "Requested discount is within safe margins and loyalty limits. Accept."
        }

    async def evaluate_combo_negotiation(self, user_id: int, cart_products: list[Product], requested_discount: float, current_discount: float, is_angry: bool = False) -> dict:
        """
        Negotiation logic when the user is trying to bargain on the ENTIRE cart/combo.
        """
        if not cart_products:
            return {"accepted": False, "counter_offer_percent": 0.0, "agent_internal_reasoning": "Cart is empty."}
            
        # 1. Fetch Mathematical Limits from ComboPricingEngine
        from services.combo_pricing_engine import combo_pricing_engine
        limits = combo_pricing_engine.get_negotiation_limits(cart_products)
        
        if limits["total_price"] == 0:
            return {"accepted": False, "counter_offer_percent": 0.0, "agent_internal_reasoning": "Total price is 0."}
            
        absolute_max = limits["absolute_max_discount_percent"]
        
        # 2. Fetch Aggregated Policies for Haggling Rules
        avg_base_discount = 0.0
        avg_agent_step = 0.0
        avg_min_loyalty = 0.0
        valid_policies = 0
        
        for p in cart_products:
            try:
                policy = await policy_repo.get_by_product_id(p.id)
                if policy:
                    avg_base_discount += policy.base_discount_percent
                    avg_agent_step += policy.agent_step_percent
                    avg_min_loyalty += policy.min_loyalty_score
                    valid_policies += 1
            except AttributeError:
                pass
                
        if valid_policies > 0:
            avg_base_discount /= valid_policies
            avg_agent_step /= valid_policies
            avg_min_loyalty /= valid_policies
        else:
            avg_base_discount = 0.0
            avg_agent_step = 2.0
            avg_min_loyalty = 5.0
            
        # --- ANGRY USER RULE ---
        # Agar user gussa hai toh deal jaldi close karne ke liye step size double kar do
        if is_angry:
            avg_agent_step *= 2.0
            
        # 3. Loyalty Check
        scores = await behavior_scorer.get_category_affinity(user_id)
        user_loyalty_score = sum(scores.values()) if scores else 0.0
        
        # Agar user bilkul naya hai ya loyalty kam hai, usko ye max pool pura nahi denge
        if user_loyalty_score < avg_min_loyalty:
            absolute_max = absolute_max * 0.70  # Only loyal users get to push to the absolute max
            
        absolute_max = round(absolute_max, 2)
        
        # 4. Haggling Logic (Using Average Agent Step)
        if requested_discount <= current_discount:
            return {
                "accepted": True, 
                "counter_offer_percent": current_discount, 
                "agent_internal_reasoning": "User asked for less/same on combo. Accept."
            }
            
        if requested_discount > absolute_max:
            next_offer = min(current_discount + avg_agent_step, absolute_max)
            next_offer = round(next_offer, 2)
            
            if next_offer <= current_discount:
                return {
                    "accepted": False, 
                    "counter_offer_percent": current_discount, 
                    "agent_internal_reasoning": f"Combo profit limit hit. Cannot exceed {absolute_max}%."
                }
                
            return {
                "accepted": False, 
                "counter_offer_percent": next_offer, 
                "agent_internal_reasoning": f"Combo requested {requested_discount}% is too high. Countering with {next_offer}%."
            }
            
        return {
            "accepted": True, 
            "counter_offer_percent": requested_discount, 
            "agent_internal_reasoning": "Combo discount requested is safe. Accept!"
        }

negotiation_service = NegotiationService()
