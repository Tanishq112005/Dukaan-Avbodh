import logging
from typing import Optional
from fastapi import HTTPException, status

from config.database import db_connection
from repositories.order import OrderRepository

logger = logging.getLogger(__name__)


class OrderController:
    def __init__(self, order_repo: Optional[OrderRepository] = None):
        self.order_repo = order_repo or OrderRepository(db_connection=db_connection)

    ## 1. Create Order for a user from their cart
    async def create_order(self, user_id: int):
        try:
            order = await self.order_repo.createOrder(user_id=user_id)
            return {
                "success": True,
                "message": "Order created successfully",
                "order": order
            }
        except ValueError as e:
            logger.warning("Validation error while creating order for user %s: %s", user_id, str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception:
            logger.exception("Failed to create order for user %s", user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create order"
            )

    ## 2. Get all orders for a specific user
    async def get_user_orders(self, user_id: int):
        try:
            orders = await self.order_repo.getUsersAllOrder(user_id=user_id)
            return {
                "success": True,
                "count": len(orders),
                "orders": orders
            }
        except HTTPException:
            raise
        except Exception:
            logger.exception("Failed to fetch orders for user %s", user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch orders"
            )



orderController = OrderController()
