from repositories.discount_policy_repository import DiscountPolicyRepository
from services.behavior_scorer import behavior_scorer
from models import Product
from repositories.cart_repository import cart_repository
from repositories.product_repository import ProductRepository
from services.combo_pricing_engine import combo_pricing_engine  
from repositories.order_repository import OrderRepository
from datetime import datetime, timedelta 
from utils.pricing_math import calculate_next_offer, AGENT_MAX_DISCOUNT_PERCENT
order_repo = OrderRepository()    
policy_repo = DiscountPolicyRepository()
product_repo = ProductRepository()



class NegotiationService:
    """
    Handles haggling logic by enforcing the Discount Policy and checking User Behavior scores.
    """


    async def evaluate_combo_negotiation(self, user_id: int, requested_discount: float, current_discount: float) -> dict:
        """
        Backend directly fetches the cart using user_id. 
        Agent does not need to provide product lists.
        """
     
        ## step 1: Fetch cart items and resolve products
        cart_items = await cart_repository.get_cart_items(user_id)
        
        ## Step 2: Validate cart and fetch product details
            ## if no item is found in the cart, return a failure response with an appropriate message.
        if not cart_items:
            return {"accepted": False, "counter_offer_percent": 0.0, "agent_internal_reasoning": "Cart is empty.", "products": []}
        
        
        ## Step 3: Get all the product ids from the cart and fetch their details from the product repository    
        cart_products = []
        for item in cart_items:
            p = await product_repo.get_by_id(item["product_id"])
            if p:
                cart_products.append(p)
                
        
        ## Step 4: Evaluate the limits of the discount based on the cart products 
        limits = combo_pricing_engine.get_negotiation_limits(cart_products)
        
        if limits["total_price"] == 0:
            return {"accepted": False, "counter_offer_percent": 0.0, "agent_internal_reasoning": "Total price is 0.", "products": cart_products}
            
        absolute_max = limits["absolute_max_discount_percent"]
        
    
            
        
        ## Step 5: Adjust the step size based on user behavior , check the past orders of user 
        user_orders = await order_repo.get_by_user(user_id)
        
        if not user_orders:
            absolute_max = absolute_max * 0.70 
            step = 1.0
        else:
            
            ## check if the user has placed an order in the last 30 days, if yes, then increase the step size to 2.0, else keep it at 1.5
            now = datetime.utcnow()
            has_recent_order = any(
                order.created_at and (now - order.created_at.replace(tzinfo=None)) < timedelta(days=30)
                for order in user_orders
            )
            
            if has_recent_order:
                step = 2.0
            else:
                step = 1.5
            
        
        absolute_max = round(min(absolute_max, AGENT_MAX_DISCOUNT_PERCENT), 2)
        
        ### step 6: Calculate the next offer based on the requested discount, current discount, absolute max and step size
        res = calculate_next_offer(requested_discount, current_discount, absolute_max, step)
        return {
            "accepted": res["accepted"], 
            "counter_offer_percent": res["counter"], 
            "agent_internal_reasoning": res["reason"],
            "products": cart_products
        }

negotiation_service = NegotiationService()
