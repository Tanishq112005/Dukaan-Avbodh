# controllers/order_controller.py
from fastapi import HTTPException
from repositories import OrderRepository, ProductRepository, DiscountPolicyRepository
from services.audit_logger import audit_logger   # add kiya
from models import Order


class OrderController:
    def __init__(self):
        self.order_repo = OrderRepository()
        self.product_repo = ProductRepository()
        self.discount_repo = DiscountPolicyRepository()
        self.audit_logger = audit_logger              # add kiya

    async def get_my_orders(self, user_id: int):
        return await self.order_repo.get_by_user(user_id)

    async def get_all_orders(self):
        return await self.order_repo.get_all()

    async def update_status(self, order_id: int, status: str, merchant_id: int):
        updated = await self.order_repo.update_status(order_id, status)
        if not updated:
            raise HTTPException(status_code=404, detail="Order nahi mila")

        await self.audit_logger.log_action(          # audit_repo → audit_logger
            action="order_status_updated",
            reason=f"merchant {merchant_id} updated order {order_id}",
            result=f"new_status={status}"
        )
        return updated