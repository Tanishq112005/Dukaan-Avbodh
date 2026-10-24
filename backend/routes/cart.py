from fastapi import APIRouter, Depends, Query, status
from typing import Optional

from middleware.auth_middleware import auth_middleware
from controllers.cart import cartController
from schemas.cart import (
    AddItemRequest,
    UpdateItemRequest,
    DeleteItemRequest,
    ApplyDiscountRequest
)

router = APIRouter(
    prefix="/cart",
    tags=["Cart"]
)


# 1. Add Item to Cart
@router.post("/add", status_code=status.HTTP_200_OK)
async def add_item_to_cart(
    payload: AddItemRequest,
    current_user: dict = Depends(auth_middleware)
):
    return await cartController.add_item(
        user_id=current_user["user_id"],
        payload=payload
    )


# 2. Get Cart Items
@router.get("", status_code=status.HTTP_200_OK)
@router.get("/items", status_code=status.HTTP_200_OK)
async def get_cart_items(
    current_user: dict = Depends(auth_middleware)
):
    return await cartController.get_items(
        user_id=current_user["user_id"]
    )


# 3. Update Cart Item
@router.put("/update", status_code=status.HTTP_200_OK)
@router.patch("/update", status_code=status.HTTP_200_OK)
async def update_cart_item(
    payload: UpdateItemRequest,
    current_user: dict = Depends(auth_middleware)
):
    return await cartController.update_item(
        user_id=current_user["user_id"],
        payload=payload
    )


# 4. Delete Cart Item
@router.delete("/delete", status_code=status.HTTP_200_OK)
@router.delete("/item", status_code=status.HTTP_200_OK)
async def delete_cart_item(
    payload: Optional[DeleteItemRequest] = None,
    product_id: Optional[int] = Query(default=None, description="Product ID if not passed in body"),
    size: Optional[str] = Query(default=None, description="Size if not passed in body"),
    current_user: dict = Depends(auth_middleware)
):
    p_id = payload.product_id if payload else product_id
    sz = payload.size if payload else size
    return await cartController.delete_item(
        user_id=current_user["user_id"],
        product_id=p_id,
        size=sz
    )


# 5. Get Cart Summary
@router.get("/summary", status_code=status.HTTP_200_OK)
async def get_cart_summary(
    current_user: dict = Depends(auth_middleware)
):
    return await cartController.get_summary(
        user_id=current_user["user_id"]
    )


# 6. Apply Discount
@router.post("/discount", status_code=status.HTTP_200_OK)
async def apply_cart_discount(
    payload: ApplyDiscountRequest,
    current_user: dict = Depends(auth_middleware)
):
    return await cartController.apply_discount(
        user_id=current_user["user_id"],
        payload=payload
    )


# 7. Clear Cart
@router.delete("/clear", status_code=status.HTTP_200_OK)
async def clear_cart(
    current_user: dict = Depends(auth_middleware)
):
    return await cartController.clear_cart(
        user_id=current_user["user_id"]
    )
