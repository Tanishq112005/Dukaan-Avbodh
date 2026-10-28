import logging
from typing import Optional, List, Any
from fastapi import HTTPException, status

from Negotiation.database import NegotiationDatabase, negotiationDatabase
from Cart.database import cart
from Negotiation.utils import (
    calculate_discount_limits,
    calculate_cart_discount_headroom,
    calculate_next_offer,
    calculate_product_discount_limits,
    calculate_product_next_offer,
    AGENT_MAX_DISCOUNT_PERCENT,
)
from Negotiation.schemas import (
    MaxDiscountRequest,
    MaxDiscountResponse,
    NextDiscountRequest,
    NextDiscountResponse,
    ProductNegotiationRequest,
    ProductNegotiationResponse,
    NegotiationItemDTO,
)

logger = logging.getLogger(__name__)


class NegotiationController:
    """
    Controller handling discount ceilings and interactive negotiation offers.
    Supports:
      1. Per-product negotiation before item is added to cart (Scenario 1).
      2. Per-product negotiation after item is in the cart (Scenario 2).
      3. Cart-wide compound negotiation.
    """

    def __init__(self, db: Optional[NegotiationDatabase] = None):
        self.db = db or negotiationDatabase

    async def _resolve_items(
        self,
        user_id: Optional[int],
        items: Optional[List[NegotiationItemDTO]]
    ) -> List[Any]:
        """
        Resolves items from request JSON if provided; otherwise loads from the user's cart in the DB.
        """
        if items and len(items) > 0:
            return items

        if user_id:
            cart_products = await self.db.getPoroductItemsOfCart(user_id=user_id, expand_quantities=True)
            return cart_products

        return []

    async def get_max_discount(self, req: MaxDiscountRequest) -> MaxDiscountResponse:
        """
        Calculate total possible maximum discount percentage without breaching merchant profit margins.
        """
        try:
            items = await self._resolve_items(req.user_id, req.items)
            limits = calculate_discount_limits(items)

            return MaxDiscountResponse(
                total_selling_price=limits["total_selling_price"],
                total_cost_price=limits["total_cost_price"],
                total_minimum_selling_price=limits["total_minimum_selling_price"],
                max_discount_amount=limits["max_discount_amount"],
                max_discount_percentage=limits["max_discount_percentage"],
                is_loss_leader=limits["is_loss_leader"],
            )
        except Exception as e:
            logger.exception("Error calculating maximum discount: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to calculate maximum discount: {str(e)}"
            )

    async def get_next_discount(self, req: NextDiscountRequest) -> NextDiscountResponse:
        """
        Calculate the next counter-offer discount percentage for cart-wide negotiation.
        Evaluates the current selling price of all cart items after each product's discount,
        checks required profit percentages to determine remaining headroom, and applies
        a step-wise diminishing counter-offer ON TOP of existing items as a combined discount.
        Preserves individual product discounts and updates the global cart discount.
        """
        try:
            cart_global_discount = 0.0
            if req.user_id:
                detailed_items = await self.db.get_cart_items_detailed(user_id=req.user_id)
                user_cart = await cart.get_cart(user_id=req.user_id)
                if user_cart and user_cart.discount_percentage:
                    cart_global_discount = float(user_cart.discount_percentage)
            elif req.items:
                detailed_items = [
                    {
                        "product_id": it.product_id,
                        "name": it.name,
                        "original_price": it.price,
                        "current_price": it.price * (1.0 - (it.discount_percentage or 0.0) / 100.0) if it.discount_percentage else it.price,
                        "discount_percentage": it.discount_percentage or 0.0,
                        "cost_price": it.cost_price,
                        "min_profit_margin_percent": it.min_profit_margin_percent,
                        "quantity": it.quantity,
                        "discount": it.discount or 0,
                    }
                    for it in req.items
                ]
            else:
                detailed_items = []

            if not detailed_items:
                return NextDiscountResponse(
                    accepted=False,
                    current_discount_percent=req.current_discount_percent,
                    requested_discount_percent=req.requested_discount_percent,
                    next_discount_percent=0.0,
                    counter_offer_price=0.0,
                    total_original_price=0.0,
                    absolute_max_discount_percent=0.0,
                    customer_tier="loyal",
                    reason="Your shopping cart is empty. Add items to negotiate a discount.",
                )

            headroom = calculate_cart_discount_headroom(detailed_items)
            total_original_price = headroom["total_original_price"]
            total_cost_price = headroom["total_cost_price"]
            current_cart_total = headroom["current_cart_total"]
            total_minimum_selling_price = headroom["total_minimum_selling_price"]

            # Headroom on top of current cart items
            remaining_headroom = max(0.0, current_cart_total - total_minimum_selling_price)

            # If items are already at or below cost, refuse any extra cart discount
            if headroom["is_loss_leader"] or current_cart_total <= 0 or remaining_headroom <= 0:
                return NextDiscountResponse(
                    accepted=False,
                    current_discount_percent=cart_global_discount,
                    requested_discount_percent=req.requested_discount_percent,
                    next_discount_percent=cart_global_discount,
                    counter_offer_price=current_cart_total,
                    total_original_price=total_original_price,
                    absolute_max_discount_percent=0.0,
                    customer_tier="loyal",
                    reason="Items in your cart are already at the minimum allowed selling price. Extra cart discount cannot be offered.",
                )

            # Max extra discount percentage on top of current cart total
            max_cart_ceiling = min(
                AGENT_MAX_DISCOUNT_PERCENT,
                max(0.0, (remaining_headroom / current_cart_total) * 100.0)
            )
            max_cart_ceiling = round(max_cart_ceiling, 2)

            baseline_cart_discount = max(req.current_discount_percent, cart_global_discount)

            result = calculate_next_offer(
                requested=req.requested_discount_percent,
                current=baseline_cart_discount,
                absolute_max=max_cart_ceiling,
                concession_factor=0.40,
            )

            counter_discount = result["counter"]
            counter_price = round(current_cart_total * (1.0 - counter_discount / 100.0), 2)

            # Hard financial floor check: price must stay strictly above cost
            if counter_price <= total_cost_price:
                counter_price = round(total_cost_price + 0.01, 2)
                result["accepted"] = False
                if current_cart_total > 0:
                    counter_discount = round(max(0.0, (1.0 - counter_price / current_cart_total) * 100.0), 2)
                result["reason"] = "Counter discount clipped to protect required profit margins."

            # Persist cart global discount on top of cart without modifying individual item discounts
            if req.apply_to_cart and req.user_id:
                try:
                    await cart.discountChange(req.user_id, counter_discount)
                except Exception as cart_err:
                    logger.warning("Could not auto-apply cart discount for user %s: %s", req.user_id, cart_err)

            # Sanitize reasons for customer dialogue
            raw_reason = result["reason"]
            if "maximum possible is" in raw_reason:
                clean_reason = f"Counter-offering {counter_discount}% extra discount across your cart."
            elif "maximum possible discount of" in raw_reason:
                clean_reason = f"Your current cart discount of {baseline_cart_discount}% is the absolute best deal we can offer on top of these items."
            else:
                clean_reason = raw_reason

            return NextDiscountResponse(
                accepted=result["accepted"],
                current_discount_percent=baseline_cart_discount,
                requested_discount_percent=req.requested_discount_percent,
                next_discount_percent=counter_discount,
                counter_offer_price=counter_price,
                total_original_price=total_original_price,
                absolute_max_discount_percent=max_cart_ceiling,
                customer_tier="loyal",
                reason=clean_reason,
            )

        except Exception as e:
            logger.exception("Error calculating next discount: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to calculate next discount: {str(e)}"
            )

    async def negotiate_product_discount(
        self,
        req: ProductNegotiationRequest
    ) -> ProductNegotiationResponse:
        """
        Evaluate and negotiate discount for an individual product.
        Supports both scenarios:
          1. Before adding to cart: evaluates against product profit margin & merchant ceiling.
          2. After adding to cart: inspects current discount on cart item, calculates remaining headroom,
             and optionally persists the newly negotiated discount directly to CartItem in DB.
        """
        try:
            product = await self.db.get_product_by_id(req.product_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID {req.product_id} not found."
                )

            # Check if item is already in user's active cart
            in_cart = False
            cart_item = None
            if req.user_id:
                cart_item = await self.db.get_cart_item(
                    user_id=req.user_id,
                    product_id=req.product_id,
                    size=req.size
                )
                if cart_item:
                    in_cart = True

            # Determine baseline current discount
            current_discount = req.current_discount_percent
            if in_cart and cart_item and current_discount == 0.0 and (cart_item.discount_percentage or 0.0) > 0:
                current_discount = float(cart_item.discount_percentage)

            # Calculate diminishing-return counter offer bounded by product economics
            offer = calculate_product_next_offer(
                product=product,
                requested_discount_percent=req.requested_discount_percent,
                current_discount_percent=current_discount,
                concession_factor=0.40,
            )

            updated_in_cart = False
            if in_cart and req.apply_to_cart and req.user_id:
                try:
                    await self.db.apply_item_discount(
                        user_id=req.user_id,
                        product_id=req.product_id,
                        discount_percentage=offer["next_discount_percent"],
                        discounted_price=offer["counter_offer_price"],
                        size=req.size or (cart_item.size if cart_item else None),
                    )
                    updated_in_cart = True
                except Exception as update_err:
                    logger.warning("Failed to auto-update cart item discount: %s", update_err)

            # Calculate totals for quantity
            qty = max(1, req.quantity)
            total_price = round(offer["counter_offer_price"] * qty, 2)
            base_unit_price = round(float(offer["original_price"]), 2)
            original_total = round(base_unit_price * qty, 2)
            savings = round(max(0.0, original_total - total_price), 2)

            # Sanitize confidential ceiling reasons from LLM exposure
            raw_reason = offer["reason"]
            if "maximum possible is" in raw_reason:
                clean_reason = f"Counter-offering {offer['next_discount_percent']}% discount on {product.name}."
            elif "maximum possible discount of" in raw_reason:
                clean_reason = (
                    f"Your current discount of {current_discount}% is the best price "
                    f"we can offer for {product.name}."
                )
            else:
                clean_reason = raw_reason

            return ProductNegotiationResponse(
                accepted=offer["accepted"],
                product_id=product.id,
                product_name=product.name,
                original_price=base_unit_price,
                current_discount_percent=current_discount,
                requested_discount_percent=req.requested_discount_percent,
                next_discount_percent=offer["next_discount_percent"],
                counter_offer_price=offer["counter_offer_price"],
                total_price=total_price,
                savings_amount=savings,
                in_cart=in_cart,
                updated_in_cart=updated_in_cart,
                customer_tier="loyal",
                reason=clean_reason,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Error negotiating product discount: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to negotiate product discount: {str(e)}"
            )


negotiationController = NegotiationController()
