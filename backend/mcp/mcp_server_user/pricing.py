from mcp_server_user.server import mcp
from services.combo_pricing_engine import combo_pricing_engine
from services.negotiation_service import negotiation_service
from services.pricing_service import pricing_service
from services.audit_logger import audit_logger
from services.upsell_service import upsell_service
from repositories.cart_repository import cart_repository
from repositories.chat_audit_repository import chat_audit_repo


@mcp.tool()
async def calculate_combo_offer(user_id: int, discount_percent: float = 0.0, thread_id: str = "") -> dict:
    """
    Builds a Curated Kit (1-2 cart items + 1-2 recommendations). Campaign discounts are stacked
    sequentially into each item's New Selling Price; total_combo_price is the sum of those NSPs.
    Any extra discount_percent is applied on top of that NSP total.

    LLM Instructions:
    - DO pass user_id. Pass discount_percent=0.0 to show the kit price before haggling.
    - DO pitch the kit using total_combo_price. Mention campaign savings if campaign_savings > 0.
    - DO NOT invent a different kit price.
    - If success is false, tell the user a kit needs at least 2 items.
    """
    cart_items = await cart_repository.get_cart_items(user_id)
    offer = await upsell_service.generate_upsell_offer(user_id, cart_items)

    kit = offer.get("kit_products") if offer.get("success") else None
    if not kit:
        kit = await pricing_service.price_cart_items(cart_items) if cart_items else []

    if len(kit) < 2:
        return {"success": False, "error": "A curated kit needs at least 2 items (cart + recommendations)."}

    combo = combo_pricing_engine.calculate_combo_price(kit, discount_percent)

    await audit_logger.log_action(
        action="calculate_combo_offer",
        reason=f"discount_percent={discount_percent}, has_campaign={combo.get('has_campaign')}",
        result=f"total_combo_price={combo.get('total_combo_price')}, final={combo.get('final_price')}",
        user_id=user_id,
        thread_id=str(thread_id) if thread_id else None,
        metadata={"combo_offer": combo, "applied_campaigns": combo.get("applied_campaigns", [])},
    )

    if thread_id:
        await chat_audit_repo.update_state_patch(user_id, str(thread_id), {
            "combo_offer": combo,
            "new_selling_price_total": combo.get("total_combo_price", 0.0),
            "applied_campaigns": combo.get("applied_campaigns", []),
            "campaign_priced_products": combo.get("products", []),
        })

    return {"success": True, "combo_offer": combo}


@mcp.tool()
async def negotiate_discount(
    user_id: int,
    current_discount_percent: float,
    requested_discount_percent: float,
    thread_id: str = "",
) -> dict:
    """
    Evaluates a requested extra discount against combo New Selling Price minus cost.
    The model MUST call this tool for every discount ask and MUST use only the returned numbers.

    LLM Instructions:
    - NEVER invent or guess a discount percent or a rupee amount.
    - IF loss_leader is True or accepted is False with a rejection message, refuse extra discount.
    - IF accepted is True, confirm using counter_offer_percent AND counter_offer_price exactly.
    - IF accepted is False, counter with ONLY counter_offer_percent / counter_offer_price.
    - Pass the last counter_offer_percent as current_discount_percent on the next round.
    """
    result = await negotiation_service.evaluate_combo_negotiation(
        user_id=user_id,
        requested_discount=requested_discount_percent,
        current_discount=current_discount_percent,
    )

    priced_items = result.get("priced_items") or result.get("products") or []
    product_meta = [
        {
            "id": p.get("id"),
            "name": p.get("name"),
            "price": p.get("price"),
            "new_selling_price": p.get("new_selling_price"),
            "image_url": p.get("image_url") or p.get("image"),
            "applied_campaigns": p.get("applied_campaigns", []),
        }
        for p in priced_items
    ]

    await audit_logger.log_action(
        action="negotiate_discount",
        reason=(
            f"requested={requested_discount_percent}%, current={current_discount_percent}%, "
            f"accepted={result.get('accepted')}, loss_leader={result.get('loss_leader')}, "
            f"margin={result.get('margin')}, nsp={result.get('total_cart_price')}, "
            f"cost={result.get('total_cart_cost')}, max_allowed={result.get('absolute_max_discount_percent')}"
        ),
        result=(
            f"counter={result.get('counter_offer_percent')}% "
            f"price={result.get('counter_offer_price')} accepted={result.get('accepted')}"
        ),
        user_id=user_id,
        thread_id=str(thread_id),
        metadata={
            "products": product_meta,
            "applied_campaigns": [c for p in priced_items for c in (p.get("applied_campaigns") or [])],
            "margin": result.get("margin"),
            "loss_leader": result.get("loss_leader"),
        },
    )

    await chat_audit_repo.append_negotiation_log(user_id, str(thread_id), {
        "requested": requested_discount_percent,
        "agent_offered": result.get("counter_offer_percent", 0.0),
        "accepted": result.get("accepted", False),
        "counter_offer_price": result.get("counter_offer_price", 0.0),
        "margin": result.get("margin", 0.0),
        "loss_leader": result.get("loss_leader", False),
    })

    combo = combo_pricing_engine.calculate_combo_price(
        priced_items,
        result.get("counter_offer_percent", 0.0),
    )
    combo["final_price"] = result.get("counter_offer_price", combo.get("final_price"))

    await chat_audit_repo.update_state_patch(user_id, str(thread_id), {
        "cart_products": product_meta,
        "max_discount_we_can_give": result.get("absolute_max_discount_percent", 0.0),
        "total_cost_price": result.get("total_cart_cost", 0.0),
        "total_selling_price": result.get("total_cart_price", 0.0),
        "new_selling_price_total": result.get("total_cart_price", 0.0),
        "combo_margin": result.get("margin", 0.0),
        "applied_campaigns": combo.get("applied_campaigns", []),
        "campaign_priced_products": combo.get("products", []),
        "combo_offer": combo,
        "current_discount_percent": result.get("counter_offer_percent", 0.0),
    })

    if result.get("loss_leader"):
        return {
            "success": True,
            "accepted": False,
            "loss_leader": True,
            "counter_offer_percent": 0.0,
            "counter_offer_price": result.get("counter_offer_price", 0.0),
            "message": result.get("agent_internal_reasoning"),
            "combo_offer": combo,
        }

    if not priced_items:
        return {"success": False, "error": result["agent_internal_reasoning"]}

    return {
        "success": True,
        "accepted": result["accepted"],
        "loss_leader": False,
        "counter_offer_percent": result["counter_offer_percent"],
        "counter_offer_price": result["counter_offer_price"],
        "combo_offer": combo,
    }
