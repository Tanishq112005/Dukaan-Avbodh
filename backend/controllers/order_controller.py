# controllers/order_controller.py
from fastapi import HTTPException
from repositories import OrderRepository, ProductRepository, DiscountPolicyRepository

from models import Order


class OrderController:
    def __init__(self):
        self.order_repo = OrderRepository()
        self.product_repo = ProductRepository()
        self.discount_repo = DiscountPolicyRepository()
    

    async def get_my_orders(self, user_id: int):
        return await self.order_repo.get_by_user(user_id)

    async def get_all_orders(self):
        """Sirf merchant use karega — poora order list dekhne ke liye."""
        return await self.order_repo.get_all()

    async def update_status(self, order_id: int, status: str, merchant_id: int):
        updated = await self.order_repo.update_status(order_id, status)
        if not updated:
            raise HTTPException(status_code=404, detail="Order nahi mila")

        await self.audit_repo.log_action(
            action="order_status_updated",
            reason=f"merchant {merchant_id} updated order {order_id}",
            result=f"new_status={status}"
        )
        return updated