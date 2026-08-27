# controllers/checkout_controller.py
from fastapi import HTTPException
from schemas.checkout_schemas import CheckoutRequest
from repositories import ProductRepository, OrderRepository, DiscountPolicyRepository
from repositories.audit_log_repository import AuditLogRepository
from models import Order


class CheckoutController:
    def __init__(self):
        self.product_repo = ProductRepository()
        self.order_repo = OrderRepository()
        self.discount_repo = DiscountPolicyRepository()
        self.audit_repo = AuditLogRepository()

    async def checkout(self, payload: CheckoutRequest, user_id: int):
        product = await self.product_repo.get_by_id(payload.product_id)
        if not product or product.stock <= 0:
            raise HTTPException(status_code=400, detail="Product available nahi hai")

        policy = await self.discount_repo.get_for_product(payload.product_id)
        max_discount = policy.max_discount_percent if policy else 0.0
        final_discount = min(payload.requested_discount, max_discount)   # bounded logic

        order = Order(
            product_id=product.id,
            user_id=user_id,
            discount_applied=final_discount,
            status="confirmed"
        )
        created = await self.order_repo.create(order)

        await self.audit_repo.log_action(
            action="checkout_completed",
            reason=f"user {user_id} checked out product {product.id}, requested {payload.requested_discount}%",
            result=f"applied={final_discount}%, capped={payload.requested_discount > max_discount}"
        )

        return {
            "order_id": created.id,
            "discount_applied": final_discount,
            "capped": payload.requested_discount > max_discount,
            "final_price": product.price * (1 - final_discount / 100)
        }