from datetime import datetime, timedelta

from repositories.cart_repository import cart_repository
from repositories.order_repository import OrderRepository
from services.combo_pricing_engine import combo_pricing_engine
from services.pricing_service import pricing_service
from services.upsell_service import upsell_service
from utils.pricing_math import calculate_next_offer, AGENT_MAX_DISCOUNT_PERCENT

order_repo = OrderRepository()


class NegotiationService:
    """Haggling is bounded by combo New Selling Price minus cost. The agent never invents percents."""

    async def _priced_combo_for_user(self, user_id: int) -> list[dict]:
        cart_items = await cart_repository.get_cart_items(user_id)
        if not cart_items:
            return []
        offer = await upsell_service.generate_upsell_offer(user_id, cart_items)
        kit = offer.get("kit_products") if offer.get("success") else None
        if kit and len(kit) >= 1:
            return kit
        return await pricing_service.price_cart_items(cart_items)

    async def evaluate_combo_negotiation(self, user_id: int, requested_discount: float, current_discount: float) -> dict:
        priced_items = await self._priced_combo_for_user(user_id)
        if not priced_items:
            return {
                "accepted": False,
                "counter_offer_percent": 0.0,
                "counter_offer_price": 0.0,
                "agent_internal_reasoning": "Cart is empty.",
                "products": [],
                "priced_items": [],
                "loss_leader": False,
                "margin": 0.0,
            }

        limits = combo_pricing_engine.get_negotiation_limits(priced_items)
        if limits["total_price"] == 0:
            return {
                "accepted": False,
                "counter_offer_percent": 0.0,
                "counter_offer_price": 0.0,
                "agent_internal_reasoning": "Total price is 0.",
                "products": priced_items,
                "priced_items": priced_items,
                "loss_leader": True,
                "margin": limits["margin"],
            }

        if limits["loss_leader"] or limits["margin"] <= 0:
            return {
                "accepted": False,
                "counter_offer_percent": 0.0,
                "counter_offer_price": limits["total_price"],
                "agent_internal_reasoning": (
                    "LOSS_LEADER_REJECT: Combo new selling price is at or below cost. "
                    "Do not offer any additional discount. Politely refuse and keep the current kit price."
                ),
                "products": priced_items,
                "priced_items": priced_items,
                "loss_leader": True,
                "margin": limits["margin"],
                "absolute_max_discount_percent": 0.0,
                "step_size": 0.0,
                "user_orders_recent": False,
                "total_cart_price": limits["total_price"],
                "total_cart_cost": limits["total_cost"],
                "total_cart_min_profit": limits["total_min_profit"],
                "max_discount_amount": 0.0,
            }

        absolute_max = limits["absolute_max_discount_percent"]
        if absolute_max <= 0:
            playable = max(0.0, limits["margin"] * 0.15)
            absolute_max = (playable / limits["total_price"]) * 100 if limits["total_price"] else 0.0

        user_orders = await order_repo.get_by_user(user_id)
        has_recent_order = False
        if not user_orders:
            # New User: Very stingy, only gives away 25% of the remaining margin per haggle round
            absolute_max = absolute_max * 0.70
            concession_factor = 0.25
        else:
            now = datetime.utcnow()
            has_recent_order = any(
                order.created_at and (now - order.created_at.replace(tzinfo=None)) < timedelta(days=30)
                for order in user_orders
            )
            # Loyal User (recent order): Gives away 40% of the remaining margin
            # Old User (no recent order): Gives away 30%
            concession_factor = 0.40 if has_recent_order else 0.30

        absolute_max = round(min(absolute_max, AGENT_MAX_DISCOUNT_PERCENT), 2)
        res = calculate_next_offer(requested_discount, current_discount, absolute_max, concession_factor)

        counter_price = round(limits["total_price"] * (1 - res["counter"] / 100), 2)
        if counter_price <= limits["total_cost"]:
            counter_price = round(limits["total_cost"] + 0.01, 2)
            res["accepted"] = False
            if limits["total_price"] > 0:
                res["counter"] = round(max(0.0, (1 - counter_price / limits["total_price"]) * 100), 2)
            res["reason"] = "Counter clipped to stay strictly above cost."

        return {
            "accepted": res["accepted"],
            "counter_offer_percent": res["counter"],
            "counter_offer_price": counter_price,
            "agent_internal_reasoning": res["reason"],
            "products": priced_items,
            "priced_items": priced_items,
            "loss_leader": False,
            "margin": limits["margin"],
            "absolute_max_discount_percent": absolute_max,
            "step_size": concession_factor,
            "user_orders_recent": has_recent_order,
            "total_cart_price": limits["total_price"],
            "total_cart_cost": limits["total_cost"],
            "total_cart_min_profit": limits["total_min_profit"],
            "max_discount_amount": limits["max_discount_amount"],
        }


negotiation_service = NegotiationService()
