import logging
from typing import Optional, List, Any
from fastapi import HTTPException, status

from Negotiation.database import NegotiationDatabase, negotiationDatabase
from Negotiation.utils import (
    calculate_discount_limits,
    calculate_next_offer,
    AGENT_MAX_DISCOUNT_PERCENT,
)
from Negotiation.schemas import (
    MaxDiscountRequest,
    MaxDiscountResponse,
    NextDiscountRequest,
    NextDiscountResponse,
    NegotiationItemDTO,
)

logger = logging.getLogger(__name__)


class NegotiationController:
    """
    Controller handling discount ceilings and interactive negotiation offers.
    Currently treats every customer as loyal (concession_factor = 0.40).
    Loyalty tier differentiation will be added in v3.
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
        Calculate the next counter-offer discount percentage for the user.
        Treats every customer as loyal (concession_factor = 0.40).
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

            # Customer is treated as loyal: no penalty on absolute ceiling, concession_factor = 0.40
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

            # Optional DB cart update if user_id is provided and apply_to_cart is True
            if req.apply_to_cart and req.user_id:
                try:
                    await self.db.apply_discount(req.user_id, counter_discount)
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


negotiationController = NegotiationController()
