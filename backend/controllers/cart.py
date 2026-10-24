import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status
from sqlmodel import select

from config.database import db_connection
from models.cart import Cart as CartModel, CartItem
from repositories.cart import Cart
from repositories.user import userRepository
from schemas.cart import (
    AddItemRequest,
    UpdateItemRequest,
    DeleteItemRequest,
    ApplyDiscountRequest
)

try:
    from repositories.userEvent import userEvent
    from models.userEvent import EventType
except Exception:
    userEvent = None
    EventType = None

logger = logging.getLogger(__name__)



class CartController:

    def __init__(self, db=db_connection, user_repo=userRepository):
        self.db = db
        self.user_repo = user_repo

    def _get_cart_repo(self, user_id: int) -> Cart:
        """Helper to create a Cart repository instance for a specific user."""
        return Cart(user_id=user_id, db_connection=self.db)

    async def _get_existing_cart(self, user_id: int) -> Optional[CartModel]:
        """Check if a cart already exists in the database for the given user."""
        async with self.db.get_session() as session:
            result = await session.exec(
                select(CartModel).where(CartModel.user_id == user_id)
            )
            return result.first()

    
    async def add_item(
        self,
        user_id: int,
        payload: Optional[AddItemRequest] = None,
        product_id: Optional[int] = None,
        quantity: int = 1,
        size: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add an item to the user's cart.
        If this is the user's first time / first item, ensures user exists via userRepository
        to satisfy database constraints before adding the item.
        """
        p_id = payload.product_id if payload else product_id
        qty = payload.quantity if payload else quantity
        sz = payload.size if payload else size

        if p_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="product_id is required"
            )

        if qty <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be greater than zero"
            )

        # Step 1: Ensure user exists in userRepository (e.g. guest or new user)
        user = await self.user_repo.ensure_guest_exists(user_id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to verify or create user account for cart"
            )

        # Step 2: Initialize Cart repository and add item
        cart_repo = self._get_cart_repo(user_id)

        # Sync existing discount percentage if cart already existed
        existing_cart = await self._get_existing_cart(user_id)
        if existing_cart:
            cart_repo.discount_percentage = existing_cart.discount_percentage

        try:
            item = await cart_repo.add_item(
                product_id=p_id,
                quantity=qty,
                size=sz
            )

            # Record ADD_TO_CART event if userEvent repository is available (fail-safe)
            if userEvent and EventType:
                try:
                    await userEvent.addUserEvents(
                        user_id=user_id,
                        event_type=EventType.ADD_TO_CART,
                        product_id=p_id
                    )
                except Exception as ev_err:
                    logger.warning(f"Failed to record ADD_TO_CART event: {ev_err}")

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
            err_msg = str(e)
            if "not found" in err_msg.lower():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

        except HTTPException:
            raise

        except Exception as e:
            logger.error(f"Error adding item to cart for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add item to cart"
            )

    
    async def get_items(self, user_id: int) -> Dict[str, Any]:
        """
        Get all items in the user's cart.
        Returns an error if the cart is not created, or if there are no items in the cart.
        """
        cart = await self._get_existing_cart(user_id)
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart is not created or does not exist for this user"
            )

        cart_repo = self._get_cart_repo(user_id)
        items = await cart_repo.get_items()

        if not items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No items found in cart"
            )

        return {
            "success": True,
            "items": items,
            "count": len(items)
        }

    # ---------------------------------------------------------
    # 3. Update Item
    # ---------------------------------------------------------
    async def update_item(
        self,
        user_id: int,
        payload: Optional[UpdateItemRequest] = None,
        product_id: Optional[int] = None,
        quantity: Optional[int] = None,
        size: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update the quantity of an item in the cart.
        If quantity <= 0, the item is removed.
        Returns error if cart is not created or item is not found.
        """
        p_id = payload.product_id if payload else product_id
        qty = payload.quantity if payload else quantity
        sz = payload.size if payload else size

        if p_id is None or qty is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="product_id and quantity are required"
            )

        cart = await self._get_existing_cart(user_id)
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart is not created or does not exist for this user"
            )

        cart_repo = self._get_cart_repo(user_id)
        cart_repo.discount_percentage = cart.discount_percentage

        try:
            item = await cart_repo.update_quantity(
                product_id=p_id,
                quantity=qty,
                size=sz
            )

            if item is None and qty > 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Item with product_id {p_id} not found in cart"
                )

            return {
                "success": True,
                "message": "Cart item updated successfully" if item else "Item removed from cart because quantity was <= 0",
                "item": {
                    "id": item.id,
                    "cart_id": item.cart_id,
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "size": item.size
                } if item else None
            }

        except ValueError as e:
            err_msg = str(e)
            if "not found" in err_msg.lower():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

        except HTTPException:
            raise

        except Exception as e:
            logger.error(f"Error updating item in cart for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update cart item"
            )

    # ---------------------------------------------------------
    # 4. Delete Item
    # ---------------------------------------------------------
    async def delete_item(
        self,
        user_id: int,
        payload: Optional[DeleteItemRequest] = None,
        product_id: Optional[int] = None,
        size: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Remove a specific item from the cart.
        Returns error if cart is not created or item is not found.
        """
        p_id = payload.product_id if payload else product_id
        sz = payload.size if payload else size

        if p_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="product_id is required"
            )

        cart = await self._get_existing_cart(user_id)
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart is not created or does not exist for this user"
            )

        cart_repo = self._get_cart_repo(user_id)
        cart_repo.discount_percentage = cart.discount_percentage

        try:
            removed = await cart_repo.remove_item(
                product_id=p_id,
                size=sz
            )

            if not removed:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Item with product_id {p_id} not found in cart"
                )

            # Record REMOVE_FROM_CART event if userEvent repository is available (fail-safe)
            if userEvent and EventType:
                try:
                    await userEvent.addUserEvents(
                        user_id=user_id,
                        event_type=EventType.REMOVE_FROM_CART,
                        product_id=p_id
                    )
                except Exception as ev_err:
                    logger.warning(f"Failed to record REMOVE_FROM_CART event: {ev_err}")

            return {
                "success": True,
                "message": f"Product {p_id} removed from cart successfully"
            }

        except HTTPException:
            raise

        except Exception as e:
            logger.error(f"Error deleting item from cart for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete cart item"
            )

    # ---------------------------------------------------------
    # 5. Get Summary
    # ---------------------------------------------------------
    async def get_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Get complete cart summary including items, subtotal, discount, and total.
        Returns error if cart is not created.
        """
        cart = await self._get_existing_cart(user_id)
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart is not created or does not exist for this user"
            )

        cart_repo = self._get_cart_repo(user_id)
        cart_repo.discount_percentage = cart.discount_percentage

        try:
            summary = await cart_repo.get_summary()
            return {
                "success": True,
                **summary
            }
        except Exception as e:
            logger.error(f"Error fetching cart summary for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get cart summary"
            )

    # ---------------------------------------------------------
    # 6. Apply Discount
    # ---------------------------------------------------------
    async def apply_discount(
        self,
        user_id: int,
        payload: Optional[ApplyDiscountRequest] = None,
        discount_percentage: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Apply a discount percentage (0 to 100) to the cart and persist it in the database.
        Returns updated summary.
        """
        disc = payload.discount_percentage if payload else discount_percentage
        if disc is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="discount_percentage is required"
            )

        if not (0 <= disc <= 100):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Discount percentage must be between 0 and 100"
            )

        cart = await self._get_existing_cart(user_id)
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart is not created or does not exist for this user"
            )

        cart_repo = self._get_cart_repo(user_id)
        cart_repo.discountChange(disc)

        # Persist discount percentage to the Cart database model
        async with self.db.get_session() as session:
            try:
                db_cart = (
                    await session.exec(
                        select(CartModel).where(CartModel.user_id == user_id)
                    )
                ).first()
                if db_cart:
                    db_cart.discount_percentage = disc
                    db_cart.updated_at = datetime.utcnow()
                    session.add(db_cart)
                    await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Error persisting discount to database: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to persist discount"
                )

        summary = await cart_repo.get_summary()

        return {
            "success": True,
            "message": f"Discount of {disc}% applied successfully",
            "discount_percentage": disc,
            "summary": summary
        }

    # ---------------------------------------------------------
    # Clear Cart Helper
    # ---------------------------------------------------------
    async def clear_cart(self, user_id: int) -> Dict[str, Any]:
        """Remove every item from the user's cart."""
        cart = await self._get_existing_cart(user_id)
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart is not created or does not exist for this user"
            )

        cart_repo = self._get_cart_repo(user_id)
        await cart_repo.clear_cart()

        return {
            "success": True,
            "message": "Cart cleared successfully"
        }

    # CamelCase Aliases for flexible integration
    addItem = add_item
    getItems = get_items
    getCartItems = get_items
    updateItem = update_item
    deleteItem = delete_item
    removeItem = delete_item
    getSummary = get_summary
    applyDiscount = apply_discount
    clearCart = clear_cart


# Singleton instance for routes/controllers import
cartController = CartController()
