import logging

from fastapi import HTTPException, status

from repositories.cart import cart
from repositories.userEvent import userEvent
from models.userEvent import EventType
from schemas.cart import (
    AddItemRequest,
    UpdateItemRequest,
    DeleteItemRequest,
    ApplyDiscountRequest
)

logger = logging.getLogger(__name__)


class CartController:

    # Add item to cart
    async def add_item(
        self,
        user_id: int,
        payload: AddItemRequest
    ):
        try:
            item = await cart.add_item(
                user_id=user_id,
                product_id=payload.product_id,
                quantity=payload.quantity,
                size=payload.size
            )

            try:
                await userEvent.addUserEvents(
                    user_id=user_id,
                    event_type=EventType.ADD_TO_CART,
                    product_id=payload.product_id
                )
            except Exception:
                logger.exception("Failed to record add-to-cart event")

            return {
                "success": True,
                "message": "Item added to cart successfully",
                "item": {
                    "id": item.id,
                    "cart_id": item.cart_id,
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "size": item.size
                }
            }

        except ValueError as e:
            message = str(e)
            code = (
                status.HTTP_404_NOT_FOUND
                if "not found" in message.lower()
                else status.HTTP_400_BAD_REQUEST
            )
            raise HTTPException(status_code=code, detail=message)

        except Exception:
            logger.exception("Failed to add item to cart")
            raise HTTPException(
                status_code=500,
                detail="Failed to add item to cart"
            )

    # Get cart items
    async def get_items(self, user_id: int):
        try:
            items = await cart.get_items(user_id=user_id)

            return {
                "success": True,
                "items": items,
                "count": len(items)
            }

        except Exception:
            logger.exception("Failed to get cart items")
            raise HTTPException(
                status_code=500,
                detail="Failed to get cart items"
            )

    # Update cart item quantity
    async def update_item(
        self,
        user_id: int,
        payload: UpdateItemRequest
    ):
        try:
            item = await cart.update_quantity(
                user_id=user_id,
                product_id=payload.product_id,
                quantity=payload.quantity,
                size=payload.size
            )

            if item is None and payload.quantity > 0:
                raise HTTPException(
                    status_code=404,
                    detail="Item not found in cart"
                )

            return {
                "success": True,
                "message": (
                    "Item updated successfully"
                    if item
                    else "Item removed from cart"
                ),
                "item": {
                    "id": item.id,
                    "cart_id": item.cart_id,
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "size": item.size
                } if item else None
            }

        except ValueError as e:
            message = str(e)
            code = (
                404 if "not found" in message.lower()
                else 400
            )
            raise HTTPException(status_code=code, detail=message)

        except HTTPException:
            raise

        except Exception:
            logger.exception("Failed to update cart item")
            raise HTTPException(
                status_code=500,
                detail="Failed to update cart item"
            )

    # Remove item from cart
    async def delete_item(
        self,
        user_id: int,
        payload: DeleteItemRequest
    ):
        try:
            removed = await cart.remove_item(
                user_id=user_id,
                product_id=payload.product_id,
                size=payload.size
            )

            if not removed:
                raise HTTPException(
                    status_code=404,
                    detail="Item not found in cart"
                )

            try:
                await userEvent.addUserEvents(
                    user_id=user_id,
                    event_type=EventType.REMOVE_FROM_CART,
                    product_id=payload.product_id
                )
            except Exception:
                logger.exception("Failed to record remove-from-cart event")

            return {
                "success": True,
                "message": "Item removed from cart successfully"
            }

        except HTTPException:
            raise

        except Exception:
            logger.exception("Failed to remove cart item")
            raise HTTPException(
                status_code=500,
                detail="Failed to remove cart item"
            )

    # Get cart summary
    async def get_summary(self, user_id: int):
        try:
            summary = await cart.get_summary(user_id=user_id)

            return {
                "success": True,
                **summary
            }

        except Exception:
            logger.exception("Failed to get cart summary")
            raise HTTPException(
                status_code=500,
                detail="Failed to get cart summary"
            )

    # Apply cart discount
    async def apply_discount(
        self,
        user_id: int,
        payload: ApplyDiscountRequest
    ):
        try:
            discount = payload.discount_percentage

            await cart.discountChange(
                user_id=user_id,
                discount_percentage=discount
            )

            summary = await cart.get_summary(user_id=user_id)

            return {
                "success": True,
                "message": "Discount applied successfully",
                "discount_percentage": discount,
                "summary": summary
            }

        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )

        except Exception:
            logger.exception("Failed to apply discount")
            raise HTTPException(
                status_code=500,
                detail="Failed to apply discount"
            )

    # Clear cart
    async def clear_cart(self, user_id: int):
        try:
            await cart.clear_cart(user_id=user_id)

            return {
                "success": True,
                "message": "Cart cleared successfully"
            }

        except Exception:
            logger.exception("Failed to clear cart")
            raise HTTPException(
                status_code=500,
                detail="Failed to clear cart"
            )


cartController = CartController()
