import logging
from typing import Optional, List, Any
from fastapi import HTTPException, status

from Negotiation.database import NegotiationDatabase, negotiationDatabase
from Negotiation.utils import (
    calculate_discount_limits,
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
        Treats customer with loyal concession factor (0.40).
        """
        try:
            items = await self._resolve_items(req.user_id, req.items)
            if not items:
                return NextDiscountResponse(
                    accepted=False,
                    current_discount_percent=req.current_discount_percent,
                    requested_discount_percent=req.requested_discount_percent,
                    next_discount_percent=0.0,
                    counter_offer_price=0.0,
                    total_original_price=0.0,
                    absolute_max_discount_percent=0.0,
                    customer_tier="loyal",
                    reason="No items provided and user cart is empty.",
                )

            limits = calculate_discount_limits(items)
            total_selling_price = limits["total_selling_price"]
            total_cost_price = limits["total_cost_price"]

            # If items are already at or below cost, refuse any extra discount
            if limits["is_loss_leader"] or total_selling_price <= 0:
                return NextDiscountResponse(
                    accepted=False,
                    current_discount_percent=req.current_discount_percent,
                    requested_discount_percent=req.requested_discount_percent,
                    next_discount_percent=0.0,
                    counter_offer_price=total_selling_price,
                    total_original_price=total_selling_price,
                    absolute_max_discount_percent=0.0,
                    customer_tier="loyal",
                    reason="Items are at or below cost price. Extra discount cannot be offered.",
                )

            max_possible = limits["max_discount_percentage"]
            ceiling = round(min(max_possible, AGENT_MAX_DISCOUNT_PERCENT), 2)
            concession_factor = 0.40

            result = calculate_next_offer(
                requested=req.requested_discount_percent,
                current=req.current_discount_percent,
                absolute_max=ceiling,
                concession_factor=concession_factor,
            )

            counter_discount = result["counter"]
            counter_price = round(total_selling_price * (1.0 - counter_discount / 100.0), 2)

            # Hard financial floor check: price must stay strictly above cost
            if counter_price <= total_cost_price:
                counter_price = round(total_cost_price + 0.01, 2)
                result["accepted"] = False
                if total_selling_price > 0:
                    counter_discount = round(max(0.0, (1.0 - counter_price / total_selling_price) * 100.0), 2)
                result["reason"] = "Counter discount clipped to protect base cost."

            # Persist per-item discounts across user cart if requested
            if req.apply_to_cart and req.user_id:
                try:
                    await self.db.apply_discount_to_all_items(req.user_id, counter_discount)
                except Exception as cart_err:
                    logger.warning("Could not auto-apply discount to cart for user %s: %s", req.user_id, cart_err)

            return NextDiscountResponse(
                accepted=result["accepted"],
                current_discount_percent=req.current_discount_percent,
                requested_discount_percent=req.requested_discount_percent,
                next_discount_percent=counter_discount,
                counter_offer_price=counter_price,
                total_original_price=total_selling_price,
                absolute_max_discount_percent=ceiling,
                customer_tier="loyal",
                reason=result["reason"],
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
            original_total = round(float(product.price) * qty, 2)
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
                original_price=round(float(product.price), 2),
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
